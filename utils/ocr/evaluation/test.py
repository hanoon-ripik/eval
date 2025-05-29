import json
import os

# JSON file path - modify this variable to point to your JSON file
JSON_FILE_PATH = "test_data.json"

def levenshtein_distance(s1, s2):
    """
    Calculate the Levenshtein distance between two strings.
    This represents the minimum number of single-character edits 
    (insertions, deletions, or substitutions) required to change one string into another.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = list(range(len(s2) + 1))
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            # Cost of insertions, deletions, and substitutions
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]

def calculate_cer(reference, prediction):
    """
    Calculate Character Error Rate (CER).
    CER = Levenshtein distance / Number of characters in reference
    """
    if len(reference) == 0:
        return 1.0 if len(prediction) > 0 else 0.0
    
    distance = levenshtein_distance(reference, prediction)
    return distance / len(reference)

def load_and_evaluate_json(json_path):
    """
    Load JSON file and calculate CER for each entry, along with exact match count.
    """
    if not os.path.exists(json_path):
        print(f"Error: JSON file '{json_path}' not found.")
        return
    
    total_cer = 0.0
    exact_matches = 0
    total_rows = 0
    
    with open(json_path, 'r', encoding='utf-8') as jsonfile:
        data = json.load(jsonfile)
        
        for entry in data:
            true_value = entry["true"]
            predicted_value = entry["predicted"]
            
            # Calculate CER for this entry
            cer = calculate_cer(true_value, predicted_value)
            total_cer += cer
            
            # Check for exact match
            is_exact_match = true_value == predicted_value
            if is_exact_match:
                exact_matches += 1
            
            total_rows += 1
    
    if total_rows == 0:
        print("No data found in JSON file.")
        return
    
    # Calculate averages
    average_cer = total_cer / total_rows
    
    print(f"Average CER: {average_cer:.4f}")
    print(f"Total Absolute Matches: {exact_matches}")

def main():
    """
    Main function to run the CER evaluation.
    """
    # Load and evaluate the JSON file
    load_and_evaluate_json(JSON_FILE_PATH)

if __name__ == "__main__":
    main()
