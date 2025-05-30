#!/usr/bin/env python3
"""
Clean script to filter out entries with empty coilId from raw.json
"""

import json
import os

def clean_coil_data(input_file="raw.json"):
    """
    Read raw.json and remove entries where coilId is empty string.
    Updates the original file directly.
    
    Args:
        input_file (str): Input JSON file path to be modified
    """
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found!")
        return
    
    try:
        # Load JSON data
        print(f"Loading data from {input_file}...")
        with open(input_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Check if data is empty
        if not data:
            print("Error: JSON file is empty!")
            return
        
        print(f"Loaded {len(data)} entries from {input_file}")
        
        # Filter out entries with empty coilId
        original_count = len(data)
        filtered_data = [entry for entry in data if entry.get("coilId", "") != ""]
        filtered_count = len(filtered_data)
        removed_count = original_count - filtered_count
        
        print(f"Filtering complete: {removed_count} entries to be removed")
        
        # Write cleaned data back to the same file
        print(f"Writing cleaned data back to {input_file}...")
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(filtered_data, f, indent=2, ensure_ascii=False)
        
        print(f"Successfully cleaned {input_file}")
        print(f"Original entries: {original_count}")
        print(f"Entries with non-empty coilId: {filtered_count}")
        print(f"Entries removed (empty coilId): {removed_count}")
        print(f"File {input_file} has been updated in place")
        
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
    except Exception as e:
        print(f"Error during cleaning: {e}")

def main():
    """Main function to run the cleaning process."""
    print("Cleaning coil data - removing entries with empty coilId from raw.json...")
    clean_coil_data()

main()
