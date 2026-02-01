from ..src import *

class DatabaseConnectionDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Connect to Database")
        self.setModal(True)

        self.db_url = QLineEdit()
        self.db_path = QLineEdit()

        self.db_url.setPlaceholderText(
            "sqlite:///example.db  |  postgresql://user:pass@host/db"
        )
        self.db_path.setPlaceholderText(
            "Optional local DB path (used if dbUrl empty)"
        )

        form = QVBoxLayout()
        form.addWidget(QLabel("Database URL"))
        form.addWidget(self.db_url)
        form.addWidget(QLabel("Database Path"))
        form.addWidget(self.db_path)

        buttons = QHBoxLayout()
        ok = QPushButton("Connect")
        cancel = QPushButton("Cancel")

        ok.clicked.connect(self.accept)
        cancel.clicked.connect(self.reject)

        buttons.addWidget(ok)
        buttons.addWidget(cancel)

        root = QVBoxLayout()
        root.addLayout(form)
        root.addLayout(buttons)

        self.setLayout(root)

    def get_values(self):
        return {
            "dbUrl": self.db_url.text().strip() or None,
            "dbPath": self.db_path.text().strip() or None,
        }
