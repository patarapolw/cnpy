from PySide6.QtWidgets import QMainWindow, QApplication, QPushButton

import sys

from cjpy import load_db


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Hello World")

        button = QPushButton("My simple app.")
        button.pressed.connect(self.close)

        self.setCentralWidget(button)
        self.show()


if __name__ == "__main__":
    load_db()

    app = QApplication(sys.argv)
    w = MainWindow()
    app.exec()
