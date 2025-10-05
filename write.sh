#!/bin/bash
# for sending to LLMs

find . -type f -name "*.py" -not -path "*/.*" | while read -r file; do
    echo -e "\n========== $file ==========\n"
    cat "$file"
    echo -e "\n================================\n"
done
