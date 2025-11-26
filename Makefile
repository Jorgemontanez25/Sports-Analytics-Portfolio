.PHONY: setup fetch build train viz app

setup:
	python -m venv .venv && . .venv/bin/activate && pip install -U pip && pip install -r requirements.txt
	mkdir -p data/raw data/interim data/processed models

# Example: current season regular season game range; adjust in src/config.py
fetch:
	python -m src.data.fetch_pbp

build:
	python -m src.features.build_stints

train:
	python -m src.models.rapm

viz:
	python -m src.visualize.leaderboard

app:
	streamlit run app.py
