import json
import os

# JSON file path - modify this variable to point to your JSON file
JSON_FILE_PATH = "digital_meter_reading/gemini_2_5_flash_preview_tonnage.json"

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

def calculate_general_metrics(true_positives, false_positives, false_negatives, true_negatives):
    """
    Calculate precision, recall, accuracy, and F1 score.
    """
    # Precision = TP / (TP + FP)
    precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0.0
    
    # Recall = TP / (TP + FN)
    recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0.0
    
    # Accuracy = (TP + TN) / (TP + FP + FN + TN)
    total = true_positives + false_positives + false_negatives + true_negatives
    accuracy = (true_positives + true_negatives) / total if total > 0 else 0.0
    
    # F1 Score = 2 * (Precision * Recall) / (Precision + Recall)
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return precision, recall, accuracy, f1_score

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
    Load JSON file and calculate metrics including CER, exact matches, and classification metrics.
    """
    if not os.path.exists(json_path):
        print(f"Error: JSON file '{json_path}' not found.")
        return
    
    total_cer = 0.0
    exact_matches = 0
    total_rows = 0
    mismatches = []  # Store entries that don't match exactly
    
    # For classification metrics (treating exact match as positive class)
    true_positives = 0   # Exact matches
    false_positives = 0  # No exact match but prediction was made
    false_negatives = 0  # No exact match (since we always have annotations and predictions, this equals false_positives)
    true_negatives = 0   # Not applicable in this binary exact match scenario
    
    with open(json_path, 'r', encoding='utf-8') as jsonfile:
        data = json.load(jsonfile)
        
        for entry in data:
            # Handle the number plate recognition JSON format
            true_value = entry["ocr_annotated"]
            predicted_value = entry["ocr_predicted"]
            
            # Skip entries where annotated value is empty
            if not true_value:
                continue
            
            # Calculate CER for this entry
            cer = calculate_cer(true_value, predicted_value)
            total_cer += cer
            
            # Check for exact match
            is_exact_match = true_value == predicted_value
            if is_exact_match:
                exact_matches += 1
                true_positives += 1
            else:
                false_positives += 1
                false_negatives += 1
                # Store mismatch information
                mismatches.append({
                    'id': entry.get('id', 'unknown'),
                    'predicted': predicted_value,
                    'annotated': true_value,
                    'cer': cer
                })
            
            total_rows += 1
    
    if total_rows == 0:
        print("No data found in JSON file.")
        return
    
    # Calculate averages and metrics
    average_cer = total_cer / total_rows
    match_percentage = (exact_matches / total_rows) * 100
    
    # Calculate classification metrics
    precision, recall, accuracy, f1_score = calculate_general_metrics(
        true_positives, false_positives, false_negatives, true_negatives
    )
    
    # Print results in organized sections
    print("=" * 60)
    print("OCR EVALUATION RESULTS")
    print("=" * 60)
    print(f"Total Samples Evaluated: {total_rows}")
    print()
    
    print("1. OCR METRICS:")
    print("-" * 30)
    print(f"   Average CER (Character Error Rate): {average_cer:.4f}")
    print(f"   Exact Match Count: {exact_matches}/{total_rows}")
    print()
    
    print("2. GENERAL METRICS:")
    print("-" * 30)
    print(f"   Precision: {precision:.4f}")
    print(f"   Recall: {recall:.4f}")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   F1 Score: {f1_score:.4f}")
    print("=" * 60)
    
    # Print mismatches if any
    if mismatches:
        print()
        print("3. NON-EXACT MATCHES:")
        print("-" * 30)
        print(f"   Total Mismatches: {len(mismatches)}")
        print()
        for i, mismatch in enumerate(mismatches, 1):
            print(f"   {i}. ID: {mismatch['id']}")
            print(f"      Predicted: '{mismatch['predicted']}'")
            print(f"      Annotated: '{mismatch['annotated']}'")
            print(f"      CER: {mismatch['cer']:.4f}")
            print()
        print("=" * 60)

def main():
    """
    Main function to run the CER evaluation.
    """
    # Load and evaluate the JSON file
    load_and_evaluate_json(JSON_FILE_PATH)

if __name__ == "__main__":
    main()
