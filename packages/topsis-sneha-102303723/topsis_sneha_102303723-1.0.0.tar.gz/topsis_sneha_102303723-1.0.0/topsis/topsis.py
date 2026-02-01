import sys
import pandas as pd
import numpy as np
import os 
def main():
  # 1. Check number of arguments
    if len(sys.argv) != 5:
        print("Error: Incorrect number of parameters")
        sys.exit(1)
    
    input_file = sys.argv[1]
    weights = sys.argv[2]
    impacts = sys.argv[3]
    output_file = sys.argv[4]

  # File Existence check
    if not os.path.isfile(input_file):
      print("Error: File not found")
      sys.exit(1)
    
  # Read the Input File
    try:
      data = pd.read_csv(input_file)
    except:
      print("Error: Unable to read input file")
      sys.exit(1)

  # 4. Minimum 3 columns
    if data.shape[1] < 3:
        print("Error: Input file must contain at least 3 columns")
        sys.exit(1)

  # 5. Extract criteria columns
    criteria = data.iloc[:, 1:]
  
  # 6. Numeric check
    if not np.all(criteria.applymap(np.isreal)):
        print("Error: Non-numeric value found")
        sys.exit(1)
  
  # 7. Parse weights & impacts
    try:
        weights = list(map(float, weights.split(',')))
        impacts = impacts.split(',')
    except:
        print("Error: Invalid weights or impacts format")
        sys.exit(1)
  
  # 8. Length check
    if len(weights) != criteria.shape[1] or len(impacts) != criteria.shape[1]:
        print("Error: Number of weights/impacts must match number of criteria")
        sys.exit(1)

  # 9. Impact validation
    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be + or -")
            sys.exit(1)

  # TOPSIS
  # Step 1: Normalize
    norm = criteria / np.sqrt((criteria ** 2).sum())
  
  # Step 2: Weight multiplication
    weighted = norm * weights
  
  # Step 3: Ideal best & worst
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

  # Step 4: Distance measures (Euclidean)
    s_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    s_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

 # Step 5: Topsis score
    score = s_neg / (s_pos + s_neg)

# Step 6: Rank
    data['Topsis Score'] = score
    data['Rank'] = data['Topsis Score'].rank(ascending=False, method='dense').astype(int)


 # Save output
    data.to_csv(output_file, index=False)
    print("Output saved to", output_file)

if __name__ == "__main__":
    main()

