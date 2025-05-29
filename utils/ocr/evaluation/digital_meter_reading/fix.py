import json
import os

def read_json(file_path):
    """Read JSON file and return data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(data, file_path):
    """Write data to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def update_cycle_json():
    """Update annotated_cycle.json by copying ocr_predicted to ocr_annotated when ocr_annotated is empty"""
    
    # Define file path
    base_dir = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading"
    cycle_file = os.path.join(base_dir, "annotated_cycle.json")
    
    # Read cycle data
    try:
        cycle_data = read_json(cycle_file)
        print(f"Read {len(cycle_data)} items from {cycle_file}")
    except FileNotFoundError:
        print(f"Error: {cycle_file} not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error reading JSON: {e}")
        return
    
    # Update items where ocr_annotated is empty
    updated_count = 0
    for item in cycle_data:
        if item.get("ocr_annotated", "") == "":
            item["ocr_annotated"] = item.get("ocr_predicted", "")
            updated_count += 1
    
    # Write updated data back
    write_json(cycle_data, cycle_file)
    print(f"Updated {updated_count} items in {cycle_file}")
    print(f"Total items processed: {len(cycle_data)}")

def main():
    update_cycle_json()

if __name__ == "__main__":
    main()
