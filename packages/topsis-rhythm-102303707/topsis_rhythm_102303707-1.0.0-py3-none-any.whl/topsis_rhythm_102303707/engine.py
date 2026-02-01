import pandas as pd
import numpy as np

def validate_inputs(df, weights, impacts):
    if df.shape[1] < 3:
        raise ValueError("Input file must have at least 3 columns")

    data = df.iloc[:, 1:]

    for col in data.columns:
        if not pd.to_numeric(data[col], errors="coerce").notnull().all():
            raise ValueError(f"Non-numeric value found in column {col}")

    weights_list = list(map(float, weights.split(",")))
    impacts_list = impacts.split(",")

    if len(weights_list) != data.shape[1] or len(impacts_list) != data.shape[1]:
        raise ValueError("Weights, impacts and number of criteria columns must match")

    for imp in impacts_list:
        if imp not in ["+", "-"]:
            raise ValueError("Impacts must be either + or -")

    return data.astype(float), np.array(weights_list), impacts_list

def run_topsis(input_csv, weights, impacts, output_csv):
    df = pd.read_csv(input_csv)

    data, weights, impacts = validate_inputs(df, weights, impacts)

    norm = data / np.sqrt((data ** 2).sum())
    weighted = norm * weights

    ideal_best = []
    ideal_worst = []

    for i, imp in enumerate(impacts):
        if imp == "+":
            ideal_best.append(weighted.iloc[:, i].max())
            ideal_worst.append(weighted.iloc[:, i].min())
        else:
            ideal_best.append(weighted.iloc[:, i].min())
            ideal_worst.append(weighted.iloc[:, i].max())

    ideal_best = np.array(ideal_best)
    ideal_worst = np.array(ideal_worst)

    d_pos = np.sqrt(((weighted - ideal_best) ** 2).sum(axis=1))
    d_neg = np.sqrt(((weighted - ideal_worst) ** 2).sum(axis=1))

    score = d_neg / (d_pos + d_neg)
    rank = score.rank(ascending=False).astype(int)

    df["Topsis Score"] = score.round(4)
    df["Rank"] = rank

    df.to_csv(output_csv, index=False)
    return output_csv
