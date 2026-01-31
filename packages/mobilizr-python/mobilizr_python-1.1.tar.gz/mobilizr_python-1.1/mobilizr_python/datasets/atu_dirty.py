import os
import pandas as pd

def load():
    """Load the atu_dirty dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'atu_dirty.csv')
    df = pd.read_csv(path)
    return df

def describe():
    """Return a description of the atu_dirty dataset."""
    return 
'''
American Time Use Survey Data Sample - Dirty
Description
A dataset containing a subset of variables from the American Time Use Survey. This dataset is "dirty", meaning it has elements which require formatting before use.

Usage
data(atu_dirty)
Format
A data frame with 10,493 observations of 8 variables

Details
caseid. unique identifier of individual survey participant

V1. the age of the respondent

V2. the gender of the respondent (1: Male, 2: Female)

V3. the employment status of the respondent

V4. does the respondent have a physical difficulty (1: Person did not report having a physical difficulty, 2: Person surveyed reported the have a physical difficulty)

V5. the length of time the person sleeps, in minutes

V6. How long the respondent spent on homework assignments, in minutes

V7. the number of minutes the respondent spent socializing

Source
http://www.bls.gov/tus/
'''.strip()

