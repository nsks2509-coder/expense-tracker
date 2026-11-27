import datetime
import math
import sqlite3


class ExpenseTracker:
    """Small command-line expense tracker backed by SQLite."""

    def __init__(self, db_name="expenses.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT NOT NULL,
                category TEXT NOT NULL,
                amount REAL NOT NULL CHECK (amount > 0),
                description TEXT NOT NULL
            )
            """
        )
        self.conn.commit()

    def add_expense(self, category, amount, description):
        category = category.strip()
        description = description.strip()
        if not category:
            raise ValueError("Category cannot be empty.")
        if not math.isfinite(amount) or amount <= 0:
            raise ValueError("Amount must be a positive number.")
        if not description:
            raise ValueError("Description cannot be empty.")

        expense_date = datetime.date.today().isoformat()
        self.cursor.execute(
            """
            INSERT INTO expenses (date, category, amount, description)
            VALUES (?, ?, ?, ?)
            """,
            (expense_date, category, amount, description),
        )
        self.conn.commit()
        print("\n✅ Expense added successfully.")

    def view_expenses(self):
        self.cursor.execute(
            "SELECT id, date, category, amount, description "
            "FROM expenses ORDER BY date DESC, id DESC"
        )
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo expenses recorded yet.")
            return

        print("\n" + "=" * 72)
        print("ALL EXPENSES")
        print("=" * 72)
        for expense_id, expense_date, category, amount, description in rows:
            print(
                f"ID: {expense_id:<4} | Date: {expense_date} | "
                f"Category: {category:<14} | Amount: ${amount:>9.2f} | "
                f"Description: {description}"
            )
        print("=" * 72)

    def view_summary(self):
        self.cursor.execute(
            "SELECT category, SUM(amount) FROM expenses "
            "GROUP BY category ORDER BY category COLLATE NOCASE"
        )
        rows = self.cursor.fetchall()
        if not rows:
            print("\nNo expenses to summarize.")
            return

        total = sum(amount for _, amount in rows)
        print("\n" + "=" * 36)
        print("EXPENSE SUMMARY")
        print("=" * 36)
        for category, amount in rows:
            print(f"{category:<20} ${amount:>12.2f}")
        print("-" * 36)
        print(f"{'TOTAL SPENT':<20} ${total:>12.2f}")
        print("=" * 36)

    def delete_expense(self, expense_id):
        self.cursor.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
        self.conn.commit()
        if self.cursor.rowcount:
            print(f"\n🗑️ Expense {expense_id} deleted.")
            return True
        print(f"\nNo expense found with ID {expense_id}.")
        return False

    def close(self):
        self.conn.close()


def main():
    tracker = ExpenseTracker()
    try:
        while True:
            print("\n💰 EXPENSE TRACKER")
            print("1. Add expense")
            print("2. View all expenses")
            print("3. View summary by category")
            print("4. Delete an expense")
            print("5. Exit")

            choice = input("\nChoose an option (1-5): ").strip()
            if choice == "1":
                try:
                    category = input("Category: ")
                    amount = float(input("Amount: $"))
                    description = input("Description: ")
                    tracker.add_expense(category, amount, description)
                except ValueError as error:
                    print(f"\n❌ {error}")
            elif choice == "2":
                tracker.view_expenses()
            elif choice == "3":
                tracker.view_summary()
            elif choice == "4":
                try:
                    expense_id = int(input("Expense ID to delete: "))
                    if expense_id <= 0:
                        raise ValueError("Enter a positive expense ID.")
                    tracker.delete_expense(expense_id)
                except ValueError as error:
                    print(f"\n❌ {error}")
            elif choice == "5":
                print("\nGoodbye.")
                break
            else:
                print("\n❌ Choose a number from 1 to 5.")
    except (EOFError, KeyboardInterrupt):
        print("\n\nClosing expense tracker.")
    finally:
        tracker.close()


if __name__ == "__main__":
    main()
