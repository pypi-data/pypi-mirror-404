import sys
import pandas as pd
import numpy as np

def main():
    args = sys.argv

    if len(args) != 5:
        print("Error: Incorrect number of arguments.")
        print("Usage: python topsis.py <input_file> <weights> <impacts> <output_file>")
        sys.exit(1)

    input_file = args[1]
    weights_str = args[2]
    impacts_str = args[3]
    output_file = args[4]

    try:
        weights = list(map(float, weights_str.split(',')))
    except ValueError:
        print("Error: Weights must be numeric and comma-separated.")
        sys.exit(1)

    impacts = impacts_str.split(',')

    for impact in impacts:
        if impact not in ['+', '-']:
            print("Error: Impacts must be either '+' or '-'.")
            sys.exit(1)

    if len(weights) != len(impacts):
        print("Error: Number of weights and impacts must match.")
        sys.exit(1)

    try:
        df = pd.read_csv(input_file)
    except FileNotFoundError:
        print(f"Error: File '{input_file}' not found.")
        sys.exit(1)

    if df.shape[1] < 3:
        print("Error: Input file must contain at least three columns.")
        sys.exit(1)

    numeric_df = df.iloc[:, 1:]
    numeric_df = numeric_df.apply(pd.to_numeric, errors='coerce')

    if numeric_df.isnull().values.any():
        print("Error: From second to last column, all values must be numeric.")
        sys.exit(1)
        
    
    denominator = np.sqrt((numeric_df**2).sum())
    
    if (denominator == 0).any():
        print("Error: Division by zero encountered during normalization.")
        sys.exit(1)

    normalized_df = numeric_df / denominator
    
    if len(weights) != normalized_df.shape[1]:
        print("Error: Number of weights does not match number of criteria columns.")
        sys.exit(1)
    weighted = normalized_df * weights
  
  
    ideal_best = []
    ideal_worst = []
    
    for i in range(weighted.shape[1]):
        col = weighted.iloc[ : , i]
        if impacts[i] == '+':
            ideal_best.append(col.max())
            ideal_worst.append(col.min())
        else:
            ideal_best.append(col.min())
            ideal_worst.append(col.max())


    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)


    s_plus = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_minus = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))
    
    performance_score = s_minus / (s_plus + s_minus)
    
    df["Topsis Score"] = performance_score
    df["Rank"] = df["Topsis Score"].rank(ascending=False, method="dense").astype(int)
    
    df.to_csv(output_file, index=False)
    print(f"Result saved to '{output_file}'")


def run():
    main()

if __name__ == "__main__":
    run()