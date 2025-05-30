#!/usr/bin/env python3
"""
Script to delete entries with odd IDs from clean.json and remove corresponding image files
from the downloads folder.
"""

import json
import os
import sys

def delete_odd_entries():
    """Delete odd ID entries from clean.json and corresponding image files."""
    
    # Define file paths
    json_file_path = "/Users/hanoon/Documents/eval/ocr/data/coil_id/clean.json"
    downloads_folder = "/Users/hanoon/Documents/eval/ocr/data/coil_id/downloads"
    
    # Check if files exist
    if not os.path.exists(json_file_path):
        print(f"Error: {json_file_path} not found!")
        return False
    
    if not os.path.exists(downloads_folder):
        print(f"Error: {downloads_folder} not found!")
        return False
    
    try:
        # Load the JSON data
        print("Loading clean.json...")
        with open(json_file_path, 'r') as f:
            data = json.load(f)
        
        # Find entries with odd IDs
        odd_entries = [entry for entry in data if entry['id'] % 2 == 1]
        even_entries = [entry for entry in data if entry['id'] % 2 == 0]
        
        print(f"Found {len(odd_entries)} entries with odd IDs to delete")
        print(f"Keeping {len(even_entries)} entries with even IDs")
        
        # Delete image files for odd IDs
        deleted_images = 0
        for entry in odd_entries:
            image_filename = entry['download_image']
            image_path = os.path.join(downloads_folder, image_filename)
            
            if os.path.exists(image_path):
                try:
                    os.remove(image_path)
                    print(f"Deleted: {image_filename}")
                    deleted_images += 1
                except OSError as e:
                    print(f"Error deleting {image_filename}: {e}")
            else:
                print(f"Warning: {image_filename} not found in downloads folder")
        
        # Create backup of original JSON
        backup_path = json_file_path + ".backup"
        print(f"Creating backup at {backup_path}")
        with open(backup_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        # Save the filtered data (only even IDs) back to clean.json
        print("Updating clean.json with only even ID entries...")
        with open(json_file_path, 'w') as f:
            json.dump(even_entries, f, indent=2)
        
        print(f"\nSummary:")
        print(f"- Deleted {len(odd_entries)} entries from clean.json")
        print(f"- Deleted {deleted_images} image files")
        print(f"- Remaining entries in clean.json: {len(even_entries)}")
        print(f"- Backup created at: {backup_path}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

if __name__ == "__main__":
    print("Starting deletion of odd ID entries...")
    success = delete_odd_entries()
    
    if success:
        print("✅ Operation completed successfully!")
        sys.exit(0)
    else:
        print("❌ Operation failed!")
        sys.exit(1)
