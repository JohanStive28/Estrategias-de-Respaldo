import sys
import sqlite3
import subprocess
import threading
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

        # Conectar a la base de datos
        self.conn = sqlite3.connect('Iv3.db')
        self.cursor = self.conn.cursor()

        # Configurar las señales del trabajador
        self.signals = WorkerSignals()
        self.signals.update_message.connect(self.update_procedure_text)

        # Variable de control para el hilo
        self.stop_thread = False

        # Configuración para la redirección de print a archivo de log
        self.log_file = open("application.log", "w")

        self.load_data()

    def load_data(self):
        try:
            # Obtener datos
            self.cursor.execute("SELECT nombre_estrategia, ruta_estrategia, estatus FROM estrategias")
            rows = self.cursor.fetchall()

            # Configurar la tabla
            self.table_widget.setRowCount(len(rows))
            self.table_widget.setColumnCount(4)
            self.table_widget.setHorizontalHeaderLabels(["Nombre Estrategia", "Ruta Estrategia", "Estatus", "Backup"])

            for i, row in enumerate(rows):
                name = row[0]
                path = row[1]
                estatus = row[2]

                # Columna de Nombre Estrategia
                self.table_widget.setItem(i, 0, QTableWidgetItem(name))
                # Columna de Ruta Estrategia
                self.table_widget.setItem(i, 1, QTableWidgetItem(path))

                # Columna de Estatus (CheckBox)
                estatus_checkbox = QCheckBox()
                estatus_checkbox.setChecked(estatus == 1)  # Establecer estado del CheckBox basado en el valor de estatus
                # Conectar el estado del CheckBox al manejador
                estatus_checkbox.stateChanged.connect(lambda state, name=name: self.update_status(state, name))
                self.table_widget.setCellWidget(i, 2, estatus_checkbox)

                # Columna de Backup (CheckBox)
                backup_checkbox = QCheckBox()
                backup_checkbox.setChecked(estatus == 1)  # Establecer el estado inicial del CheckBox en función del estado
                self.table_widget.setCellWidget(i, 3, backup_checkbox)

        except sqlite3.Error as e:
            self.log_error(f"Error al cargar datos: {e}")

    def update_status(self, state, name):
        status = 1 if state == Qt.CheckState.Checked else 0
        try:
            self.log_debug(f"Nombre de la estrategia: '{name}'")
            self.log_debug(f"Estado a actualizar: {status}")
            query = "UPDATE estrategias SET estatus = ? WHERE nombre_estrategia = ?"
            self.log_debug(f"Ejecutando consulta: {query}")
            self.cursor.execute(query, (status, name))
            self.conn.commit()
            self.log_debug("Estado actualizado correctamente.")
        except sqlite3.Error as e:
            self.log_error(f"Error al actualizar estado: {e}")

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
        # Obtener las filas de la tabla
        self.strategies = []
        for row_index in range(self.table_widget.rowCount()):
            backup_checkbox = self.table_widget.cellWidget(row_index, 3)
            if isinstance(backup_checkbox, QCheckBox) and backup_checkbox.isChecked():
                name = self.table_widget.item(row_index, 0).text()
                path = self.table_widget.item(row_index, 1).text()
                self.strategies.append((name, path))

        # Variable de control para detener el hilo
        self.stop_thread = False

        # Crear y empezar el hilo para realizar el backup y mostrar el progreso en tiempo real
        self.thread = threading.Thread(target=self.execute_strategies)
        self.thread.start()

    def execute_strategies(self):
        try:
            for name, path in self.strategies:
                if self.stop_thread:
                    break

                self.signals.update_message.emit(f"Ejecutando estrategia: {name}")

                process = subprocess.Popen([path], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                
                # Leer salida línea por línea
                for line in iter(process.stdout.readline, ''):
                    self.signals.update_message.emit(line.strip())
                    self.log_debug(line.strip())

                # Esperar a que el proceso termine
                process.stdout.close()
                process.wait()

                # Leer errores, si los hay
                stderr = process.stderr.read()
                if stderr:
                    self.signals.update_message.emit(f"Error al ejecutar: {stderr.strip()}")
                    self.log_error(stderr.strip())

                # Comprobar si se debe detener el hilo
                if self.stop_thread:
                    break
        except Exception as e:
            self.signals.update_message.emit(f"Error al ejecutar estrategias: {e}")
            self.log_error(f"Error al ejecutar estrategias: {e}")

    def update_procedure_text(self, message):
        self.procedure_text.append(message)

    def closeEvent(self, event):
        # Detener el hilo si está en ejecución
        self.stop_thread = True
        if hasattr(self, 'thread') and self.thread.is_alive():
            self.thread.join()
        
        # Cerrar la conexión a la base de datos
        if hasattr(self, 'conn'):
            self.conn.close()
        
        # Cerrar el archivo de log
        if hasattr(self, 'log_file'):
            self.log_file.close()
        
        super().closeEvent(event)

    def show_message(self, title, message):
        msg_box = QMessageBox()
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.exec()
    
    def log_debug(self, message):
        self.log_file.write(f"DEBUG: {message}\n")
        self.log_file.flush()

    def log_error(self, message):
        self.log_file.write(f"ERROR: {message}\n")
        self.log_file.flush()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
