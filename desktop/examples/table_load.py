import sqlite3
from PyQt5 import QtWidgets, QtCore, uic
import sys
import os

QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QtWidgets.QApplication.setAttribute(QtCore.Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

Ui_Interface, _ = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'tableLoad.ui'))

class MainWindow(QtWidgets.QMainWindow, Ui_Interface):
  def handleLoadData(self):
    connection = sqlite3.connect(os.path.join(os.path.dirname(__file__), '..', 'transportation.db'))
    try:
      query = """
      SELECT v.*, m.label AS model, m.speed 
      FROM vehicle v 
      JOIN model m ON m.model_id = v.model_id;
      """
      result = connection.execute(query)
      self.tableWidget.setRowCount(0)
      
      self.tableWidget.setColumnCount(len(result.description))
      self.tableWidget.setHorizontalHeaderLabels([x[0] for x in result.description])
      
      for r, rdata in enumerate(result):
        self.tableWidget.insertRow(r)
        for c, cdata in enumerate(rdata):
          self.tableWidget.setItem(r, c, QtWidgets.QTableWidgetItem(str(cdata)))

      self.tableWidget.resizeColumnsToContents()
      self.err_label.setText("")
      self.err_label.adjustSize()
    except Exception as e:
      print(e)
      errStr = str(e)
      _translate = QtCore.QCoreApplication.translate
      self.err_label.setText(_translate("MainWindow", f"<html><head/><body><p><span style=\" color:#ff0000;\">{errStr}</span></p></body></html>"))
      self.err_label.adjustSize()
    finally:
      connection.close()

  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)
    self.btn_load.clicked.connect(self.handleLoadData)


def main():
  app = QtWidgets.QApplication(sys.argv)
  main_window = MainWindow()
  main_window.show()
  sys.exit(app.exec_())


if __name__ == '__main__':
  main()