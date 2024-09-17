import sys
import sqlite3
import subprocess
import threading
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, 
                             QWidget, QPushButton, QCheckBox, QMessageBox, QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QIcon

class WorkerSignals(QObject):
    update_message = pyqtSignal(str)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restrategias")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon('logo.jpeg'))

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet(
            "QHeaderView::section { background-color: #A9A9A9; color: white; }"
        )
        self.layout.addWidget(self.table_widget)

        self.procedure_text = QTextEdit()
        self.procedure_text.setReadOnly(True)
        self.layout.addWidget(self.procedure_text)

        self.run_button = QPushButton("Ejecutar Estrategias")
        self.run_button.clicked.connect(self.run_strategies)
        self.layout.addWidget(self.run_button)

        self.conn = sqlite3.connect('Iv3.db')
        self.cursor = self.conn.cursor()

        self.signals = WorkerSignals()
        self.signals.update_message.connect(self.update_procedure_text)

        self.stop_thread = False

        self.load_data()

    def load_data(self):
        try:
            self.cursor.execute("SELECT nombre_estrategia, ruta_estrategia, estatus FROM estrategias")
            rows = self.cursor.fetchall()

            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(4)
            self.table_widget.setHorizontalHeaderLabels(["Nombre Estrategia", "Ruta Estrategia", "Estatus", "Backup"])

            for i, row in enumerate(rows):
                name = row[0]
                path = row[1]
                estatus = row[2]

                self.table_widget.setItem(i, 0, QTableWidgetItem(name))
                self.table_widget.setItem(i, 1, QTableWidgetItem(path))

                estatus_checkbox = QCheckBox()
                estatus_checkbox.setChecked(estatus == 1)
                estatus_checkbox.stateChanged.connect(lambda state, name=name: self.update_status(state, name))
                self.table_widget.setCellWidget(i, 2, estatus_checkbox)

                backup_checkbox = QCheckBox()
                backup_checkbox.setChecked(estatus == 1)
                self.table_widget.setCellWidget(i, 3, backup_checkbox)

        except sqlite3.Error as e:
            self.show_message("Error", f"Error al cargar datos: {e}")

    def update_status(self, state, name):
        status = 1 if state == Qt.CheckState.Checked else 0
        try:
            self.cursor.execute("UPDATE estrategias SET estatus = ? WHERE nombre_estrategia = ?", (status, name))
            self.conn.commit()
        except sqlite3.Error as e:
            self.show_message("Error", f"Error al actualizar estado: {e}")

    def adjust_column_widths(self):
        table_width = self.table_widget.viewport().width()
        column_count = self.table_widget.columnCount()
        if column_count > 0:
            column_width = table_width // column_count
            for i in range(column_count):
                self.table_widget.setColumnWidth(i, column_width)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjust_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.adjust_column_widths()

    def run_strategies(self):
        self.strategies = []
        for row_index in range(self.table_widget.rowCount()):
            backup_checkbox = self.table_widget.cellWidget(row_index, 3)
            if isinstance(backup_checkbox, QCheckBox) and backup_checkbox.isChecked():
                name = self.table_widget.item(row_index, 0).text()
                path = self.table_widget.item(row_index, 1).text()
                self.strategies.append((name, path))

        self.stop_thread = False
        self.thread = threading.Thread(target=self.execute_strategies)
        self.thread.start()

    def execute_strategies(self):
        try:
            for name, path in self.strategies:
                if self.stop_thread:
                    break

                if not os.path.isfile(path):
                    self.signals.update_message.emit(f"Archivo no encontrado: {path}")
                    continue

                self.signals.update_message.emit(f"Ejecutando estrategia: {name}")

                process = subprocess.Popen([path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                for line in iter(process.stdout.readline, ''):
                    self.signals.update_message.emit(line.strip())

                stderr = process.stderr.read()
                if stderr:
                    self.signals.update_message.emit(f"Error al ejecutar: {stderr.strip()}")

                process.stdout.close()
                process.wait()

                if process.returncode != 0:
                    self.signals.update_message.emit(f"Proceso terminó con error: {process.returncode}")

                if self.stop_thread:
                    break
        except Exception as e:
            self.signals.update_message.emit(f"Error al ejecutar estrategias: {e}")

    def update_procedure_text(self, message):
        self.procedure_text.append(message)

    def closeEvent(self, event):
        self.stop_thread = True
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join()

        if hasattr(self, 'conn'):
            self.conn.close()
        super().closeEvent(event)

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
