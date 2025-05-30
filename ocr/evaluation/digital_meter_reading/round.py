#!/usr/bin/env python3
"""
Script to round ocr_predicted values to 2 decimal places
"""

import json
import os

def round_predictions(input_file_path, output_file_path):
    """
    Read JSON file and round ocr_predicted values to 2 decimal places
    
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
            # Check if the item has ocr_predicted field
            if 'ocr_predicted' in item and item['ocr_predicted'] != "":
                try:
                    # Convert to float, round to 2 decimal places, then convert back to string
                    original_value = item['ocr_predicted']
                    float_value = float(str(original_value))
                    rounded_value = round(float_value, 2)
                    
                    # Convert back to string, removing unnecessary trailing zeros
                    if rounded_value == int(rounded_value):
                        item['ocr_predicted'] = str(int(rounded_value))
                    else:
                        item['ocr_predicted'] = f"{rounded_value:.2f}".rstrip('0').rstrip('.')
                    
                    if str(original_value) != item['ocr_predicted']:
                        modified_count += 1
                        print(f"ID {item.get('id', 'unknown')}: {original_value} -> {item['ocr_predicted']}")
                        
                except (ValueError, TypeError):
                    # Skip if the value cannot be converted to float
                    print(f"Warning: Could not convert '{item['ocr_predicted']}' to float for ID {item.get('id', 'unknown')}")
                    continue
        
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
    output_file_path = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading/annotated_tonnage_rounded.json"
    
    print("Rounding ocr_predicted values to 2 decimal places...")
    round_predictions(input_file_path, output_file_path)

if __name__ == "__main__":
    main()
