#!/usr/bin/env python3
"""
Script to find IDs where ocr_predicted is not equal to ocr_annotated
"""

import json
import os

def find_incorrect_predictions(json_file_path):
    """
    Read JSON file and find IDs where ocr_predicted != ocr_annotated
    
    Args:
        json_file_path (str): Path to the JSON file
    
    Returns:
        list: List of IDs where predictions don't match annotations
    """
    incorrect_ids = []
    
    try:
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        for item in data:
            # Skip items that don't have required fields
            if 'id' not in item or 'ocr_predicted' not in item or 'ocr_annotated' not in item:
                continue
            
            # Convert both values to strings for comparison to handle mixed types
            predicted = str(item['ocr_predicted']).strip()
            annotated = str(item['ocr_annotated']).strip()
            
            # Check if they are not equal
            if predicted != annotated:
                incorrect_ids.append({
                    'id': item['id'],
                    'predicted': item['ocr_predicted'],
                    'annotated': item['ocr_annotated']
                })
    
    except FileNotFoundError:
        print(f"Error: File not found - {json_file_path}")
        return []
    except json.JSONDecodeError:
        print(f"Error: Invalid JSON format in {json_file_path}")
        return []
    except Exception as e:
        print(f"Error: {e}")
        return []
    
    return incorrect_ids

def main():
    """Main function to execute the script"""
    json_file_path = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading/annotated_tonnage.json"
    
    # Find incorrect predictions
    incorrect_items = find_incorrect_predictions(json_file_path)
    
    if not incorrect_items:
        print("No mismatches found! All predictions match annotations.")
    else:
        # Print details of mismatches in a clean format
        for item in incorrect_items:
            print(f"ID: {item['id']}, Predicted: {item['predicted']}, Annotated: {item['annotated']}")

if __name__ == "__main__":
    main()
