import os
import json
from tqdm import tqdm
import pandas as pd
from nba_api.stats.endpoints import leaguegamefinder, playbyplayv2, boxscoretraditionalv2
from nba_api.stats.library.parameters import SeasonType
from datetime import datetime
from ..config import paths, season

def ensure_dirs():
    os.makedirs(paths.data_raw, exist_ok=True)

def get_games():
    # Query games by season & date filter
    lgf = leaguegamefinder.LeagueGameFinder(
        season_nullable=season.season,
        season_type_nullable=SeasonType.regular
    )
    df = lgf.get_data_frames()[0]

    # Filter by date window
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    mask = (df["GAME_DATE"] >= pd.to_datetime(season.start_date)) & (df["GAME_DATE"] <= pd.to_datetime(season.end_date))
    df = df.loc[mask].sort_values("GAME_DATE")
    if season.max_games:
        df = df.head(season.max_games)
    return df

def fetch_pbp_for_game(game_id: str) -> pd.DataFrame:
    pbp = playbyplayv2.PlayByPlayV2(game_id=game_id).get_data_frames()[0]
    pbp["GAME_ID"] = game_id
    return pbp

def fetch_starters_for_game(game_id: str):
    # Use boxscoretraditionalv2 to infer starters by MIN & START_POSITION when available
    box = boxscoretraditionalv2.BoxScoreTraditionalV2(game_id=game_id).get_data_frames()[0]
    starters = box[box["START_POSITION"].notna()][["TEAM_ID","PLAYER_ID","PLAYER_NAME","START_POSITION"]]
    return starters

def main():
    ensure_dirs()
    games = get_games()
    games.to_csv(os.path.join(paths.data_raw, "games.csv"), index=False)

    all_pbp = []
    starters_records = []
    for _, row in tqdm(games.iterrows(), total=len(games), desc="Fetching games"):
        gid = row["GAME_ID"]
        try:
            pbp = fetch_pbp_for_game(gid)
            all_pbp.append(pbp)
            starters = fetch_starters_for_game(gid)
            starters["GAME_ID"] = gid
            starters_records.append(starters)
        except Exception as e:
            print(f"[WARN] skip {gid}: {e}")

    if all_pbp:
        pbp_df = pd.concat(all_pbp, ignore_index=True)
        pbp_df.to_csv(os.path.join(paths.data_raw, "pbp.csv"), index=False)

    if starters_records:
        starters_df = pd.concat(starters_records, ignore_index=True)
        starters_df.to_csv(os.path.join(paths.data_raw, "starters.csv"), index=False)

    print("Done. Saved raw data to data/raw/")

if __name__ == "__main__":
    main()
