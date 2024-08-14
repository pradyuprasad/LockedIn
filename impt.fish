#!/usr/bin/env fish

set output_file "activity_tracker_summary.txt"

# Function to add a separator and file name
function add_separator
    echo "----------------------------------------" >> $output_file
    echo "File: $argv[1]" >> $output_file
    echo "----------------------------------------" >> $output_file
end

# Clear or create the output file
echo "" > $output_file

# Main application file
add_separator "main.py"
cat main.py >> $output_file

# Database setup
add_separator "db_setup.py"
cat db_setup.py >> $output_file

# Activity visualization
add_separator "activity_viz.py"
cat activity_viz.py >> $output_file

# Project configuration
add_separator "pyproject.toml"
cat pyproject.toml >> $output_file

# README
add_separator "README.md"
cat README.md >> $output_file

echo "Files have been concatenated into $output_file"
