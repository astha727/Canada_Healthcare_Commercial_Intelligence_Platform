import pandas as pd
from pathlib import Path

Project_root = Path(__file__).resolve().parents[2]

def load_file(file_path):
    if file_path.exists():
        if file_path.suffix == '.csv':
            df = pd.read_csv(file_path)
            print("Data Loaded")
        elif file_path.suffix == '.xlsx':
            df = pd.read_excel(file_path)
            print("Data Loaded")
    else:
        raise FileNotFoundError(f"{file_path} does not exist")


    return df
