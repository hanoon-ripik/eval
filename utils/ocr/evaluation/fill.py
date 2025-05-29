#!/usr/bin/env python3
"""
Script to fill empty ocr_annotated fields with ocr_predicted values
"""

import json
import os

def fill_empty_annotations(json_path):
    """
    Read the JSON file and fill empty ocr_annotated fields with ocr_predicted values
    """
    if not os.path.exists(json_path):
        print(f"Error: JSON file '{json_path}' not found.")
        return
    
    # Read the JSON file
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    filled_count = 0
    total_count = len(data)
    
    # Process each entry
    for entry in data:
        # Check if ocr_annotated is empty or missing
        if not entry.get("ocr_annotated", "").strip():
            # Fill with ocr_predicted value
            entry["ocr_annotated"] = entry.get("ocr_predicted", "")
            filled_count += 1
    
    # Write back to the same file
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {total_count} entries")
    print(f"Filled {filled_count} empty ocr_annotated fields")
    print(f"Updated file: {json_path}")

def main():
    """
    Main function
    """
    json_file_path = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/number_plate_recognition.json"
    fill_empty_annotations(json_file_path)

if __name__ == "__main__":
    main()