import sys
import pandas as pd
import numpy as np
import os

def topsis(input_file, weights, impacts, output_file):

    # ---------- File check ----------
    if not os.path.isfile(input_file):
        print("Error: Input file not found")
        sys.exit(1)

    df = pd.read_csv(input_file)

    if df.shape[1] < 3:
        print("Error: Input file must contain three or more columns")
        sys.exit(1)

    data = df.iloc[:, 1:].values

    try:
        data = data.astype(float)
    except:
        print("Error: From 2nd column to last column must be numeric")
        sys.exit(1)

    weights = weights.split(',')
    impacts = impacts.split(',')

    if len(weights) != data.shape[1] or len(impacts) != data.shape[1]:
        print("Error: Number of weights, impacts and columns must be same")
        sys.exit(1)

    weights = np.array(weights, dtype=float)

    for i in impacts:
        if i not in ['+', '-']:
            print("Error: Impacts must be either + or -")
            sys.exit(1)

    # ---------- Normalize ----------
    norm = np.sqrt((data ** 2).sum(axis=0))
    normalized = data / norm

    # ---------- Weighted ----------
    weighted = normalized * weights

    # ---------- Ideal best & worst ----------
    ideal_best = []
    ideal_worst = []

    for i in range(len(impacts)):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    # ---------- Distance ----------
    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    # ---------- Score ----------
    score = dist_worst / (dist_best + dist_worst)

    df['Topsis Score'] = score
    df['Rank'] = df['Topsis Score'].rank(ascending=False).astype(int)

    df.to_csv(output_file, index=False)
    print("TOPSIS successfully completed")

# ---------- Command line ----------
def main():
    import sys
    if len(sys.argv) != 5:
        print("Usage: topsis <inputfile> <weights> <impacts> <outputfile>")
        sys.exit(1)

    topsis(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
