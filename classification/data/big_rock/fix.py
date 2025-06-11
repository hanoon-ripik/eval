#!/usr/bin/env python3
"""
Script to fix clean.json by replacing 'big_rock_detected_annotated' with 'big_rock_detected_truth'
for objects where 'big_rock_detected_predicted' is false.
"""

import json
import os
from typing import Dict, List, Any


def load_json(file_path: str) -> List[Dict[str, Any]]:
    """Load JSON data from file."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save_json(data: List[Dict[str, Any]], file_path: str) -> None:
    """Save JSON data to file with proper formatting."""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fix_big_rock_data(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Fix the big rock data:
    - For objects where 'big_rock_detected_predicted' is false: 
      replace 'big_rock_detected_annotated' with 'big_rock_detected_truth'
    - For objects where 'big_rock_detected_predicted' is true:
      add 'big_rock_detected_truth' key and replace 'big_rock_detected_annotated' with 'big_rock_annotated_correct'
    """
    fixed_data = []
    false_predicted_changes = 0
    true_predicted_changes = 0
    
    for item in data:
        # Create a copy of the item
        fixed_item = item.copy()
        
        # Check if big_rock_detected_predicted is false
        if fixed_item.get('big_rock_detected_predicted') is False:
            # Replace the field name
            if 'big_rock_detected_annotated' in fixed_item:
                # Get the value and remove the old key
                annotated_value = fixed_item.pop('big_rock_detected_annotated')
                # Add the new key with the same value
                fixed_item['big_rock_detected_truth'] = annotated_value
                false_predicted_changes += 1
        
        # Check if big_rock_detected_predicted is true
        elif fixed_item.get('big_rock_detected_predicted') is True:
            # Add big_rock_detected_truth key (empty string by default)
            fixed_item['big_rock_detected_truth'] = ""
            
            # Replace big_rock_detected_annotated with big_rock_annotated_correct
            if 'big_rock_detected_annotated' in fixed_item:
                # Get the value and remove the old key
                annotated_value = fixed_item.pop('big_rock_detected_annotated')
                # Add the new key with the same value
                fixed_item['big_rock_annotated_correct'] = annotated_value
                true_predicted_changes += 1
        
        fixed_data.append(fixed_item)
    
    print(f"Applied fixes to {false_predicted_changes} objects where big_rock_detected_predicted was false")
    print(f"Applied fixes to {true_predicted_changes} objects where big_rock_detected_predicted was true")
    return fixed_data


def main():
    """Main function to process the clean.json file."""
    # Define file paths
    input_file = 'clean.json'
    backup_file = 'clean_backup.json'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found in current directory")
        return
    
    print(f"Loading data from {input_file}...")
    
    try:
        # Load the original data
        original_data = load_json(input_file)
        print(f"Loaded {len(original_data)} objects")
        
        # Create backup
        print(f"Creating backup as {backup_file}...")
        save_json(original_data, backup_file)
        
        # Fix the data
        print("Applying fixes...")
        fixed_data = fix_big_rock_data(original_data)
        
        # Save the fixed data
        print(f"Saving fixed data to {input_file}...")
        save_json(fixed_data, input_file)
        
        print("Fix completed successfully!")
        print(f"Backup saved as: {backup_file}")
        
        # Print summary
        false_predicted_count = sum(1 for item in original_data 
                                  if item.get('big_rock_detected_predicted') is False)
        true_predicted_count = sum(1 for item in original_data 
                                 if item.get('big_rock_detected_predicted') is True)
        
        print(f"\nSummary:")
        print(f"- Total objects: {len(original_data)}")
        print(f"- Objects with big_rock_detected_predicted=false: {false_predicted_count}")
        print(f"- Objects with big_rock_detected_predicted=true: {true_predicted_count}")
        print(f"- Objects modified (false predicted): {false_predicted_count}")
        print(f"- Objects modified (true predicted): {true_predicted_count}")
        
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON format in {input_file}: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
