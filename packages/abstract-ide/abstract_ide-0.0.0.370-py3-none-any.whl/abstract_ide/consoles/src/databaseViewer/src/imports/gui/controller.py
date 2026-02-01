from .table_model import PandasTableModel
from ..src import *
class DBController:
    def __init__(self, ui, browser):
        self.ui = ui
        self.browser = browser

        self.ui.refresh_btn.clicked.connect(self.load_tables)
        self.ui.tables.itemClicked.connect(self.load_columns)
        self.ui.tables.itemClicked.connect(self.preview_table)

    def load_tables(self):
        self.ui.tables.clear()
        for t in self.browser.list_tables():
            self.ui.tables.addItem(t)

    def load_columns(self, item):
        table = item.text()
        self.ui.columns.clear()
        for col in self.browser.list_columns(table):
            self.ui.columns.addItem(col)

    def preview_table(self, item):
        table = item.text()
        cols = self.browser.list_columns(table)
        if not cols:
            return

        df = self.browser.search_table(
            table,
            cols[0],
            "",
            False
        )

        if df is not None:
            self.ui.table_view.setModel(PandasTableModel(df))
