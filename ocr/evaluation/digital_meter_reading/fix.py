import json
import os
import re

def read_json(file_path):
    """Read JSON file and return data"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def write_json(data, file_path):
    """Write data to JSON file"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def convert_tonnage_to_decimal(tonnage_str):
    """Convert tonnage string like '7,270' to decimal like 7.27"""
    if not tonnage_str or tonnage_str == "":
        return ""
    
    # Remove any non-digit and non-comma characters
    cleaned = re.sub(r'[^\d,.]', '', str(tonnage_str))
    
    # If already a decimal number, return as is
    if '.' in cleaned:
        try:
            return float(cleaned)
        except ValueError:
            return ""
    
    # If contains comma, convert comma to decimal
    if ',' in cleaned:
        # Split by comma and take first two parts
        parts = cleaned.split(',')
        if len(parts) >= 2:
            # Convert to decimal format: 7,270 -> 7.27
            integer_part = parts[0]
            decimal_part = parts[1][:2] if len(parts[1]) >= 2 else parts[1]
            try:
                result = float(f"{integer_part}.{decimal_part}")
                # Remove trailing zeros
                if result == int(result):
                    return int(result)
                return result
            except ValueError:
                return ""
    
    # If just digits, return as integer
    try:
        return int(cleaned)
    except ValueError:
        return ""

def process_annotated_json():
    """Process annotated.json to convert tonnage values and split into separate files"""
    
    # Define file paths
    base_dir = "/Users/hanoon/Documents/eval/utils/ocr/evaluation/digital_meter_reading"
    annotated_file = os.path.join(base_dir, "annotated.json")
    tonnage_file = os.path.join(base_dir, "annotated_tonnage.json")
    cycle_file = os.path.join(base_dir, "annotated_cycle.json")
    
    # Read annotated data
    try:
        annotated_data = read_json(annotated_file)
        print(f"Read {len(annotated_data)} items from {annotated_file}")
    except FileNotFoundError:
        print(f"Error: {annotated_file} not found")
        return
    except json.JSONDecodeError as e:
        print(f"Error reading JSON: {e}")
        return
    
    tonnage_data = []
    cycle_data = []
    
    for item in annotated_data:
        # Process tonnage data
        if any(key in item for key in ["ocr_tonnage_predicted", "ocr_tonnage_annotated"]):
            tonnage_item = {
                "id": item.get("id"),
                "original_image": item.get("original_image", ""),
                "download_image": item.get("download_image", ""),
                "ocr_predicted": str(item.get("ocr_tonnage_predicted", "")),
                "ocr_annotated": ""
            }
            
            # Convert tonnage annotated value
            tonnage_annotated = item.get("ocr_tonnage_annotated", "")
            if tonnage_annotated:
                converted_tonnage = convert_tonnage_to_decimal(tonnage_annotated)
                tonnage_item["ocr_annotated"] = str(converted_tonnage) if converted_tonnage != "" else ""
            
            tonnage_data.append(tonnage_item)
        
        # Process cycle data
        if any(key in item for key in ["ocr_cycle_predicted", "ocr_cycle_annotated"]):
            cycle_item = {
                "id": item.get("id"),
                "original_image": item.get("original_image", ""),
                "download_image": item.get("download_image", ""),
                "ocr_predicted": str(item.get("ocr_cycle_predicted", "")),
                "ocr_annotated": str(item.get("ocr_cycle_annotated", ""))
            }
            
            cycle_data.append(cycle_item)
    
    # Write tonnage data
    if tonnage_data:
        write_json(tonnage_data, tonnage_file)
        print(f"Created {tonnage_file} with {len(tonnage_data)} items")
    
    # Write cycle data
    if cycle_data:
        write_json(cycle_data, cycle_file)
        print(f"Created {cycle_file} with {len(cycle_data)} items")
    
    print("Processing completed successfully!")

def main():
    process_annotated_json()

if __name__ == "__main__":
    main()
