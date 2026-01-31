import os
import pandas as pd

def load():
    """Load the slasher dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'slasher.csv')
    df = pd.read_csv(path)
    return df

def describe():
    """Return a description of the slasher dataset."""
    return """
    Survival status of actors and actresses in "Slasher" films
    Description
    A dataset containing survival statuses of actors and actresses in 50 randomly sampled "Slasher" films from 1960 to 2009.

    Usage
    data(slasher)
    Format
    A data frame with 485 observations of 2 variables

    Details
    gender. the gender of actor/actress

    survival. the survival status of the actor/actress


    """.strip()

