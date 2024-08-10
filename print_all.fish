#!/usr/bin/env fish

# List all .py files in the current directory
set py_files (ls *.py)

# Clear the output file at the beginning
echo -n "" > output.txt

# Iterate over each Python file
for file in $py_files
    echo "Processing: $file"
    
    # Write the file name to output.txt
    echo "----- $file -----" >> output.txt
    
    # Write the contents of the file to output.txt
    cat $file >> output.txt
    
    # Add a separator (optional)
    echo "\n\n" >> output.txt
end

echo "Done! Contents written to output.txt"

