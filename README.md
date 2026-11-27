# Expense Tracker

A command-line personal expense tracker written in Python using SQLite.

## Features
- Add, list, and delete expenses
- Validate positive amounts with up to two decimal places
- Category-wise summaries and monthly totals
- Export records to CSV
- Persistent SQLite storage (created automatically)

## Requirements
- Python 3.10 or newer
- No third-party packages required

## Run
```bash
python main.py
```

The app creates `expenses.db` in the current directory. The default currency display is INR (₹); the database stores numeric amounts, so use a consistent currency for all entries.

## Test
```bash
python -m unittest discover -s tests -v
```

## Data and backups
The database contains your expense records. Keep `expenses.db` private and back it up regularly. Use the CSV export option to create a portable copy.
