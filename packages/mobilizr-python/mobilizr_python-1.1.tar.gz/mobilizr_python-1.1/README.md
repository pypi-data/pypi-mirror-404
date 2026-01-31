# UCLA IDS Data Library

A lightweight Python library for loading example datasets used in data science courses.

---

## Installation

Clone the repository and install locally:
git clone "https://github.com/EmilioD19/mobilizr-python"
cd "your-repo-directory"
pip install .

## Usage
Import functions:
import mobilizr_python as ids

## Load a dataset
df = load("iris")
print(df.head())

## Describe a dataset
print(describe("iris"))

## List available datasets
print(list_datasets())

## Error Handling
If a dataset does not exist, ValueError is raised:
load("nonexistent")