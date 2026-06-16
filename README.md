# ApexPlanet Data Analytics Internship - Task 1

## Overview

This repository contains my work for Task 1 of the ApexPlanet Data Analytics Internship, covering environment setup, data sourcing, data cleaning, and exploratory data analysis (EDA) on a retail sales dataset. The goal of this task was to set up a proper analytics workflow and practice extracting insights from a real-world-style dataset using Python.

## Dataset

For this project, I used the Sample Superstore dataset from Tableau's sample datasets. It contains 10,194 transactional records from a retail superstore, with 21 columns covering order details, customer information, product categories, sales, discounts, and profit. I picked this dataset because it has a good mix of numerical and categorical variables, which made it well suited for the kind of EDA this task asked for.

## Repository Structure

```
apexplanet-data-analytics/
├── data/
│   ├── raw/            # Original, unmodified dataset
│   └── processed/      # Cleaned dataset after preprocessing
├── notebooks/          # Jupyter notebook with the full analysis
├── scripts/            # Python scripts (if any)
├── reports/            # PDF/PPT reports
├── dashboards/         # Power BI / Tableau files
└── README.md
```

## Tools and Libraries

- Python 3.10
- pandas, numpy
- matplotlib, seaborn
- Jupyter Notebook

## What This Task Covers

**Environment setup**
Installed the required Python libraries and organised the project into a structured folder hierarchy for data, notebooks, reports, and dashboards.

**Data sourcing and understanding**
Loaded the dataset into a pandas DataFrame and reviewed its structure (shape, columns, data types) before doing anything else, along with documenting the data source, collection method, and limitations.

**Data cleaning**
Checked for missing values and duplicate rows (none found in either case), converted the relevant columns to category type, and used the IQR method to identify outliers in Sales and Profit. The outliers were kept rather than removed, since they reflect genuine business events such as bulk orders and heavy discounting rather than data entry errors. The full cleaning steps are documented in the notebook, along with a cleaning log.

**Exploratory data analysis**
Generated statistical summaries and value counts, ran univariate analysis (histograms, boxplots, bar charts), and bivariate analysis (a discount vs profit scatter plot and a correlation heatmap) to look for patterns and relationships in the data.

## Key Findings

- Discounting has a clear negative effect on profit. Orders with discounts above 0.5 are mostly loss-making, and Discount and Profit show a negative correlation of -0.22.
- Sales is driven by a relatively small number of large orders. Most transactions are under 1,000, but a long tail of bigger orders pulls the distribution out to over 20,000.
- Office Supplies and the Consumer segment account for the highest order volumes, but a high order count does not necessarily mean higher profitability per order.
- Outliers in Sales and Profit (around 11.6% and 18.8% of the data, respectively) appear to reflect real business activity rather than data quality issues, so they were retained for the analysis.


## Sample Visualizations

### Sales Distribution
![Sales Distribution](reports/images/sales_distribution.png)

### Discount vs Profit
![Discount vs Profit](reports/images/discount_vs_profit.png)

### Correlation Heatmap
![Correlation Heatmap](reports/images/correlation_heatmap.png)

## How to Run

1. Clone this repository
2. Install the required libraries: `pip install pandas numpy matplotlib seaborn`
3. Open `notebooks/EDA_Task1.ipynb` in Jupyter Notebook or VS Code
4. Run the cells in order

## Author

Khushi Vig
B.Tech, Electronics and Communication Engineering, GTBIT, GGSIPU