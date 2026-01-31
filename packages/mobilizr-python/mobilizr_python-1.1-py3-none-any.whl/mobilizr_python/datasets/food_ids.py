import os
import pandas as pd

def load():
    """Load the food dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'food_ids.csv')
    df = pd.read_csv(path)
    return df