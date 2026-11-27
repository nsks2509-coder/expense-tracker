# Expense Tracker

A dependency-free Python command-line app for recording expenses in SQLite, reviewing transactions, and comparing spending by category.

## Features

- Add expenses with a date, category, amount, and description
- Review recent entries
- View totals grouped by category
- Delete an entry by its ID
- Validate blank fields, non-positive amounts, and invalid IDs
- Persist data in a local SQLite database

## Requirements

- Python 3.9+
- No third-party packages

## Run

```bash
python main.py
```

Choose an action from the menu. The application creates `expenses.db` in the current working directory on first run.

## Data and limitations

Expense amounts are displayed in USD and stored as SQLite floating-point values. This is a learning project and is intended for local use; it does not include accounts, synchronization, backups, or financial reporting controls. Keep the database file private and make backups if its contents matter.
