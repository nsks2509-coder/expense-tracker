import sqlite3
import datetime

class ExpenseTracker:
    def __init__(self, db_name="expenses.db"):
        """Initialize the database connection and create tables if they don't exist."""
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_table()

    def create_table(self):
        """Creates the expenses table."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date TEXT,
                category TEXT,
                amount REAL,
                description TEXT
            )
        ''')
        self.conn.commit()

    def add_expense(self, category, amount, description):
        """Adds a new expense to the database."""
        date = datetime.date.today().strftime("%Y-%m-%d")
        self.cursor.execute('''
            INSERT INTO expenses (date, category, amount, description)
            VALUES (?, ?, ?, ?)
        ''', (date, category, amount, description))
        self.conn.commit()
        print("\n✅ Expense added successfully!")

    def view_expenses(self):
        """Displays all recorded expenses."""
        self.cursor.execute('SELECT * FROM expenses')
        rows = self.cursor.fetchall()
        
        if not rows:
            print("\nNo expenses recorded yet.")
            return
            
        print("\n" + "="*50)
        print("ALL EXPENSES")
        print("="*50)
        for row in rows:
            print(f"ID: {row[0]:<3} | Date: {row[1]} | Category: {row[2]:<12} | Amount: ${row[3]:<8.2f} | Desc: {row[4]}")
        print("="*50)

    def view_summary(self):
        """Generates a summary of expenses grouped by category."""
        self.cursor.execute('SELECT category, SUM(amount) FROM expenses GROUP BY category')
        rows = self.cursor.fetchall()
        
        if not rows:
            print("\nNo expenses to summarize.")
            return
            
        print("\n" + "="*30)
        print("EXPENSE SUMMARY")
        print("="*30)
        total = 0
        for row in rows:
            print(f"{row[0]:<15}: ${row[1]:.2f}")
            total += row[1]
        print("-" * 30)
        print(f"TOTAL SPENT    : ${total:.2f}")
        print("="*30)

    def delete_expense(self, expense_id):
        """Deletes an expense by its ID."""
        self.cursor.execute('DELETE FROM expenses WHERE id = ?', (expense_id,))
        self.conn.commit()
        print(f"\n🗑️ Expense ID {expense_id} deleted.")

    def close(self):
        """Closes the database connection."""
        self.conn.close()

def main():
    tracker = ExpenseTracker()
    
    while True:
        print("\n💰 EXPENSE TRACKER MENU")
        print("1. Add Expense")
        print("2. View All Expenses")
        print("3. View Summary by Category")
        print("4. Delete an Expense")
        print("5. Exit")
        
        choice = input("\nEnter your choice (1-5): ")
        
        if choice == '1':
            category = input("Enter category (e.g., Food, Transport, Utilities): ").strip()
            try:
                amount = float(input("Enter amount: $"))
                description = input("Enter description: ").strip()
                tracker.add_expense(category, amount, description)
            except ValueError:
                print("\n❌ Invalid amount. Please enter a valid number.")
                
        elif choice == '2':
            tracker.view_expenses()
            
        elif choice == '3':
            tracker.view_summary()
            
        elif choice == '4':
            try:
                expense_id = int(input("Enter the ID of the expense to delete: "))
                tracker.delete_expense(expense_id)
            except ValueError:
                print("\n❌ Invalid ID. Please enter a valid number.")
                
        elif choice == '5':
            tracker.close()
            print("\nGoodbye! Have a great day.")
            break
            
        else:
            print("\n❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main()