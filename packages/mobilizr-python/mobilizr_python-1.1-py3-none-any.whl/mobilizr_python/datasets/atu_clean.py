import os
import pandas as pd

def load():
    """Load the atu_clean dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'atu_clean.csv')
    df = pd.read_csv(path)
    return df

def describe():
    """Return a description of the atu_clean dataset."""
    return '''
American Time Use Survey Data Sample - Clean
Description
A dataset containing a subset of variables from the American Time Use Survey. This dataset is a cleaned version of atu_dirty.

Usage
data(atu_clean)
Format
A data frame with 10,493 observations of 8 variables

Details
caseid. unique identifier of individual survey participant

age. the age of the respondent

sex. the sex of the respondent

fulltime_emp. the employment status of the respondent

phys_challenge. does the respondent have a physical difficulty

sleep. the length of time the person sleeps, in minutes

homework. How long the respondent spent on homework assignments, in minutes

socializing. the number of minutes the respondent spent socializing

Source
http://www.bls.gov/tus/
'''
