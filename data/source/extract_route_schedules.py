"""Extract selected-route schedule rows from the saved DGCA PDF archive.

The table parser is adapted from the project's monthly_route_hhi.py. It uses
PDF word positions because the reports contain multi-column airport tables.
"""

import bisect
import calendar
import hashlib
import json
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import unquote

from route_common import DATA, INTERIM, select_top20, write_csv

ROOT = DATA

NS = {"x": "http://www.w3.org/1999/xhtml"}


CITIES = {
    "DELHI": "DEL", "NEW DELHI": "DEL", "MUMBAI": "BOM",
    "MUMBAI (BOMBAY)": "BOM", "BOMBAY": "BOM", "BANGALORE": "BLR",
    "BENGALURU": "BLR", "KOLKATA": "CCU", "KOLKATA (CALCUTTA)": "CCU",
    "CALCUTTA": "CCU", "HYDERABAD": "HYD", "AHMEDABAD": "AMD",
    "PUNE": "PNQ", "POONA": "PNQ", "CHENNAI": "MAA",
    "CHENNAI(MADRAS)": "MAA", "CHENNAI (MADRAS)": "MAA", "MADRAS": "MAA",
    "SRINAGAR": "SXR", "GUWAHATI": "GAU", "GOA": "GOI", "DABOLIM": "GOI",
}


DATE_RE = re.compile(r"(?:\d{1,2}-[A-Za-z]{3}-\d{2,4}|\d{1,2}[/-]\d{1,2}[/-]\d{4})")


def parse_date(s):
    m = DATE_RE.search(s)
    s = m[0] if m else s
    for fmt in ("%d-%b-%y", "%d-%b-%Y", "%d/%m/%Y", "%d-%m-%Y", "%d/%b/%y"):
        try:
            return datetime.strptime(s.strip(), fmt).date()
        except ValueError:
            pass
    raise ValueError(f"Unrecognised date: {s!r}")


def last_sunday(year, month):
    d = date(year, month, calendar.monthrange(year, month)[1])
    return d - timedelta(days=(d.weekday() + 1) % 7)


def season_dates(year, season):
    if season == "summer":
        return last_sunday(year, 3), last_sunday(year, 10) - timedelta(days=1)
    return last_sunday(year, 10), last_sunday(year + 1, 3) - timedelta(days=1)


def airline_from_name(name):
    s = re.sub(r"[^A-Z0-9]", "", unquote(name).rsplit("/", 1)[-1].upper())
    for terms, airline in [
        (("AIRINDIAEXPRESS",), "Air India Express"),
        (("AIRASIA", "AIXCONNECT"), "AirAsia India / AIX Connect"),
        (("ALLIANCE",), "Alliance Air"), (("AIRINDIA",), "Air India"),
        (("INTERGLOBE", "INDIGO"), "IndiGo"), (("VISTARA", "TATASIA"), "Vistara"),
        (("SPICE",), "SpiceJet"), (("GOAIR", "GOFIRST"), "Go First / GoAir"),
        (("TRUJET", "TRUEJET"), "TruJet"),
        (("JETLITE",), "JetLite"), (("JETAIR", "JETSS", "JETW"), "Jet Airways"),
        (("AKASA", "SNV"), "Akasa Air"), (("AIRPEGASUS",), "Air Pegasus"),
        (("AIRCOSTA",), "Air Costa"), (("AIRCARNIVAL",), "Air Carnival"),
        (("STAR", "GHODAWAT"), "Star Air"),
        (("HERITAGE",), "Air Heritage"), (("ODISHA",), "Air Odisha"),
        (("INDIAONE", "GSECMONARCH"), "IndiaOne Air"),
        (("DECCAN",), "Air Deccan"), (("ZOOM",), "Zoom Air"),
        (("PAWAN",), "Pawan Hans"), (("JUSTUDO",), "FLY91"), (("FLYBIG",), "FlyBig"),
    ]:
        if any(t in s for t in terms):
            return airline
    return "UNKNOWN"


def get_lines(page):
    words = sorted(page.findall(".//x:word", NS), key=lambda w: (float(w.get("yMin")), float(w.get("xMin"))))
    lines = []
    for w in words:
        y = float(w.get("yMin"))
        if not lines or abs(y - lines[-1][0]) > 1.8:
            lines.append((y, []))
        lines[-1][1].append(w)
    return [(y, sorted(ws, key=lambda w: float(w.get("xMin")))) for y, ws in lines]


def center(w):
    return (float(w.get("xMin")) + float(w.get("xMax"))) / 2


def header_centers(page):
    words = page.findall(".//x:word", NS)
    freq = next((w for w in words if w.text == "Frequency"), None)
    if freq is None:
        return None
    fy = float(freq.get("yMin"))
    nearby = [w for w in words if abs(float(w.get("yMin")) - fy) < 23]
    def match(token):
        return sorted([w for w in nearby if (w.text or "").rstrip(".").lower() == token.lower()], key=center)
    left = []
    for token in ["Sl", "Flight", "Operator", "Aircraft"]:
        ws = match(token)
        if token == "Sl" and not ws:
            ws = [w for w in nearby if (w.text or "").lower().startswith("sl.")]
        if not ws:
            return None
        left.append(center(ws[0]))
    right = []
    for token in ["Arrival", "Departure", "Effective"]:
        ws = match(token)
        if token == "Departure":
            ws = sorted([w for w in nearby if (w.text or "").startswith("Departur")], key=center)
        if len(ws) != 2:
            return None
        right.extend(center(w) for w in ws)
    centers = left + [center(freq)] + right
    return centers


def pdf_extract(item):
    path = ROOT / item["path"]
    with tempfile.TemporaryDirectory(prefix="route-monthly-") as tmp:
        bbox = Path(tmp) / "words.html"
        subprocess.run(["pdftotext", "-bbox-layout", str(path), str(bbox)], check=True, capture_output=True)
        pages = ET.parse(bbox).getroot().findall(".//x:page", NS)
    first_text = " ".join(w.text or "" for w in pages[0].findall(".//x:word", NS))
    item["pages"] = len(pages)
    item["airline"] = airline_from_name(item["original_url"])
    season = "winter" if "WINTER" in first_text.upper() else "summer"
    # Some reports have a stale SUMMER caption in an October winter filing.
    # The seasonal filename and the dated rows identify the intended season.
    source_name = unquote(item["original_url"]).rsplit("/", 1)[-1]
    if re.search(r"(?:ws|_w)\d{2,4}", source_name, re.I):
        season = "winter"
    found_years = [int(x) for x in re.findall(r"\b(20\d{2})\b", first_text)]
    if found_years:
        year = found_years[0]
    else:
        name = item["filename"]
        m = re.search(r"(?:ss|ws|_w)(\d{2})(?:\D|$)", name, re.I)
        if not m:
            item.update(parse_status="no readable year", season="", source_rows=0)
            return [], [], item
        year = 2000 + int(m[1])
    lo, hi = season_dates(year, season)
    item.update(year=year, season=season, season_start=lo.isoformat(), season_end=hi.isoformat())
    movement = "MOVEMENT" in first_text.upper() and "REPORT" in first_text.upper()
    if not movement:
        item.update(parse_status="legacy table: requires separate extraction", source_rows=0)
        return [], [], item
    station = None
    records, errors = [], []
    last_centers = None
    for pageno, page in enumerate(pages, 1):
        width = float(page.get("width"))
        if width > 800:
            centers = [57 + 64.2 * (i + .5) for i in range(11)]
        else:
            centers = header_centers(page) or last_centers
        if centers is None:
            errors.append({"file": path.name, "page": pageno, "station": station, "problem": "unrecognised columns", "text": ""})
            continue
        last_centers = centers
        physical = sorted((x, i) for i, x in enumerate(centers))
        bounds = [(a[0] + b[0]) / 2 for a, b in zip(physical, physical[1:])]
        headfreq = next((float(w.get("yMin")) for w in page.findall(".//x:word", NS) if w.text == "Frequency"), 0)
        for y, words in get_lines(page):
            if y <= headfreq + 8:
                continue
            text = " ".join(w.text or "" for w in words)
            cells = [[] for _ in range(11)]
            for w in words:
                cells[physical[bisect.bisect_right(bounds, center(w))][1]].append(w.text or "")
            cells = [" ".join(c) for c in cells]
            if not re.fullmatch(r"\d+", cells[0]):
                if DATE_RE.search(text) or not re.fullmatch(r"[A-Za-z][A-Za-z /().-]*", text):
                    continue
                if re.search(r"\b(approved|schedule|operator|arrival|departure|frequency|director|report|effective)\b", text, re.I):
                    continue
                mid = (min(float(w.get("xMin")) for w in words) + max(float(w.get("xMax")) for w in words)) / 2
                if (text.upper() in CITIES or abs(mid - (centers[0] + centers[-1]) / 2) < 20
                        or abs(mid - width / 2) < 30):
                    station = text.strip()
                continue
            if not re.search(r"\d", cells[1]):
                continue
            try:
                if station is None:
                    raise ValueError("missing station")
                freq = cells[4].replace(" ", "")
                freq = "1234567" if freq.lower() == "daily" else freq
                if not re.fullmatch(r"[1-7]+", freq):
                    raise ValueError("invalid frequency")
                begin, end = parse_date(cells[9]), parse_date(cells[10])
                if begin > end:
                    raise ValueError("reversed validity")
                if bool(cells[5]) == bool(cells[7]):
                    raise ValueError("ambiguous movement direction")
                direction = "arrival" if cells[5] else "departure"
                endpoint = cells[5] if cells[5] else cells[7]
                tm = cells[6] if cells[5] else cells[8]
                if not re.fullmatch(r"[A-Z]{3}", endpoint):
                    raise ValueError("invalid endpoint")
                # Time is retained for audit but is not an input to frequency HHI.
                # A few originals print Excel time fractions or omit a time.
                if re.fullmatch(r"\d{1,2}:\d\d", tm):
                    tm = tm.zfill(5)
                flight = re.match(r"([A-Z0-9]{2})\s*(\d+[A-Z]?)", cells[1])
                if not flight:
                    raise ValueError("unrecognised flight number")
                records.append({"source_file": path.name, "source_page": pageno,
                                "source_row": cells[0], "station": station,
                                "station_iata": CITIES.get(station.upper(), ""),
                                "airline": item["airline"], "flight_number": "".join(flight.groups()),
                                "operator_code": cells[2], "operating_days": "".join(sorted(set(freq))),
                                "direction": direction, "other_airport": endpoint,
                                "scheduled_time": tm, "effective_from": begin.isoformat(),
                                "effective_to": end.isoformat(), "season_year": year,
                                "season": season, "source_url": item["source_url"]})
            except ValueError as exc:
                errors.append({"file": path.name, "page": pageno, "station": station,
                               "problem": str(exc), "text": text, "cells": " | ".join(cells)})
    item.update(parse_status="extracted" if not errors else "extracted with issues", source_rows=len(records), extraction_issues=len(errors))
    return records, errors, item


def main():
    if shutil.which("pdftotext") is None:
        raise SystemExit("Install Poppler first; this script needs pdftotext.")
    INTERIM.mkdir(parents=True, exist_ok=True)
    routes = {row["route"] for row in select_top20()}
    manifest = json.loads((DATA / "raw/route_schedule_manifest.json").read_text())
    selected_rows, selected_issues, all_issues, inventory = [], [], [], []
    total_rows = 0
    seen_hashes = set()

    for number, original in enumerate(manifest, 1):
        item = dict(original)
        payload = (DATA / item["path"]).read_bytes()
        digest = hashlib.sha256(payload).hexdigest()
        if not payload.startswith(b"%PDF") or digest != item["sha256"]:
            raise ValueError("Source PDF has changed: " + item["filename"])
        if digest in seen_hashes:
            raise ValueError("Duplicate publication in manifest: " + item["filename"])
        seen_hashes.add(digest)
        rows, issues, item = pdf_extract(item)
        total_rows += len(rows)
        for row in rows:
            pair = "-".join(sorted((row["station_iata"], row["other_airport"])))
            if row["station_iata"] and pair in routes:
                selected_rows.append(row)
        for issue in issues:
            issue["cells"] = issue.get("cells", "").rstrip()
            all_issues.append(issue)
            station = CITIES.get((issue.get("station") or "").upper(), "")
            endpoints = set(re.findall(r"\b[A-Z]{3}\b", issue["text"]))
            if item.get("year", 0) >= 2019 and station and any(
                "-".join(sorted((station, endpoint))) in routes for endpoint in endpoints
            ):
                selected_issues.append(issue)
        inventory.append(item)
        if number % 20 == 0 or number == len(manifest):
            print(f"Read {number}/{len(manifest)} PDFs; {len(selected_rows):,} selected-route rows.", flush=True)

    issue_fields = ["file", "page", "station", "problem", "text", "cells"]
    write_csv(INTERIM / "extraction_issues.csv", all_issues, issue_fields)
    (INTERIM / "source_manifest.json").write_text(json.dumps(inventory, indent=2) + "\n")
    if selected_issues:
        raise ValueError("Unresolved extraction issues on selected routes; inspect extraction_issues.csv.")

    selected_rows.sort(key=lambda row: (
        row["source_file"], int(row["source_page"]), int(row["source_row"]),
        row["station"], row["direction"], row["flight_number"],
    ))
    write_csv(INTERIM / "schedule_rows.csv", selected_rows)
    version = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True, check=True)
    audit = {
        "archive_pdfs": len(inventory), "archive_pages": sum(row["pages"] for row in inventory),
        "all_extracted_rows": total_rows, "selected_route_rows": len(selected_rows),
        "extraction_issues_all_routes": len(all_issues),
        "identified_extraction_issues_selected_routes_since_2019": len(selected_issues),
        "parse_status_counts": dict(Counter(row["parse_status"] for row in inventory)),
        "pdftotext_version": (version.stdout + version.stderr).splitlines()[0],
        "scope": "Only rows for the fixed top 20 airport pairs are saved in schedule_rows.csv.",
    }
    (INTERIM / "extraction_summary.json").write_text(json.dumps(audit, indent=2) + "\n")
    print(f"Saved {len(selected_rows):,} schedule rows with PDF, page and row references.")


if __name__ == "__main__":
    main()
