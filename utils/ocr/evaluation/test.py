import csv
import os

# CSV file path - modify this variable to point to your CSV file
CSV_FILE_PATH = "test_data.csv"

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

def load_and_evaluate_csv(csv_path):
    """
    Load CSV file and calculate CER for each row, along with exact match count.
    """
    if not os.path.exists(csv_path):
        print(f"Error: CSV file '{csv_path}' not found.")
        return
    
    total_cer = 0.0
    exact_matches = 0
    total_rows = 0
    
    print(f"Loading CSV file: {csv_path}")
    print("-" * 60)
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        # Skip the first line if it's a comment
        first_line = csvfile.readline().strip()
        if first_line.startswith('//'):
            csvfile.readline()  # Skip the header line too
        else:
            csvfile.seek(0)  # Reset to beginning if first line wasn't a comment
            csvfile.readline()  # Skip header
        
        reader = csv.reader(csvfile)
        
        for row_num, row in enumerate(reader, 1):
            if len(row) < 3:
                continue
                
            # Parse the row (remove quotes and whitespace)
            data_file = row[0].strip().strip('"')
            true_value = row[1].strip().strip('"')
            predicted_value = row[2].strip().strip('"')
            
            # Calculate CER for this row
            cer = calculate_cer(true_value, predicted_value)
            total_cer += cer
            
            # Check for exact match
            is_exact_match = true_value == predicted_value
            if is_exact_match:
                exact_matches += 1
            
            total_rows += 1
            
            # Print details for each row
            print(f"Row {row_num:2d} | File: {data_file:8s} | True: {true_value:12s} | Predicted: {predicted_value:12s} | CER: {cer:.4f} | Exact: {'✓' if is_exact_match else '✗'}")
    
    if total_rows == 0:
        print("No data rows found in CSV file.")
        return
    
    # Calculate averages
    average_cer = total_cer / total_rows
    exact_match_percentage = (exact_matches / total_rows) * 100
    
    print("-" * 60)
    print(f"SUMMARY RESULTS:")
    print(f"Total rows processed: {total_rows}")
    print(f"Average CER: {average_cer:.4f} ({average_cer * 100:.2f}%)")
    print(f"Exact matches: {exact_matches}/{total_rows} ({exact_match_percentage:.2f}%)")

def main():
    """
    Main function to run the CER evaluation.
    """
    print("Character Error Rate (CER) Evaluation")
    print("=" * 60)
    
    # Load and evaluate the CSV file
    load_and_evaluate_csv(CSV_FILE_PATH)

if __name__ == "__main__":
    main()
