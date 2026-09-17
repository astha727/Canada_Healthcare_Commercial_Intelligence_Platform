import pandas as pd
from pathlib import Path
from src.data.data_loader import load_file

Project_root = Path(__file__).resolve().parents[2]

market_context = Project_root /'Data' / 'synthetic' / 'market_context.csv'
hcp_data = Project_root /'Data' / 'synthetic' / 'synthetic_hcp_segmentation_output.csv'

datasets = {
    'market': market_context,
    'hcp': hcp_data
}

market = load_file(datasets['market'])
hcp = load_file(datasets['hcp'])

print(market.shape)
print(hcp.shape)
