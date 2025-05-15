# Marks crawler from XLSX files 

![Static Badge](https://img.shields.io/badge/WIP-0.1-blue?style=flat&color=blue)

This script provides a [Streamlit](https://streamlit.io/) application for visualizing and analyzing student marks.

It allows users to view marks by module, student, or academic year. The application
loads data from Excel files, preprocesses it, and presents it in interactive tables
with features like highlighting failing grades and sorting.
The application consists of the following main functionalities:
- **Data Loading and Preprocessing:**
    - Loads data from Excel files in a specified directory.
    - Removes unnecessary rows and columns.
    - Mangles column names for better readability.
    - Extracts module code, module name, and academic year from filenames.
- **Module View:**
    - Displays a selectbox with module names.
    - Shows the corresponding DataFrame for the selected module.
    - Highlights failing grades in pink.
    - Allows navigation between modules using "Previous" and "Next" buttons.
- **Student View:**
    - Displays a selectbox with student names.
    - Shows the aggregated information for the selected student across all modules.
    - Presents a summary table with module results and final grades.
    - Displays detailed course data for each module.
- **Academic Year View:**
    - Displays a view of student marks aggregated by academic year and module level.
    - Allows filtering by module level (1st year, 2nd year, 3rd year).
    - Highlights failing grades in pink.
The application uses Streamlit for the user interface and pandas for data manipulation.
It also utilizes regular expressions for extracting information from filenames.

## Preview

![Streamlit Marks Crawler](preview.png)


## Usage

Add the modules marks Excel files in `res/marks` folder. There's even a script to gather all of them (`gather_copy.sh`). Enjoy!

## How to install and run

### Installing with UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install
uv add streamlit
```

### Running with UV
Then run with `uv run streamlit run marks_overview.py`

### Creating a streamlit app from scratch (NOT required here)
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
uv python install
uv init hello-world
uv run hello.py
uv add streamlit
uv run streamlit
```

