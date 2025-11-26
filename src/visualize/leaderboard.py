import os
import pandas as pd
import plotly.graph_objects as go
from ..config import paths

def main():
    path = os.path.join(paths.data_processed, "rapm_leaderboard.csv")
    df = pd.read_csv(path)
    # If you have a player-id to name map, merge it here; otherwise show ids.
    top = df.head(25)

    fig = go.Figure(data=[go.Table(
        header=dict(values=["Rank","PLAYER_ID","RAPM"], align="left"),
        cells=dict(values=[range(1, len(top)+1), top["PLAYER_ID"], top["RAPM"].round(3)],
                   align="left")
    )])
    fig.update_layout(title="NBA RAPM (prototype)")
    os.makedirs(paths.data_processed, exist_ok=True)
    html_path = os.path.join(paths.data_processed, "rapm_leaderboard.html")
    fig.write_html(html_path)
    print(f"Wrote {html_path}")

if __name__ == "__main__":
    main()
