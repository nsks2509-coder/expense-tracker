import os
import tempfile
import unittest

from main import ExpenseTracker


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        database_path = os.path.join(self.temp_dir.name, "test-expenses.db")
        self.tracker = ExpenseTracker(database_path)

    def tearDown(self):
        self.tracker.close()
        self.temp_dir.cleanup()

    def test_add_expense_persists_normalized_fields(self):
        self.tracker.add_expense("  Food  ", 12.5, "  Lunch  ")

        row = self.tracker.cursor.execute(
            "SELECT category, amount, description FROM expenses"
        ).fetchone()
        self.assertEqual(row, ("Food", 12.5, "Lunch"))

    def test_rejects_empty_text_fields(self):
        for category, description in [("", "Lunch"), ("Food", "  ")]:
            with self.subTest(category=category, description=description):
                with self.assertRaises(ValueError):
                    self.tracker.add_expense(category, 5.0, description)

    def test_rejects_non_positive_or_non_finite_amounts(self):
        for amount in [0, -1, float("nan"), float("inf")]:
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    self.tracker.add_expense("Food", amount, "Lunch")

    def test_delete_reports_whether_an_expense_existed(self):
        self.tracker.add_expense("Food", 5.0, "Snack")
        expense_id = self.tracker.cursor.execute(
            "SELECT id FROM expenses"
        ).fetchone()[0]

        self.assertTrue(self.tracker.delete_expense(expense_id))
        self.assertFalse(self.tracker.delete_expense(expense_id))


if __name__ == "__main__":
    unittest.main()
