import os
import pandas as pd
from ..config import paths, rapm

SUB_EVENT_TYPES = {8: "SUBSTITUTION"}  # from NBA pbp schema

def load_raw():
    pbp_path = os.path.join(paths.data_raw, "pbp.csv")
    starters_path = os.path.join(paths.data_raw, "starters.csv")
    games_path = os.path.join(paths.data_raw, "games.csv")
    return (
        pd.read_csv(pbp_path, low_memory=False),
        pd.read_csv(starters_path),
        pd.read_csv(games_path)
    )

def initialize_lineups(starters_df):
    # Map GAME_ID -> {TEAM_ID: set(PIDs)}
    starters_df = starters_df.dropna(subset=["PLAYER_ID"])
    starters_df["PLAYER_ID"] = starters_df["PLAYER_ID"].astype(int)
    lineup_map = {}
    for gid, gdf in starters_df.groupby("GAME_ID"):
        by_team = {}
        for tid, tdf in gdf.groupby("TEAM_ID"):
            by_team[int(tid)] = set(map(int, tdf["PLAYER_ID"].tolist()))
        lineup_map[gid] = by_team
    return lineup_map

def iterate_stints(pbp_df, lineup_map):
    stints = []
    for gid, gpbp in pbp_df.groupby("GAME_ID", sort=False):
        gpbp = gpbp.sort_values(["PERIOD", "PCTIMESTRING"]).reset_index(drop=True)

        if gid not in lineup_map or len(lineup_map[gid]) != 2:
            continue
        teams = list(lineup_map[gid].keys())
        on_court = {teams[0]: set(lineup_map[gid][teams[0]]),
                    teams[1]: set(lineup_map[gid][teams[1]])}

        last_index = 0
        start_score_home = start_score_away = None

        def current_score(r):
            # Basic score parsing
            if isinstance(r["SCORE"], str) and "-" in r["SCORE"]:
                a, b = r["SCORE"].split("-")
                return int(a), int(b)
            return None, None

        for idx, row in gpbp.iterrows():
            et = row.get("EVENTMSGTYPE", None)
            if et in SUB_EVENT_TYPES:
                # Close stint at this index - 1
                stint = gpbp.iloc[last_index:idx]
                if not stint.empty:
                    ah, bh = None, None
                    for _, r in stint[::-1].iterrows():
                        ah, bh = current_score(r)
                        if ah is not None:
                            break
                    for _, r in stint.iterrows():
                        sah, sbh = current_score(r)
                        if sah is not None:
                            start_score_home, start_score_away = sah, sbh
                            break

                    if ah is not None and start_score_home is not None:
                        pts_diff = (ah - start_score_home) - (bh - start_score_away)
                        possessions = max(1, int(stint["HOMEDESCRIPTION"].notna().sum() * 0.5
                                                 + stint["VISITORDESCRIPTION"].notna().sum() * 0.5))
                        stints.append({
                            "GAME_ID": gid,
                            "PERIOD": stint["PERIOD"].iloc[0],
                            "start_idx": last_index,
                            "end_idx": idx-1,
                            "teamA": teams[0],
                            "teamB": teams[1],
                            "players_teamA": sorted(list(on_court[teams[0]])),
                            "players_teamB": sorted(list(on_court[teams[1]])),
                            "possessions": possessions,
                            "pts_diff": pts_diff,
                            "pts_per_poss_diff": pts_diff / possessions
                        })
                # Apply substitution
                pid_in = row.get("PLAYER1_ID", None)
                pid_out = row.get("PLAYER2_ID", None)
                team_id = row.get("PLAYER1_TEAM_ID", None)
                if pd.notna(pid_in) and pd.notna(pid_out) and pd.notna(team_id):
                    team_id = int(team_id)
                    on_court[team_id].discard(int(pid_out))
                    on_court[team_id].add(int(pid_in))
                last_index = idx + 1

        # close last stint of game
        stint = gpbp.iloc[last_index:]
        if not stint.empty:
            # similar scoring computation
            end_home = end_away = None
            start_home = start_away = None
            for _, r in stint[::-1].iterrows():
                end_home, end_away = None, None
                if isinstance(r["SCORE"], str) and "-" in r["SCORE"]:
                    a, b = r["SCORE"].split("-")
                    end_home, end_away = int(a), int(b)
                    break
            for _, r in stint.iterrows():
                if isinstance(r["SCORE"], str) and "-" in r["SCORE"]:
                    a, b = r["SCORE"].split("-")
                    start_home, start_away = int(a), int(b)
                    break
            if end_home is not None and start_home is not None:
                pts_diff = (end_home - start_home) - (end_away - start_away)
                possessions = max(1, int(stint["HOMEDESCRIPTION"].notna().sum() * 0.5
                                         + stint["VISITORDESCRIPTION"].notna().sum() * 0.5))
                stints.append({
                    "GAME_ID": gid,
                    "PERIOD": stint["PERIOD"].iloc[0],
                    "start_idx": last_index,
                    "end_idx": stint.index[-1],
                    "teamA": teams[0],
                    "teamB": teams[1],
                    "players_teamA": sorted(list(on_court[teams[0]])),
                    "players_teamB": sorted(list(on_court[teams[1]])),
                    "possessions": possessions,
                    "pts_diff": pts_diff,
                    "pts_per_poss_diff": pts_diff / possessions
                })
    return pd.DataFrame(stints)

def main():
    pbp, starters, _games = load_raw()
    lineup_map = initialize_lineups(starters)
    stints = iterate_stints(pbp, lineup_map)
    # Filter out tiny/noisy stints
    stints = stints[stints["possessions"] >= rapm.min_stint_possessions].reset_index(drop=True)
    os.makedirs(paths.data_interim, exist_ok=True)
    stints.to_parquet(os.path.join(paths.data_interim, "stints.parquet"), index=False)
    print(f"Built {len(stints)} stints → data/interim/stints.parquet")

if __name__ == "__main__":
    main()
