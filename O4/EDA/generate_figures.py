"""Generate all O4 EDA figures and tables from the prepared CSVs."""

import eda_national
import eda_routes
import eda_capacity


def main():
    print("Figure 1: national concentration and share gap")
    eda_national.main()
    print("Figures 2 and 3: route coverage, HHI distribution and heatmap")
    eda_routes.main()
    print("Section 4.3: December capacity-input table")
    eda_capacity.main()
    print("Figures saved in O4/output/figures; numerical tables in O4/output/tables.")


if __name__ == "__main__":
    main()
