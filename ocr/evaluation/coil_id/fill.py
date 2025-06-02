#!/usr/bin/env python3
"""
Fill script to add ocr_annotated values from annotated.json to target JSON file.

This script reads a target JSON file, finds entries by ID, and adds matching
ocr_annotated values from the annotated.json file.
"""

import json
import os
from typing import List, Dict, Any

# Configuration
TARGET_JSON_FILE = "gemini_1_5_pro_coil_id.json"  # File to modify
ANNOTATED_JSON_FILE = "annotated.json"  # Source file


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except FileNotFoundError:
        print(f"Error: File {file_path} not found.")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {file_path}: {e}")
        return []


def save_json(data: List[Dict[str, Any]], file_path: str) -> bool:
    """Save JSON data to file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        print(f"Error saving to {file_path}: {e}")
        return False


def create_id_to_annotation_map(annotated_data: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Create a mapping from ID to ocr_annotated value from annotated.json.
    
    Returns:
        Dict[int, str]: Mapping of ID to ocr_annotated value
    """
    id_map = {}
    for item in annotated_data:
        if 'id' in item and 'ocr_annotated' in item:
            id_map[item['id']] = item['ocr_annotated']
    return id_map


def add_annotations_to_target(target_data: List[Dict[str, Any]], id_map: Dict[int, str]) -> int:
    """
    Add ocr_annotated fields to target data based on ID mapping.
    
    Returns:
        int: Number of fields that were added
    """
    added_count = 0
    
    for item in target_data:
        if 'id' in item:
            item_id = item['id']
            if item_id in id_map:
                # Add ocr_annotated field with the value from annotated.json
                item['ocr_annotated'] = id_map[item_id]
                added_count += 1
                print(f"Added annotation for ID {item_id}: '{id_map[item_id]}'")
    
    return added_count


def main():
    """Main function to execute the annotation addition operation."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    target_file = os.path.join(script_dir, TARGET_JSON_FILE)
    
    print(f"Loading target file: {TARGET_JSON_FILE}...")
    target_data = load_json(target_file)
    
    if not target_data:
        print("No target data loaded. Exiting.")
        return
    
    print(f"Loaded {len(target_data)} entries from target file.")
    
    print(f"Loading annotated file: {ANNOTATED_JSON_FILE}...")
    annotated_data = load_json(ANNOTATED_JSON_FILE)
    
    if not annotated_data:
        print("No annotated data loaded. Exiting.")
        return
    
    print(f"Loaded {len(annotated_data)} entries from annotated file.")
    
    # Create ID to annotation mapping
    print("Creating ID to annotation mapping...")
    id_map = create_id_to_annotation_map(annotated_data)
    print(f"Created mapping for {len(id_map)} IDs.")
    
    # Add annotations to target data
    print("Adding ocr_annotated fields to target data...")
    added_count = add_annotations_to_target(target_data, id_map)
    
    if added_count > 0:
        # Save updated data
        if save_json(target_data, target_file):
            print(f"Successfully added {added_count} annotations.")
            print(f"Updated file saved: {target_file}")
        else:
            print("Error: Could not save updated file.")
    else:
        print("No matching IDs found for annotation addition.")


if __name__ == "__main__":
    main()
