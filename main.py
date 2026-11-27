"""A small, persistent command-line expense tracker.

Amounts are validated and rounded to two decimal places before storage.
The database is created automatically when the application first runs.
"""

from __future__ import annotations

import csv
import sqlite3
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Iterable

CENT = Decimal("0.01")
MAX_AMOUNT = Decimal("1000000000.00")


def parse_amount(raw: str) -> Decimal:
    """Parse a positive monetary amount with at most two decimal places."""
    try:
        amount = Decimal(raw.strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Enter a valid number, for example 125.50.") from None

    if not amount.is_finite():
        raise ValueError("Amount must be a finite number.")
    if amount <= 0:
        raise ValueError("Amount must be greater than zero.")
    if amount > MAX_AMOUNT:
        raise ValueError(f"Amount cannot exceed {MAX_AMOUNT}.")
    if amount != amount.quantize(CENT, rounding=ROUND_HALF_UP):
        raise ValueError("Amount can have at most two decimal places.")
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


class ExpenseTracker:
    """SQLite-backed expense tracker."""

    def __init__(self, db_name: str | Path = "expenses.db") -> None:
        self.db_name = str(db_name)
        if self.db_name != ":memory:":
            Path(self.db_name).expanduser().resolve().parent.mkdir(
                parents=True, exist_ok=True
            )
        self.conn = sqlite3.connect(self.db_name)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.create_table()

    def create_table(self) -> None:
        """Create the expenses table and indexes when they do not exist."""
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount NUMERIC NOT NULL CHECK (amount > 0),
                description TEXT NOT NULL DEFAULT ''
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_date ON expenses(date DESC)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_expenses_category ON expenses(category)"
        )
        self.conn.commit()

    def add_expense(
        self,
        category: str,
        amount: Decimal | str | int | float,
        description: str = "",
        expense_date: date | None = None,
    ) -> int:
        """Add an expense and return its new ID."""
        clean_category = category.strip() if isinstance(category, str) else ""
        clean_description = description.strip() if isinstance(description, str) else ""
        if not clean_category:
            raise ValueError("Category cannot be empty.")
        if len(clean_category) > 60:
            raise ValueError("Category cannot exceed 60 characters.")
        if len(clean_description) > 500:
            raise ValueError("Description cannot exceed 500 characters.")

        clean_amount = parse_amount(str(amount))
        recorded_date = (expense_date or date.today()).isoformat()
        cursor = self.conn.execute(
            """
            INSERT INTO expenses (date, category, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (recorded_date, clean_category, str(clean_amount), clean_description),
        )
        self.conn.commit()
        return int(cursor.lastrowid)

    def fetch_expenses(self) -> list[sqlite3.Row]:
        """Return expenses newest first."""
        cursor = self.conn.execute(
            "SELECT id, date, category, amount, description "
            "FROM expenses ORDER BY date DESC, id DESC"
        )
        return list(cursor.fetchall())

    def summary_by_category(self) -> list[sqlite3.Row]:
        """Return totals grouped by category."""
        cursor = self.conn.execute(
            """
            SELECT category, ROUND(SUM(amount), 2) AS total, COUNT(*) AS count
            FROM expenses
            GROUP BY category
            ORDER BY total DESC, category COLLATE NOCASE
            """
        )
        return list(cursor.fetchall())

    def monthly_summary(self, year: int, month: int) -> Decimal:
        """Return the total spent in a month."""
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")
        cursor = self.conn.execute(
            """
            SELECT COALESCE(ROUND(SUM(amount), 2), 0)
            FROM expenses
            WHERE substr(date, 1, 7) = ?
            """,
            (f"{year:04d}-{month:02d}",),
        )
        return Decimal(str(cursor.fetchone()[0])).quantize(CENT)

    def total_spent(self) -> Decimal:
        """Return the total amount spent across all records."""
        cursor = self.conn.execute(
            "SELECT COALESCE(ROUND(SUM(amount), 2), 0) FROM expenses"
        )
        return Decimal(str(cursor.fetchone()[0])).quantize(CENT)

    def delete_expense(self, expense_id: int) -> bool:
        """Delete an expense; return False when the ID does not exist."""
        if not isinstance(expense_id, int) or expense_id <= 0:
            raise ValueError("Expense ID must be a positive integer.")
        cursor = self.conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    def export_csv(self, file_path: str | Path = "expenses_export.csv") -> Path:
        """Export all expenses to CSV and return the output path."""
        output = Path(file_path).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        rows = self.fetch_expenses()
        with output.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(("ID", "Date", "Category", "Amount", "Description"))
            for row in rows:
                writer.writerow(
                    (row["id"], row["date"], row["category"], row["amount"], row["description"])
                )
        return output

    def close(self) -> None:
        self.conn.close()

    def __enter__(self) -> "ExpenseTracker":
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()


def _prompt_amount() -> Decimal:
    while True:
        try:
            return parse_amount(input("Amount (₹): "))
        except ValueError as error:
            print(f"Invalid amount: {error}")


def _print_expenses(rows: Iterable[sqlite3.Row]) -> None:
    records = list(rows)
    if not records:
        print("\nNo expenses recorded yet.")
        return

    print("\n" + "=" * 88)
    print(f"{'ID':<6} {'DATE':<12} {'CATEGORY':<18} {'AMOUNT (₹)':>14}  DESCRIPTION")
    print("-" * 88)
    for row in records:
        print(
            f"{row['id']:<6} {row['date']:<12} {row['category'][:17]:<18} "
            f"{Decimal(str(row['amount'])):>14.2f}  {row['description']}"
        )
    print("=" * 88)


def main(db_name: str | Path = "expenses.db") -> None:
    """Run the interactive menu."""
    with ExpenseTracker(db_name) as tracker:
        while True:
            print(
                "\n💰 EXPENSE TRACKER"
                "\n1. Add expense"
                "\n2. View all expenses"
                "\n3. Category summary"
                "\n4. Monthly summary"
                "\n5. Delete expense"
                "\n6. Export to CSV"
                "\n7. Exit"
            )
            choice = input("Choose (1-7): ").strip()

            if choice == "1":
                category = input("Category: ").strip()
                amount = _prompt_amount()
                description = input("Description (optional): ").strip()
                try:
                    expense_id = tracker.add_expense(category, amount, description)
                    print(f"Expense #{expense_id} added successfully.")
                except ValueError as error:
                    print(f"Could not add expense: {error}")
            elif choice == "2":
                _print_expenses(tracker.fetch_expenses())
                print(f"Total spent: ₹{tracker.total_spent():.2f}")
            elif choice == "3":
                summaries = tracker.summary_by_category()
                if not summaries:
                    print("No expenses to summarize.")
                else:
                    print("\nCATEGORY SUMMARY")
                    for row in summaries:
                        print(f"{row['category']:<20} ₹{Decimal(str(row['total'])):.2f} ({row['count']} entries)")
                    print(f"TOTAL: ₹{tracker.total_spent():.2f}")
            elif choice == "4":
                try:
                    year = int(input("Year (YYYY): "))
                    month = int(input("Month (1-12): "))
                    print(f"Total for {year:04d}-{month:02d}: ₹{tracker.monthly_summary(year, month):.2f}")
                except ValueError as error:
                    print(f"Invalid year/month: {error}")
            elif choice == "5":
                try:
                    expense_id = int(input("Expense ID to delete: "))
                    if tracker.delete_expense(expense_id):
                        print(f"Expense #{expense_id} deleted.")
                    else:
                        print(f"Expense #{expense_id} was not found.")
                except ValueError as error:
                    print(f"Invalid ID: {error}")
            elif choice == "6":
                destination = input("CSV path (default expenses_export.csv): ").strip()
                try:
                    output = tracker.export_csv(destination or "expenses_export.csv")
                    print(f"Exported {len(tracker.fetch_expenses())} expense(s) to {output}.")
                except OSError as error:
                    print(f"Could not export CSV: {error}")
            elif choice == "7":
                print("Goodbye. Keep tracking your spending!")
                break
            else:
                print("Invalid choice. Enter a number from 1 to 7.")


if __name__ == "__main__":
    main()
