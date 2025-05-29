#!/usr/bin/env python3
"""
Script to fill ocr_predicted with "0" when ocr_annotated is "0" and ocr_predicted is empty
"""

import json
import os

def fill_zero_predictions(input_file_path, output_file_path):
    """
    Read JSON file and fill ocr_predicted with "0" when ocr_annotated is "0" and ocr_predicted is empty
    
    Args:
        input_file_path (str): Path to the input JSON file
        output_file_path (str): Path to save the modified JSON file
    """
    try:
        # Read the input JSON file
        with open(input_file_path, 'r') as f:
            data = json.load(f)
        
        modified_count = 0
        
        # Process each item in the data
        for item in data:
            # Check if the item has the required fields
            if 'ocr_annotated' in item and 'ocr_predicted' in item:
                # If ocr_annotated is "0" and ocr_predicted is empty string, set ocr_predicted to "0"
                if item['ocr_annotated'] == "0" and item['ocr_predicted'] == "":
                    item['ocr_predicted'] = "0"
                    modified_count += 1
                    print(f"Modified ID {item.get('id', 'unknown')}: set ocr_predicted to '0'")
        
        # Save the modified data to output file
        with open(output_file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        print(f"\nProcessing complete!")
        print(f"Modified {modified_count} entries")
        print(f"Saved results to: {output_file_path}")
        
    except FileNotFoundError:
        print(f"Error: File not found - {input_file_path}")
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {input_file_path}")
    except Exception as e:
        print(f"Error: {e}")

def main():
    """Main function to execute the script"""
    input_file_path = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading/annotated_tonnage.json"
    output_file_path = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading/annotated_zero_tonnage.json"
    
    print("Filling zero predictions in tonnage data...")
    fill_zero_predictions(input_file_path, output_file_path)

if __name__ == "__main__":
    main()
