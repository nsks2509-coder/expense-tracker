import csv
import tempfile
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from main import ExpenseTracker, parse_amount


class ExpenseTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = ExpenseTracker(":memory:")

    def tearDown(self):
        self.tracker.close()

    def test_parse_amount_accepts_two_decimal_places(self):
        self.assertEqual(parse_amount("125.50"), Decimal("125.50"))

    def test_parse_amount_rejects_invalid_values(self):
        for raw in ("", "abc", "0", "-1", "1.234", "NaN", "Infinity"):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    parse_amount(raw)

    def test_add_expense_and_total_are_accurate(self):
        self.tracker.add_expense("Food", "12.30", "Lunch", date(2026, 1, 2))
        self.tracker.add_expense("Food", "0.70", "Tea", date(2026, 1, 3))
        self.assertEqual(self.tracker.total_spent(), Decimal("13.00"))

    def test_summary_groups_categories(self):
        self.tracker.add_expense("Food", "10.00")
        self.tracker.add_expense("Travel", "15.00")
        self.tracker.add_expense("Food", "5.00")
        summary = {row["category"]: Decimal(str(row["total"])) for row in self.tracker.summary_by_category()}
        self.assertEqual(summary, {"Food": Decimal("15"), "Travel": Decimal("15")})

    def test_monthly_summary_filters_month(self):
        self.tracker.add_expense("Food", "10", expense_date=date(2026, 2, 1))
        self.tracker.add_expense("Food", "20", expense_date=date(2026, 3, 1))
        self.assertEqual(self.tracker.monthly_summary(2026, 2), Decimal("10.00"))
        self.assertEqual(self.tracker.monthly_summary(2026, 4), Decimal("0.00"))

    def test_delete_returns_whether_record_existed(self):
        expense_id = self.tracker.add_expense("Food", "10")
        self.assertTrue(self.tracker.delete_expense(expense_id))
        self.assertFalse(self.tracker.delete_expense(expense_id))

    def test_empty_category_is_rejected(self):
        with self.assertRaises(ValueError):
            self.tracker.add_expense("  ", "10")

    def test_csv_export_contains_headers_and_rows(self):
        self.tracker.add_expense("Books", "50.25", "Notebook")
        with tempfile.TemporaryDirectory() as directory:
            output = self.tracker.export_csv(Path(directory) / "export.csv")
            with output.open(encoding="utf-8", newline="") as file:
                rows = list(csv.reader(file))
        self.assertEqual(rows[0], ["ID", "Date", "Category", "Amount", "Description"])
        self.assertEqual(rows[1][2:], ["Books", "50.25", "Notebook"])


if __name__ == "__main__":
    unittest.main()
