import os
import pandas as pd
import streamlit as st

st.set_page_config(page_title="NBA RAPM – Prototype", layout="centered")

st.title("🏀 NBA RAPM – Prototype")
st.caption("Regularized Adjusted Plus-Minus from stint-level play-by-play")

csv_path = os.path.join("data", "processed", "rapm_leaderboard.csv")
if not os.path.exists(csv_path):
    st.warning("No results found. Run: `make fetch build train`")
else:
    df = pd.read_csv(csv_path)
    st.metric("Players Rated", len(df))
    st.dataframe(df.head(50))
    st.download_button("Download CSV", df.to_csv(index=False), "rapm_leaderboard.csv")
