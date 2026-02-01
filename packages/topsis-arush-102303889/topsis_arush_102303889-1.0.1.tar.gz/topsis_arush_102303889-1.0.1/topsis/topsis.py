import sys
import pandas as pd
import numpy as np

def topsis(input_file, weights, impacts, output_file):
    data = pd.read_csv(input_file)
    matrix = data.iloc[:, 1:].values.astype(float)

    n = matrix.shape[1]

    if len(weights) != n or len(impacts) != n:
        raise ValueError("Number of weights and impacts must match criteria")

    weights = np.array(weights) / sum(weights)

    norm = np.sqrt((matrix ** 2).sum(axis=0))
    normalized = matrix / norm
    weighted = normalized * weights

    ideal_best, ideal_worst = [], []

    for i in range(n):
        if impacts[i] == '+':
            ideal_best.append(weighted[:, i].max())
            ideal_worst.append(weighted[:, i].min())
        else:
            ideal_best.append(weighted[:, i].min())
            ideal_worst.append(weighted[:, i].max())

    dist_best = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = dist_worst / (dist_best + dist_worst)
    data["Topsis Score"] = score
    data["Rank"] = data["Topsis Score"].rank(ascending=False).astype(int)

    data.to_csv(output_file, index=False)

def main():
    if len(sys.argv) != 5:
        print("Usage: topsis input.csv \"1,1,1\" \"+,+,-\" output.csv")
        sys.exit(1)

    input_file = sys.argv[1]
    weights = list(map(float, sys.argv[2].split(',')))
    impacts = sys.argv[3].split(',')
    output_file = sys.argv[4]

    topsis(input_file, weights, impacts, output_file)
