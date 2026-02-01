import os
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data"

def get_data_path(filename):
    return str(DATA_PATH / filename)

def load_sample_data():
    path = get_data_path("sample_data.csv")
    # print(f"Loading data from {path}...")
    return path

def load_data_energy():
    path = get_data_path("data_energy.csv")
    # print(f"Loading data from {path}...")
    return path