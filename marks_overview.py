# MIT License
# 
# Copyright (c) 2024 Pierre-André Mudry
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.



import os
import streamlit as st
import pandas as pd
import re
import math

from streamlit_slickgrid import (
    add_tree_info,
    slickgrid,
    Formatters,
    Filters,
    FieldType,
    OperatorType,
    ExportServices,
    StreamlitSlickGridFormatters,
    StreamlitSlickGridSorters,
)

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

#This line is very important, it allows to save the selected values of widget with a key in session state
st.session_state.update(st.session_state)

st.set_page_config(layout="wide", page_title="ISCMarks", page_icon="res/logo-512.png")

st.title("Marks crawler 🔎")
st.markdown("---")

st.markdown(
    r"""
    <style>
    .stAppDeployButton {
            visibility: hidden;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


# Prepare the UI
ISC_LOGO = "res/logo-512.png"
ISC_LARGE = "res/logo-inline-black.webp"

st.logo(ISC_LARGE, icon_image=ISC_LOGO, size="large")

default_years = ["2022-2023", "2023-2024", "2024-2025"]

@st.cache_resource
def load_module_list():
    """
    Loads the module list for each sector from a csv file and return it.
    
    Returns:
        dict: A dictionary containing the module list for each sector for each year.
    """
    module_dict = {}
    module_list_dir = "res/study_plans/"
    for sector in ["ETE", "SYND", "TEVI"]:
        file_path = os.path.join(module_list_dir, sector+"StudyPlan.csv")
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Module list file not found: {file_path}") 

        # Load csv into a pandas DataFrame
        df = pd.read_csv(file_path, delimiter=";")
        # Get all rows where the value in column "Semester" contains "S1" or "S2"
        df_year1 = df[df["Semestre"].str.contains("S1|S2", na=False)]
        df_year2 = df[df["Semestre"].str.contains("S3|S4", na=False)]
        df_year3 = df[df["Semestre"].str.contains("S5|S6", na=False)]
        module_dict[sector] = {
            "1st year": [str(x) for x in df_year1["ID module"]],
            "2nd year": [str(x) for x in df_year2["ID module"]],
            "3rd year": [str(x) for x in df_year3["ID module"]],
        }
    return module_dict

#module_list = load_module_list()
st.session_state.setdefault("modules_list", load_module_list())
#print("Loaded module list:", st.session_state["modules_list"])

@st.cache_resource
def load_and_mangle_data(file_path):
    """
    Loads data from an Excel file, removes unnecessary rows and columns,
    and mangles the column names for better readability.

    Args:
        file_path (str): The path to the Excel file.

    Returns:
        pandas.DataFrame: The processed DataFrame.
    """
    print("Loading data from", file_path)

    # Read and remove everything before the header row
    xl_page = pd.read_excel(file_path, sheet_name=None, header=4)

    for sn, df in xl_page.items():
        new_cols = []
        xl_page[sn] = df

    # Get the last sheet, where only the summary is
    last_sheet_name = list(xl_page.keys())[-1]
    last_df = xl_page[last_sheet_name]

    # Remove the last two columns
    last_df = last_df.iloc[:, :]
    return last_df


# mod_200 = load_and_mangle_data("res/200 Sciences IT 2 2024-2025.xlsx")
# print(mod_200)


def load_all_data(iofiles):
    """Loads all data from a list of iofiles into a dictionary of DataFrames.

    Args:
        iofiles (list): List of file-like objects (e.g., from Streamlit's file uploader).

    Returns:
        dict: A dictionary where keys are filenames and values are pandas DataFrames.
                Only includes .xlsx files and excludes temporary files (starting with '~').
    """
    all_data = {}
    for file in iofiles:
        filename = file.name
        if filename.endswith(".xlsx") and not filename.startswith("~"):
            df = load_and_mangle_data(file)
            all_data[filename] = df
    return all_data

#all_data = load_all_data("res/marks")
#print("all_data:", all_data)

def get_keys(all_data):
    # Create a dictionary of keys with the module code, module name, and academic year
    regex = r"([^ ]+)\s+(.*?)(\d{4}-\d{4})"
    all_keys = {}

    for key in all_data.keys():
        matches = re.findall(regex, key)
        if matches:
            match = matches[0]
            module_code = match[0]
            module_name = match[1]
            academic_year = match[2]
            all_keys[key] = (module_code, module_name, academic_year)
        else:
            print(f"No match found for key: {key}")
    return all_keys

#all_keys = get_keys(all_data)

# print(f'The keys are {all_keys}')
# Initialize session state for all_data if not already set
st.session_state.setdefault("all_data", {})
st.session_state.setdefault("all_keys", {})
# if "all_data" not in st.session_state:
#     st.session_state["all_data"] = all_data
# if "all_keys" not in st.session_state:
#     st.session_state["all_keys"] = all_keys
#     print("added all keys to session state", st.session_state["all_keys"])

def replace_nan_in_display(element):
    """This is used to display None instead of nan value in multiselect widget
    """
    if isinstance(element, float) and math.isnan(element):
        return "None"
    return element

def filter_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Adds a UI on top of a dataframe to let viewers filter columns

    Args:
        df (pd.DataFrame): Original dataframe

    Returns:
        pd.DataFrame: Filtered dataframe
    """
    modify = st.checkbox("Add filters")

    if not modify:
        return df

    df = df.copy()

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            # Get unique values in the column
            unique_values = df[column].unique()
            # Use multiselect for categorical columns
            #if isinstance(df[column], pd.CategoricalDtype) or df[column].nunique() < 10:
            if column in ["Remarques", "Module", "Temps partiel"] or (len(unique_values) == 1 and pd.isna(unique_values[0])): # Hard coded to avoid filtering issues

                # Set default list
                default_list = list(unique_values)
                # This is a hack because Streamlit multiselect does not handle NaN values well if the column has only NaN values
                if len(unique_values) == 1 and pd.isna(unique_values[0]):
                    default_list = []

                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    options=unique_values,
                    format_func=replace_nan_in_display,
                    default=default_list,
                )
                df = df[df[column].isin(user_cat_input)]
            # Use slider range for numeric columns
            elif is_numeric_dtype(df[column]):

                _min = float(df[column].min())
                _max = float(df[column].max())
                step = 0.1#(_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
            
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]

    return df


def display_upload_data_view():
    st.title("Upload Excel Files")

    # Selector for the sector
    sector_options = ["ETE", "ISC", "SYND", "TEVI"]
    st.session_state["sector"] = st.radio(
        "Choose your sector:",
        sector_options,
        horizontal=True,
        key="sector_radio", # This is what saves the state of the radio button
        #index=sector_options.index(st.session_state.sector)  # Set to the correct index or None
    )

    st.markdown("Upload your `.xlsx` files to use them as the data source for the app.")

    # File uploader
    uploaded_files = st.file_uploader(
        "Upload Excel files", type=["xlsx"], accept_multiple_files=True
    )

    if uploaded_files:
        #print("Uploaded files:", uploaded_files)
        st.success(f"{len(uploaded_files)} file(s) uploaded successfully!")
        # Process the uploaded files and store the data in session state
        st.session_state["all_data"] = load_all_data(uploaded_files)
        st.session_state["all_keys"] = get_keys(st.session_state["all_data"])
        st.info("Uploaded files will now be used as the data source.")

def filter_module_by_level(selected_levels, display_names, sector):
    """
    Filters the display names based on the selected levels and sector.

    Args:
        selected_levels (list): List of selected levels (e.g., "1st year", "2nd year", "3rd year").
        display_names (list): List of display names to filter.
        sector (str): The sector to filter by.

    Returns:
        list: Filtered list of display names.
    """
    filtered_display_names = []
    for level in selected_levels:
        match sector :
            # Filter display names based on the selected level(s)
            
            case "ISC":
                # For ISC, we filter by the first character of the module code
                if level == "1st year":
                    filtered_display_names.extend(
                        [name for name in display_names if name.startswith("1")]
                    )
                elif level == "2nd year":
                    filtered_display_names.extend(
                        [name for name in display_names if name.startswith("2")]
                    )
                elif level == "3rd year":
                    filtered_display_names.extend(
                        [name for name in display_names if name.startswith("3")]
                    )
            case _:
                # For ETE, SYND and TEVI we check the module list
                filtered_display_names.extend(
                    [name for name in display_names if name.split(" ")[0] in st.session_state["modules_list"][sector][level]]
                )
            
                
    filtered_display_names.sort()

    # Remove duplicates while preserving order
    filtered_display_names = list(dict.fromkeys(filtered_display_names))
    #print("Filtered display names:", filtered_display_names)
    return filtered_display_names

def display_selected_module(all_data, all_keys):
    # Calculate the average of each column
    """
    Displays a selectbox with module names and shows the corresponding DataFrame.

    Args:
        all_data (dict): Dictionary of DataFrames, where keys are filenames.
        all_keys (dict): Dictionary mapping filenames to module information.
    """
    # Create a list of display names combining module code and module name
    display_names = [f"{v[0]} {v[1]}" for k, v in all_keys.items()]
    display_names.sort()

    # Initialize the session state
    if 'module_selected_idx' not in st.session_state:
        st.session_state['module_selected_idx'] = 0

    # Create options for the pill selector
    pill_options = ["1st year", "2nd year", "3rd year"]

    # Display the pill selector
    col1, col2 = st.columns(2)

    with col1:
        selected_levels = st.pills(
            "Module in year:",
            pill_options,
            selection_mode="multi",
            default=(pill_options),
            on_change=lambda: st.session_state.update(module_selected_idx=0))
        
        fail_success = st.pills(
            "Show students who:",
            ["Pass", "Fail"],
            selection_mode="multi",
            default=(["Pass", "Fail"]),
        )
        
        # Filter display names based on the selected level(s)
        filtered_display_names = filter_module_by_level(selected_levels, display_names, st.session_state['sector'])
        
    # Display the selectbox with the filtered names
    with col2:
        selected_display_name = st.selectbox("Select a module:", filtered_display_names, index=st.session_state['module_selected_idx'])
        
        if selected_display_name == None:
            return

        # Callback function for A and B
        def onClick(direction):
            if direction == 'U':
                current_index = st.session_state['module_selected_idx']+1
                if current_index >= len(filtered_display_names):
                    current_index = 0
            
            if direction == 'D':
                current_index = st.session_state['module_selected_idx']-1
                if current_index < 0:
                    current_index = len(filtered_display_names) - 1
            
            st.session_state['module_selected_idx'] = current_index
        
        left, right = st.columns(2)
        # Add a button to select the previous module
        if left.button("Previous", on_click=onClick, args='D'): 
            pass
        # Add a button to select the next module
        if right.button("Next", on_click=onClick, args='U'): 
            pass


    # Get the list of display names
    display_names = [f"{v[0]} {v[1]}" for k, v in all_keys.items()]
    display_names.sort()
            
    # Find the key corresponding to the selected display name
    selected_file = next(
        key
        for key, value in all_keys.items()
        if f"{value[0]} {value[1]}" == selected_display_name
    )

    # Display the DataFrame based on the selected file
    last_df = all_data[selected_file]

    # Highlight those who fail
    def highlight_if_echec(row):
        styles = []
        for col, value in row.items():
            if "Echec" in str(value):
                # Apply red background to the entire row if 'Echec' is found
                styles = ["background-color: pink"] * len(row)
                return styles  # Apply to the whole row and exit
            elif isinstance(value, (int, float)) and value <= 3.9:
                styles.append(
                    "background-color: LemonChiffon; text-align: center"
                )  # Apply to individual cell
            elif isinstance(value, (int, float)):
                styles.append("text-align: center")
            else:
                styles.append("")

        return styles
    
    def add_checkmarks(val):
        if isinstance(val, (int, float)):
            return f"{val:.2f}"
        match str(val):
            case "Réussi":
                return "✅"
            case "Echec":
                return "❌"        
                    
        return val
   
    copy_df = last_df.copy()
    # Merge "Nom" and "Prenom" columns into a single "Etudiant" column
    copy_df["Etudiant"] = copy_df["Nom"] + " " + copy_df["Prenom"]
    
    # Get the "Etudiant" column
    etudiant_col = copy_df.pop("Etudiant")
    
    copy_df = copy_df.drop(columns=["Nom", "Prenom"])
   
    # Compute the average row, ignoring all non-numeric values
    def to_numeric_or_nan(val):
        try:
            return float(val)
        except (ValueError, TypeError):
            return float('nan')
    numeric_df = copy_df.map(to_numeric_or_nan)
    numeric_df = numeric_df.drop(columns=["Module", "Temps partiel", "Remarques"], errors='ignore')

    avg_row = numeric_df.mean(axis=0, numeric_only=True)
    avg_row = avg_row.round(2)
    avg_row.name = "Average"
    
    # Create a DataFrame for the average row only
    average_df = pd.DataFrame([avg_row])
    
    # Add blue highlight to the average row
    def highlight_average_row(row):
        if row.name == "Average":
            return ['background-color: #cce6ff'] * len(row)
        else:
            return [''] * len(row)

    # Insert the "Etudiant" column at the beginning of the DataFrame
    copy_df.insert(0, "Etudiant", etudiant_col)
    # Filter the DataFrame based on the selected fail/success options
    if "Pass" in fail_success and "Fail" in fail_success:
        pass  # Show all rows
    elif "Pass" in fail_success:
        copy_df = copy_df[copy_df["Module"] != "Echec"]
    elif "Fail" in fail_success:
        copy_df = copy_df[copy_df["Module"] == "Echec"]
    else:
        copy_df = copy_df.iloc[0:0]  # Show empty if neither selected

    # Compute the height of the table based on the number of rows
    def compute_height(df):
        return (df.shape[0] + 1) * 35 + 3  # Make that we display every student in the module

    # Add the filters widgets on top of the dataframe
    filtered_df = filter_dataframe(copy_df)

    # Style the DataFrame
    styled_df = filtered_df.style.apply(highlight_if_echec, axis=1).format(add_checkmarks)
    styled_avg_df = average_df.style.apply(highlight_average_row, axis=1).format(add_checkmarks)

    # Display the DataFrame with the applied styles
    st.dataframe(styled_df, height=compute_height(filtered_df), use_container_width=True)
    st.dataframe(styled_avg_df, height=40, use_container_width=True)


def display_selected_student(all_data):
    """
    Displays a selectbox with student names and shows the aggregated information.

    Args:
        all_data (dict): Dictionary of DataFrames, where keys are filenames.
    """
    # Extract all student names from all DataFrames
    all_student_names = []
    for df in all_data.values():
        # Assuming first two columns are 'First Name' and 'Last Name'
        for i in range(len(df)):
            all_student_names.append(f"{df.iloc[i, 0]} {df.iloc[i, 1]}")

    # Remove duplicate names
    unique_student_names = sorted(list(set(all_student_names)))

    # Display the selectbox with student names
    selected_student_name = st.selectbox("Select a student:", unique_student_names)

    # Create a dictionary to store the student's information
    student_data = {}

    # Iterate through all DataFrames to find the selected student
    for filename, df in all_data.items():
        for i in range(len(df)):
            if f"{df.iloc[i, 0]} {df.iloc[i, 1]}" == selected_student_name:
                # Extract the student's data from the current DataFrame
                module_data = df.iloc[i, 2:]  # Exclude first two columns (name)
                student_data[filename] = module_data.to_dict()

    # Prepare data for DataFrame
    student_data_list = []
    # st.write(student_data)

    # Prepare data for summary table
    st.subheader(f"Notes {selected_student_name}")
    summary_data = []
    for filename, module_data in student_data.items():
        filename_short = filename.split("2024-2025")[0]
        success = module_data["Module"]
        mark_final = module_data["Note du module"]
        mark_with_detail = round(module_data["Note avant arrondi"], 1)
        if isinstance(success, float):
            success_str = "Indéterminé ❓"
        else:
            match success:
                case "Réussi":
                    success_str = "✅"
                case "Echec":
                    success_str = "❌"
                case _:
                    success_str = "❓"

        summary_data.append({"Module": filename_short, "Résultat": success_str, "Note avant arrondi": mark_with_detail, "Note finale": mark_final})

    # Display summary table
    summary_df = pd.DataFrame(summary_data)
    if "Module" in summary_df.columns:
        summary_df.sort_values(by="Module", inplace=True)
    st.dataframe(summary_df)
    
    
    for filename, module_data in student_data.items():
        filename = filename.split("2024-2025")[0]

        # st.write(f"{filename} - Note du module {mark}, module {success}")
        st.write(f"{filename}")
        
        course_data = []
        for course_name, details in module_data.items():
            if course_name.startswith("Note") or course_name.startswith("Module") or course_name.startswith("Temps partiel") or course_name.startswith("Remarques"):
                continue
            course_data.append({"Unité d'enseignement": course_name, "Note": details})

        course_df = pd.DataFrame(course_data)
        st.dataframe(course_df, column_config={
            "Unité d'enseignement": st.column_config.Column(width="large"),
            "Note": st.column_config.Column(width="small"),
        })


def display_academic_year_view(all_data, all_keys):
    """
    Displays a view of student marks aggregated by academic year and module level.

    Args:
        all_data (dict): Dictionary of DataFrames, where keys are filenames.
        all_keys (dict): Dictionary mapping filenames to module information.
    """

    # Create options for the radio buttons
    level_options = ["1st year", "2nd year", "3rd year"]

    # Display the radio buttons horizontally
    selected_level = st.radio(
        "Select module level:",
        level_options,
        index=1,  # Default to "2nd year"
        horizontal=True
    )

    # Map selected level to module code prefix
    level_prefix_map = {
        "1st year": "1",
        "2nd year": "2",
        "3rd year": "3",
    }

    selected_levels = [selected_level]
    filtered_module_codes = [level_prefix_map[selected_level]]

    # Filter module codes based on selected levels
    filtered_module_codes = []
    for level in selected_levels:
        if level == "1st year":
            filtered_module_codes.append("1")
        elif level == "2nd year":
            filtered_module_codes.append("2")
        elif level == "3rd year":
            filtered_module_codes.append("3")
        #print("filtered_module_codes:", filtered_module_codes)
        # Create a dictionary to store aggregated student data
        aggregated_data = {}
    
        # Iterate through all DataFrames
        for filename, df in all_data.items():
            # Extract module code from filename
            module_code = all_keys[filename][0]
            #print("module_code:", module_code)
            # Skip modules that do not match the selected level
            match st.session_state["sector"]:
                case "ISC":
                    # Filter by selected module levels (use first character of module code)
                    if not any(module_code.startswith(code) for code in filtered_module_codes):
                        continue
                case _:
                    # For ETE, SYND and TEVI we check the module list
                    if module_code not in st.session_state["modules_list"][st.session_state["sector"]][selected_level]:
                        continue
    
            # Iterate through each row (student) in the DataFrame
            for i in range(len(df)):
                # Extract student name
                first_name = df.iloc[i, 0]
                last_name = df.iloc[i, 1]
                student_name = f"{first_name} {last_name}"
    
                # Extract "Note du module" and rename it with the filename
                note_du_module = df.get("Note du module", None)  # Use get to handle missing column
                if note_du_module is None:
                    note_du_module = df.iloc[i]["Note finale"]
                else:
                    note_du_module = df.iloc[i]["Note du module"]
    
                # If student is not in the aggregated data, initialize their entry
                if student_name not in aggregated_data:
                    aggregated_data[student_name] = {}
    
                # Add the module note to the student's data, using the filename as the key
                aggregated_data[student_name][filename] = note_du_module
    
        # Remove students with no marks
        aggregated_data = {k: v for k, v in aggregated_data.items() if v}
    
        # Convert the aggregated data to a DataFrame
        aggregated_df = pd.DataFrame.from_dict(aggregated_data, orient='index')

        # Rename columns to remove text after "202X"
        new_column_names = {}
        for col in aggregated_df.columns:
            new_col = re.split(r"202\d", col)[0]
            new_column_names[col] = new_col
        aggregated_df = aggregated_df.rename(columns=new_column_names)
    
    # Sort columns lexicographically
    aggregated_df = aggregated_df.reindex(sorted(aggregated_df.columns), axis=1)

    # Sort by the first column
    aggregated_df = aggregated_df.sort_index()

    # Highlight values below 4 in pink
    def highlight_below_4(val):
        """
        Highlights values below 4 in pink.
        """
        if isinstance(val, (int, float)) and val < 4:
            return 'background-color: pink'
        else:
            return ''

    # Compute the height of the table based on the number of students
    table_height = (
        aggregated_df.shape[0] + 1  # +2 to account for header and new average row
    ) * 35 + 3  # Make that we display every student in the module

    # Compute the average row and create new dataframe with it
    avg_row = aggregated_df.mean(axis=0, numeric_only=True)
    avg_row = avg_row.round(2)
    avg_row.name = "Average"
    average_df = pd.DataFrame([avg_row])

    avg_row = avg_row.to_dict()

    # Add blue highlight to the average row
    def highlight_average_row(row):
        if row.name == "Average":
            return ['background-color: #cce6ff'] * len(row)
        else:
            return [''] * len(row)

    # Apply the highlighting functions and format the DataFrame
    styled_df = aggregated_df.style.map(highlight_below_4).format(precision=1)
    avg_styled_df = average_df.style.map(highlight_below_4).apply(highlight_average_row, axis=1).format(precision=1)

    # Display the DataFrame
    st.dataframe(styled_df, height=table_height, column_config={k: st.column_config.Column(width="medium") for k in aggregated_df.columns}, use_container_width=True)
    st.dataframe(avg_styled_df, height=2, column_config={k: st.column_config.Column(width="medium") for k in aggregated_df.columns}, use_container_width=True)


# Add a selectbox to the sidebar:
choice = st.sidebar.radio("View", ("Upload data", "Module view", "Student view", "Academic year view"))

if choice == "Upload data":
    # Call the function to upload data
    display_upload_data_view()
if choice == "Module view":
    # Call the function to display the selected module
    display_selected_module(st.session_state["all_data"], st.session_state["all_keys"])
elif choice == "Student view":
    # Call the function to display the selected student
    display_selected_student(st.session_state["all_data"])
elif choice == "Academic year view":
    display_academic_year_view(st.session_state["all_data"], st.session_state["all_keys"])
    # st.write("Student view is not implemented yet")
# AgGrid(last_df, height=table_height)

# Add a selectbox to the sidebar:
# add_selectbox = st.sidebar.selectbox(
#     "Academic year", default_years, index=len(default_years) - 1
# )
