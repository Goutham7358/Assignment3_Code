"""Write the full-grid table bodies used in the main report."""


def write_grid_table(path, headings, rows, columns=None):
    if columns is None:
        columns = r"|>{\raggedright\arraybackslash}X|" + "r|" * (len(headings) - 1)
    headings = [heading.replace(r"\shortstack{", r"\shortstack{\strut ")
                .replace(r"\\", r"\\\strut ") for heading in headings]
    header = " & ".join(r"\textbf{" + heading + "}" for heading in headings)
    lines = [
        r"\begin{tabularx}{\linewidth}{" + columns + "}",
        r"\hline", header + r" \\", r"\hline",
    ]
    for row in rows:
        lines.extend([row + r" \\", r"\hline"])
    lines.append(r"\end{tabularx}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
