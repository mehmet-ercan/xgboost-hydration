import pandas as pd

def normalize_composition(df):
    comp_cols = ['N2','CO2','CH4','C2H6','C3H8','iC4','nC4',
                 'neoC5','iC5','nC5','nC6','nC7','nC8','nC9']
    total = df[comp_cols].sum(axis=1)
    for c in comp_cols:
        df[c] = df[c] / total
    return df

def hydrate_fe(df):
    df["C3plus"] = df["C3H8"] + df["iC4"] + df["nC4"] + df["neoC5"] + df["iC5"] + df["nC5"] + df["nC6"] + df["nC7"] + df["nC8"] + df["nC9"]
    df["C1_fraction"] = df["CH4"]
    df["C2plus_to_C1"] = (df["C2H6"] + df["C3plus"]) / (df["CH4"] + 1e-6)
    df["diluents_to_C1"] = (df["N2"] + df["CO2"]) / (df["CH4"] + 1e-6)
    df["C1_to_allHC"] = df["CH4"] / (df["CH4"] + df["C2H6"] + df["C3plus"] + 1e-6)
    df["C2_to_C3"] = df["C2H6"] / (df["C3H8"] + 1e-6)
    return df

def fe_transform(X):
    X = X.copy()
    X = normalize_composition(X)
    X = hydrate_fe(X)
    return X
