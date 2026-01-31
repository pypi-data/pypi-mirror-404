from . import datasets
import pandas as pd

def data(name):
    """Load a dataset by name."""
    if hasattr(datasets, name):
        return getattr(datasets, name).load()
    else:
        raise ValueError(f"Dataset '{name}' not found in mobilizr_python.datasets")
    
    
def describe(name):
    """Get the description for a dataset by name."""
    if hasattr(datasets, name):
        return getattr(datasets, name).describe()
    else:
        raise ValueError(f"Dataset '{name}' not found in mobilizr_python.datasets")
    
def list_datasets():
    """Return a list of available dataset names."""
    return [name for name in dir(datasets) if not name.startswith("_")]

def View(name):
    """View a dataset by name."""
    if hasattr(datasets, name):
        df = getattr(datasets, name).load()
        if isinstance(df, pd.DataFrame):
            return df
        else:
            raise TypeError(f"Dataset '{name}' is not a pandas DataFrame.")
    else:
        raise ValueError(f"Dataset '{name}' not found in mobilizr_python.datasets")
    
def timeuse_format(df):
    df = df.replace("NOT_DISPLAYED", 0)
    df[df.columns.difference(['user.id', 'timestamp', 'activities'])] = \
        df[df.columns.difference(['user.id', 'timestamp', 'activities'])].apply(pd.to_numeric)

    submissions = df.groupby('user.id').size().rename("submissions")
    
    averages = df.groupby('user.id').mean(numeric_only = True)
    
    return averages.merge(submissions, on = "user.id")


