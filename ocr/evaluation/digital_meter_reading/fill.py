#!/usr/bin/env python3
"""
Script to add ocr_annotated fields from annotated.json to prediction files
"""

import json
import os

# File paths
PREDICTION_FILE_PATH = "gemini_2_5_flash_preview_tonnage.json"
ANNOTATED_FILE_PATH = "annotated_tonnage.json"

def add_annotations_to_predictions():
    """
    Read the prediction file and annotated file, map by ID and add ocr_annotated values
    """
    # Check if files exist
    if not os.path.exists(PREDICTION_FILE_PATH):
        print(f"Error: Prediction file '{PREDICTION_FILE_PATH}' not found.")
        return
    
    if not os.path.exists(ANNOTATED_FILE_PATH):
        print(f"Error: Annotated file '{ANNOTATED_FILE_PATH}' not found.")
        return
    
    # Read the prediction file
    with open(PREDICTION_FILE_PATH, 'r', encoding='utf-8') as f:
        prediction_data = json.load(f)
    
    # Read the annotated file
    with open(ANNOTATED_FILE_PATH, 'r', encoding='utf-8') as f:
        annotated_data = json.load(f)
    
    # Create a mapping from id to ocr_annotated
    id_to_annotation = {}
    for entry in annotated_data:
        if "id" in entry and "ocr_annotated" in entry:
            id_to_annotation[entry["id"]] = entry["ocr_annotated"]
    
    # Add ocr_annotated to prediction data
    added_count = 0
    for entry in prediction_data:
        if "id" in entry:
            entry_id = entry["id"]
            if entry_id in id_to_annotation:
                entry["ocr_annotated"] = id_to_annotation[entry_id]
                added_count += 1
            else:
                entry["ocr_annotated"] = ""  # Add empty string if no annotation found
    
    # Write back to the prediction file
    with open(PREDICTION_FILE_PATH, 'w', encoding='utf-8') as f:
        json.dump(prediction_data, f, indent=2, ensure_ascii=False)
    
    print(f"Processed {len(prediction_data)} entries")
    print(f"Added {added_count} annotations from annotated.json")
    print(f"Updated file: {PREDICTION_FILE_PATH}")

def main():
    add_annotations_to_predictions()

main()