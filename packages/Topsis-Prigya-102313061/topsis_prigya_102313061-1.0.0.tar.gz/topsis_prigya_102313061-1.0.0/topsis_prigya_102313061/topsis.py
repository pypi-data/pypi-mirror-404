import sys
import os
import pandas as pd
import numpy as np


def show_error(text):
    print("Error:", text)
    sys.exit()


def main():

    if len(sys.argv) != 5:
        show_error("Please provide: input.csv weights impacts output.csv")

    input_csv = sys.argv[1]
    weights_text = sys.argv[2]
    impacts_text = sys.argv[3]
    output_csv = sys.argv[4]

    if not os.path.exists(input_csv):
        show_error("The input file cannot be found")

    try:
        df = pd.read_csv(input_csv)
    except:
        show_error("Problem while reading the CSV file")

    if df.shape[1] < 3:
        show_error("CSV must contain at least three columns")

    values = df.iloc[:, 1:]

    if not np.all(values.applymap(np.isreal)):
        show_error("All criteria columns should contain numbers only")

    try:
        weights = [float(w) for w in weights_text.split(',')]
        impacts = impacts_text.split(',')
    except:
        show_error("Weights and impacts must be separated by commas")

    if len(weights) != values.shape[1] or len(impacts) != values.shape[1]:
        show_error("Weights, impacts and number of criteria do not match")

    if any(i not in ['+', '-'] for i in impacts):
        show_error("Impacts must be + or -")

    # ---- TOPSIS Steps ----

    root_sum_square = np.sqrt((values ** 2).sum())
    norm_matrix = values / root_sum_square

    weighted_matrix = norm_matrix * weights

    best_ref = []
    worst_ref = []

    for idx in range(len(impacts)):
        column = weighted_matrix.iloc[:, idx]
        if impacts[idx] == '+':
            best_ref.append(column.max())
            worst_ref.append(column.min())
        else:
            best_ref.append(column.min())
            worst_ref.append(column.max())

    best_ref = np.array(best_ref)
    worst_ref = np.array(worst_ref)

    dist_best = np.sqrt(((weighted_matrix - best_ref) ** 2).sum(axis=1))
    dist_worst = np.sqrt(((weighted_matrix - worst_ref) ** 2).sum(axis=1))

    final_score = dist_worst / (dist_best + dist_worst)

    df["Topsis Score"] = final_score
    df["Rank"] = final_score.rank(ascending=False).astype(int)

    df.to_csv(output_csv, index=False)
    print("Process completed. Output saved.")


if __name__ == "__main__":
    main()
