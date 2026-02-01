"""
TOPSIS (Technique for Order Preference by Similarity to Ideal Solution)
Python package for multi-criteria decision analysis

Author: Your Name
Roll Number: Your Roll Number
"""

import sys
import pandas as pd
import numpy as np
import os


def validate_inputs_package(input_file, weights_str, impacts_str):
    """
    Validate inputs for package usage
    Returns: df, weights list, impacts list, or raises ValueError
    """
    # Check if input file exists
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"File '{input_file}' not found!")
    
    # Check if file is Excel
    if not input_file.endswith('.xlsx'):
        raise ValueError("Input file must be an Excel file (.xlsx)!")
    
    # Read the Excel file
    try:
        df = pd.read_excel(input_file, engine='openpyxl')
    except Exception as e:
        raise ValueError(f"Error reading Excel file: {e}")
    
    # Check minimum columns
    if df.shape[1] < 3:
        raise ValueError(f"Input file must contain at least 3 columns! Found: {df.shape[1]} columns")
    
    # Check if criteria columns are numeric
    criteria_columns = df.columns[1:]
    for col in criteria_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"Column '{col}' contains non-numeric values! All criteria columns must be numeric.")
    
    # Parse weights
    try:
        weights = [float(w.strip()) for w in weights_str.split(',')]
    except ValueError:
        raise ValueError("Weights must be numeric values separated by commas! Example: '1,1,1,2'")
    
    # Parse impacts
    impacts = [i.strip() for i in impacts_str.split(',')]
    
    # Check if all impacts are + or -
    for impact in impacts:
        if impact not in ['+', '-']:
            raise ValueError(f"Invalid impact '{impact}'! Impacts must be '+' or '-' only.")
    
    # Check counts
    num_criteria = len(criteria_columns)
    if len(weights) != num_criteria:
        raise ValueError(f"Number of weights ({len(weights)}) does not match number of criteria ({num_criteria})!")
    
    if len(impacts) != num_criteria:
        raise ValueError(f"Number of impacts ({len(impacts)}) does not match number of criteria ({num_criteria})!")
    
    return df, weights, impacts


def normalize_matrix(df):
    """
    Normalize the decision matrix using vector normalization
    """
    criteria_data = df.iloc[:, 1:].values
    norms = np.sqrt(np.sum(criteria_data**2, axis=0))
    normalized = criteria_data / norms
    return normalized


def apply_weights(normalized_matrix, weights):
    """
    Apply weights to the normalized matrix
    """
    return normalized_matrix * weights


def calculate_ideal_solutions(weighted_matrix, impacts):
    """
    Calculate ideal best and ideal worst solutions
    """
    ideal_best = []
    ideal_worst = []
    
    for i, impact in enumerate(impacts):
        if impact == '+':
            ideal_best.append(np.max(weighted_matrix[:, i]))
            ideal_worst.append(np.min(weighted_matrix[:, i]))
        else:
            ideal_best.append(np.min(weighted_matrix[:, i]))
            ideal_worst.append(np.max(weighted_matrix[:, i]))
    
    return np.array(ideal_best), np.array(ideal_worst)


def calculate_distances(weighted_matrix, ideal_best, ideal_worst):
    """
    Calculate Euclidean distance from ideal solutions
    """
    distance_to_best = np.sqrt(np.sum((weighted_matrix - ideal_best)**2, axis=1))
    distance_to_worst = np.sqrt(np.sum((weighted_matrix - ideal_worst)**2, axis=1))
    return distance_to_best, distance_to_worst


def calculate_topsis_score(distance_to_best, distance_to_worst):
    """
    Calculate TOPSIS performance score
    """
    scores = distance_to_worst / (distance_to_best + distance_to_worst)
    return scores


def calculate_rank(scores):
    """
    Calculate ranks (1 = best)
    """
    temp = scores.argsort()
    ranks = np.empty_like(temp)
    ranks[temp] = np.arange(len(scores), 0, -1)
    return ranks


def topsis_analysis(input_file, weights, impacts, output_file):
    """
    Perform TOPSIS analysis on the input data
    
    Parameters:
    -----------
    input_file : str
        Path to input Excel file (.xlsx)
    weights : str
        Comma-separated weights (e.g., "1,1,1,2")
    impacts : str
        Comma-separated impacts (e.g., "+,+,-,+")
    output_file : str
        Path to output Excel file (.xlsx)
    
    Returns:
    --------
    pandas.DataFrame
        DataFrame with Topsis Score and Rank columns added
    """
    # Validate inputs
    df, weights_list, impacts_list = validate_inputs_package(input_file, weights, impacts)
    
    # Run TOPSIS
    normalized = normalize_matrix(df)
    weighted = apply_weights(normalized, weights_list)
    ideal_best, ideal_worst = calculate_ideal_solutions(weighted, impacts_list)
    dist_to_best, dist_to_worst = calculate_distances(weighted, ideal_best, ideal_worst)
    scores = calculate_topsis_score(dist_to_best, dist_to_worst)
    ranks = calculate_rank(scores)
    
    # Add results
    df['Topsis Score'] = scores
    df['Rank'] = ranks.astype(int)
    
    # Save to file
    df.to_excel(output_file, index=False, engine='openpyxl')
    
    return df


def main():
    """
    Command-line interface for TOPSIS package
    """
    if len(sys.argv) != 5:
        print("❌ Error: Incorrect number of arguments!")
        print("Usage: python -m Topsis-YourName-RollNumber <InputFile> <Weights> <Impacts> <OutputFile>")
        print("Example: python -m Topsis-YourName-RollNumber data.xlsx \"1,1,1,2\" \"+,+,-,+\" output.xlsx")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]
    
    try:
        print("=" * 60)
        print("TOPSIS - Multi-Criteria Decision Analysis")
        print("=" * 60)
        
        result_df = topsis_analysis(input_file, weights, impacts, output_file)
        
        print(f"✓ Alternatives: {result_df.shape[0]}")
        print(f"✓ Criteria: {result_df.shape[1] - 3}")
        print(f"✓ Results saved to: {output_file}")
        print()
        print("Top 3 Alternatives:")
        print("-" * 60)
        
        top_3 = result_df.nsmallest(3, 'Rank')
        for idx, row in top_3.iterrows():
            print(f"Rank {int(row['Rank'])}: {row.iloc[0]} (Score: {row['Topsis Score']:.4f})")
        
        print("=" * 60)
        print("✓ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
