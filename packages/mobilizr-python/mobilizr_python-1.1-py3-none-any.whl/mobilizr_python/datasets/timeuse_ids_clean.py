import os
import pandas as pd

def load():
    """Load the timeuse_ids_clean dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'timeuse_ids_clean.csv')
    df = pd.read_csv(path)
    return df