import os
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge
from ..config import paths, rapm

def explode_players(df):
    # Each stint becomes two equal-weight rows: teamA on offense vs teamB, and vice-versa.
    # For simplicity, we treat pts_per_poss_diff as the target for teamA - teamB.
    # Design matrix: for each player p, +1 if on teamA, -1 if on teamB in the row.
    rows = []
    for _, r in df.iterrows():
        rows.append({
            "players_plus": r["players_teamA"],
            "players_minus": r["players_teamB"],
            "y": r["pts_per_poss_diff"],
            "w": r["possessions"]
        })
    return pd.DataFrame(rows)

def build_matrix(stints_df):
    df = explode_players(stints_df)

    # Get unique player ids
    all_players = sorted(list(set(p for lst in (df["players_plus"].tolist() + df["players_minus"].tolist()) for p in lst)))
    player_index = {pid:i for i, pid in enumerate(all_players)}

    n = len(df)
    p = len(all_players)
    X = np.zeros((n, p), dtype=np.float32)

    for i, row in df.iterrows():
        for pid in row["players_plus"]:
            X[i, player_index[pid]] += 1.0
        for pid in row["players_minus"]:
            X[i, player_index[pid]] -= 1.0

    y = df["y"].values.astype(np.float32)
    w = df["w"].values.astype(np.float32)
    return X, y, w, all_players

def fit_rapm(X, y, w, alpha):
    # Weighted ridge
    model = Ridge(alpha=alpha, fit_intercept=False, random_state=42)
    model.fit(X, y, sample_weight=w)
    coefs = model.coef_
    return model, coefs

def main():
    stints_path = os.path.join(paths.data_interim, "stints.parquet")
    assert os.path.exists(stints_path), "Run `make build` first to create stints."
    stints = pd.read_parquet(stints_path)

    X, y, w, players = build_matrix(stints)
    model, coefs = fit_rapm(X, y, w, rapm.alpha)

    df_out = pd.DataFrame({"PLAYER_ID": players, "RAPM": coefs})
    df_out = df_out.sort_values("RAPM", ascending=False).reset_index(drop=True)

    os.makedirs(paths.data_processed, exist_ok=True)
    out_path = os.path.join(paths.data_processed, "rapm_leaderboard.csv")
    df_out.to_csv(out_path, index=False)
    print(f"Saved RAPM leaderboard → {out_path}")

if __name__ == "__main__":
    main()
