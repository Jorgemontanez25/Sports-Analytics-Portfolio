from dataclasses import dataclass, field
from typing import List
import os

# Minimal config to keep paths & season settings centralized.
@dataclass
class Paths:
    root: str = os.path.dirname(os.path.dirname(__file__))
    data_raw: str = os.path.join(root, "..", "data", "raw")
    data_interim: str = os.path.join(root, "..", "data", "interim")
    data_processed: str = os.path.join(root, "..", "data", "processed")
    models_dir: str = os.path.join(root, "..", "models")

@dataclass
class SeasonConfig:
    # NBA season format for nba_api endpoints (e.g., "2024-25")
    season: str = "2024-25"
    # Game date range (inclusive). Keep short at first for quick runs.
    start_date: str = "2024-10-20"
    end_date: str = "2024-11-10"
    # Limit number of games for a fast first run
    max_games: int = 20

@dataclass
class RAPMConfig:
    alpha: float = 200.0  # Ridge strength; tweak after inspecting variance
    min_stint_possessions: int = 4  # filter noisy stints
    response_metric: str = "pts_per_poss_diff"  # or "net_rating"

paths = Paths()
season = SeasonConfig()
rapm = RAPMConfig()
