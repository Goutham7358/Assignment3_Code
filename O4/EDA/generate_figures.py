"""Generate Figures 1-3 and their numerical tables from the prepared CSVs."""

import eda_national
import eda_routes


def main():
    print("Figure 1: national concentration and share gap")
    eda_national.main()
    print("Figures 2 and 3: route coverage, HHI distribution and heatmap")
    eda_routes.main()
    print("Figures saved in O4/output/figures; numerical tables in O4/output/tables.")


if __name__ == "__main__":
    main()
