# gsheet_loader

A simple Python package to load Google Sheets into pandas DataFrame.

## Installation

```bash
pip install gsheet-loader
```
## Requirements

- Python >= 3.7
- pandas
- requests

## Usage

### Basic Usage

```python
import pandas as pd
from gsheet_loader import load_sheet

# Load a Google Sheet
url = "google sheet url here"
data = load_sheet(url)
df = pd.read_csv(data)
```

## API Reference

### `load_sheet(sheet_url)`

Load a Google Sheet and return as StringIO (ready for `pd.read_csv`).

**Parameters:**
- `sheet_url` (str): The Google Sheet URL (sharing link or edit link)

**Returns:**
- `StringIO`: StringIO object containing the CSV data

**Raises:**
- `ValueError`: If the URL is not a valid Google Sheets URL
- `requests.RequestException`: If there's an error fetching the sheet

## Note

The Google Sheet must be publicly accessible (set to "Anyone with the link can view") for this package to work.

## Author

Arshad Ziban

## Version

1.0.2