import os
import pandas as pd

def load():
    """Load the cdc dataset."""
    path = os.path.join(os.path.dirname(__file__), '..', 'data', 'cdc.csv')
    df = pd.read_csv(path)
    return df

def describe():
    """Return a description of the CDC dataset."""
    return """
    CDC Youth Risk Behavior Survey Data

    **Description**
    A dataset containing responses from the 2021 CDC Youth Risk Behavior Survey.

    **Usage**
    `data(cdc)`

    **Format**
    A data frame with 17,232 observations of 32 variables.

    **Details**
    - **age** — age in years  
    - **sex** — sex assigned at birth  
    - **grade** — grade in school  
    - **height** — height of student in meters  
    - **weight** — weight of student in kilograms  
    - **seat_belt** — how often student wore a seatbelt in a motor vehicle driven by someone else  
    - **drive_text** — how often the student reported texting while driving in the past 30 days  
    - **hisp_latino** — whether or not student identifies as Hispanic or Latino  
    - **american_indian_or_alaska_native** — whether or not student identifies as American Indian or Alaska Native  
    - **asian** — whether or not student identifies as Asian  
    - **black_or_african_american** — whether or not student identifies as Black or African American  
    - **native_hawaiian_or_other_pacific_islander** — whether or not student identifies as Native Hawaiian or other Pacific Islander  
    - **white** — whether or not student identifies as White  
    - **bully_school** — did the student report being bullied at school  
    - **bully_electronic** — did the student report being bullied online  
    - **depressed** — student reported feeling depressed for 2 weeks in a row or more during the past 12 months  
    - **days_smoking** — number of days student reported smoking cigarettes during past 30 days  
    - **days_vaping** — number of days student reported vaping/smoking electronic cigarettes during past 30 days  
    - **sexuality** — how the student describes their sexual orientation  
    - **describe_weight** — student perception of their weight relative to what they believe it should be  
    - **drink_juice** — how often student consumed fruit juice over the previous 7 days  
    - **eat_fruit** — how often student ate fruit over the previous 7 days  
    - **eat_salad** — how often student ate salad over the previous 7 days  
    - **drink_soda** — how often student consumed soda over the previous 7 days  
    - **drink_milk** — how often student drank milk over the previous 7 days  
    - **eat_breakfast** — how often the student reported eating breakfast over the past 7 days  
    - **days_exercise_60** — how often student was active for at least 60 mins over the previous 7 days  
    - **screen_time** — average number of hours spent on a screen on a school day  
    - **number_teams** — number of sports teams played on during previous 12 months  
    - **hours_sleep** — reported hours of sleep on school nights  
    - **drink_sportdrink** — how often student consumed sports drinks over the past 7 days  
    - **drink_water** — how often student consumed water over the past 7 days

    **Source**
    http://www.cdc.gov/HealthyYouth/yrbs/index.htm
        """.strip()

