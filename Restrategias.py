import sys
import sqlite3
import subprocess
from PyQt6.QtWidgets import QApplication, QMainWindow, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget, QPushButton, QCheckBox, QMessageBox, QTextEdit
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Restrategias")
        self.setGeometry(100, 100, 800, 600)  # Ajustar el tamaño de la ventana
        
        # Establecer el icono de la ventana
        self.setWindowIcon(QIcon('logo.jpeg'))  # Reemplaza 'logo.jpeg' con el nombre de tu archivo de imagen

        # Crear el widget central y los layouts
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Crear la tabla
        self.table_widget = QTableWidget()
        self.table_widget.setStyleSheet(
            "QHeaderView::section { background-color: #A9A9A9; color: white; }"
        )  # Cambiar el color del encabezado de la tabla
        self.layout.addWidget(self.table_widget)

        # Crear el área de texto para mostrar el procedimiento
        self.procedure_text = QTextEdit()
        self.procedure_text.setReadOnly(True)
        self.layout.addWidget(self.procedure_text)

        # Crear el botón para ejecutar las estrategias
        self.run_button = QPushButton("Ejecutar Estrategias")
        self.run_button.clicked.connect(self.run_strategies)
        self.layout.addWidget(self.run_button)

        self.load_data()

    def load_data(self):
        try:
            # Conectar a la base de datos
            conn = sqlite3.connect('Iv3.db')
            cursor = conn.cursor()

            # Obtener datos
            cursor.execute("SELECT nombre_estrategia, ruta_estrategia, estatus FROM estrategias")
            rows = cursor.fetchall()

            # Configurar la tabla
            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(3)
            self.table_widget.setHorizontalHeaderLabels(["Nombre Estrategia", "Ruta Estrategia", "Estatus"])

            for i, row in enumerate(rows):
                for j, cell in enumerate(row):
                    if j == 2:  # Columna de estatus
                        checkbox = QCheckBox()
                        checkbox.setChecked(bool(cell))
                        self.table_widget.setCellWidget(i, j, checkbox)
                    else:
                        self.table_widget.setItem(i, j, QTableWidgetItem(str(cell)))

            conn.close()
        except sqlite3.Error as e:
            self.show_message("Error", f"Error al cargar datos: {e}")

    def adjust_column_widths(self):
        # Obtener el ancho total disponible
        table_width = self.table_widget.viewport().width()
        # Calcular el ancho para cada columna
        column_count = self.table_widget.columnCount()
        if column_count > 0:
            column_width = table_width // column_count

            # Aplicar el ancho calculado a cada columna
            for i in range(column_count):
                self.table_widget.setColumnWidth(i, column_width)

    def showEvent(self, event):
        super().showEvent(event)
        # Ajustar el ancho de las columnas cuando el widget se muestra
        self.adjust_column_widths()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        # Ajustar el ancho de las columnas cuando cambia el tamaño de la ventana
        self.adjust_column_widths()

    def run_strategies(self):
        try:
            # Conectar a la base de datos
            conn = sqlite3.connect('Iv3.db')
            cursor = conn.cursor()

            # Obtener las filas de la tabla
            rows = []
            for row_index in range(self.table_widget.rowCount()):
                checkbox = self.table_widget.cellWidget(row_index, 2)
                if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                    name = self.table_widget.item(row_index, 0).text()
                    path = self.table_widget.item(row_index, 1).text()
                    rows.append((name, path))

            # Ejecutar estrategias seleccionadas
            for name, path in rows:
                self.procedure_text.append(f"Ejecutando estrategia: {name}")
                result = subprocess.run([path], shell=True, capture_output=True, text=True)
                self.procedure_text.append(result.stdout)
                if result.stderr:
                    self.procedure_text.append(f"Error al ejecutar: {result.stderr}")

            conn.close()
        except sqlite3.Error as e:
            self.show_message("Error", f"Error al ejecutar estrategias: {e}")

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
