#!/bin/bash

# This script creates symbolic links to the xlsx files in the directories, it must be put into the 
# root directory of the directories containing the xlsx files (Secrétariat ISC)

# Set the target directory for the symbolic links
TARGET_DIR="collected_marks"

# Check if the target directory exists, if not create it
if [ ! -d "$TARGET_DIR" ]; then
    mkdir -p "$TARGET_DIR"
fi

# Find directories starting with 3 digits
find . -maxdepth 1 -type d -regex "./[0-9]\{3\}.*" | while read -r dir; do
    # Extract the first three digits from the directory name
    dir_prefix=$(basename "$dir" | cut -c 1-3)

    # Find xlsx files in the directory
    xlsx_files=$(find "$dir" -maxdepth 1 -type f -name "$dir_prefix*.xlsx")

    # If there is an xlsx file
    if [ -z "$xlsx_files" ]; then
        echo "No xlsx file found in $dir"
    elif [[ $(echo "$xlsx_files" | wc -l) -gt 1 ]]; then
        echo "More than one xlsx file found in $dir"
    else
        # Loop through the xlsx files (in case there are multiple, though unlikely)
        for xlsx_file in $xlsx_files; do
            # Extract the filename without the directory path
            filename=$(basename "$xlsx_file")

            # Copy to the target directory
            cp "$xlsx_file" "$TARGET_DIR/$filename"

            echo "Copied file: $xlsx_file"
        done
    fi
done