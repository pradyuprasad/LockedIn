#!/bin/bash
# for sending to LLMs

for file in *.py; do
    echo -e "\n========== $file ==========\n"
    cat "$file"
    echo -e "\n================================\n"
done
