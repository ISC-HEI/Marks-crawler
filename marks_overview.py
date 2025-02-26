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


def load_all_data(directory):
    """Loads all data from Excel files in a directory into a dictionary of DataFrames.

    Args:
        directory (str): The path to the directory containing the Excel files.

    Returns:
        dict: A dictionary where keys are filenames and values are pandas DataFrames.
                Only includes .xlsx files and excludes temporary files (starting with '~').
    """
    all_data = {}
    for filename in os.listdir(directory):
        if filename.endswith(".xlsx") and not filename.startswith("~"):
            file_path = os.path.join(directory, filename)
            df = load_and_mangle_data(file_path)
            all_data[filename] = df
    return all_data


all_data = load_all_data("res/marks")

# Create a dictionary of keys with the module code, module name, and academic year
regex = r"(\d{3})(.*?)(\d{4}-\d{4})"
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

# print(f'The keys are {all_keys}')


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

        # Filter display names based on the selected level(s)
        filtered_display_names = []
        for level in selected_levels:
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

        filtered_display_names.sort()

        # Remove duplicates while preserving order
        filtered_display_names = list(dict.fromkeys(filtered_display_names))

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


    # Find the key corresponding to the selected display name
    selected_file = next(
        key
        for key, value in all_keys.items()
        if f"{value[0]} {value[1]}" == selected_display_name
    )

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

    # Add the visual data frame in the middle of the screen
    table_height = (
        last_df.shape[0] + 1
    ) * 35 + 3  # Make that we display every student in the module

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
    
    # Insert the "Etudiant" column at the beginning of the DataFrame
    copy_df.insert(0, "Etudiant", etudiant_col)
    copy_df = copy_df.drop(columns=["Nom", "Prenom"])
   
    styled_df = copy_df.style.apply(highlight_if_echec, axis=1).format(add_checkmarks)    
    st.dataframe(styled_df, height=table_height, use_container_width=True)
    

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
    
        # Create a dictionary to store aggregated student data
        aggregated_data = {}
    
        # Iterate through all DataFrames
        for filename, df in all_data.items():
            # Extract module code from filename
            module_code = all_keys[filename][0]
    
            # Filter by selected module levels
            if not any(module_code.startswith(code) for code in filtered_module_codes):
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
        aggregated_df.shape[0] + 1
    ) * 35 + 3  # Make that we display every student in the module

    styled_df = aggregated_df.style.applymap(highlight_below_4).format(precision=1)

    # Display the DataFrame
    st.dataframe(styled_df, height=table_height, column_config={k: st.column_config.Column(width="medium") for k in aggregated_df.columns}, use_container_width=True)

# Add a selectbox to the sidebar:
choice = st.sidebar.radio("View", ("Module view", "Student view", "Academic year view"))

if choice == "Module view":
    # Call the function to display the selected module
    display_selected_module(all_data, all_keys)
elif choice == "Student view":
    # Call the function to display the selected student
    display_selected_student(all_data)
elif choice == "Academic year view":
    display_academic_year_view(all_data, all_keys)
    # st.write("Student view is not implemented yet")
# AgGrid(last_df, height=table_height)

# Add a selectbox to the sidebar:
add_selectbox = st.sidebar.selectbox(
    "Academic year", default_years, index=len(default_years) - 1
)
