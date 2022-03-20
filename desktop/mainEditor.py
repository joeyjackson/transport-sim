import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
from FkTableModel import FkTableModel, DisplaySchemaColumn, ForeignKeySpecification, AdditionalColumn
from db import ModelTable, VehicleTable
from FkColumnDelegate import FkColumnDelegate

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

Ui_Interface, _ = uic.loadUiType('mainEditor.ui')

class MainWindow(QMainWindow, Ui_Interface):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)

    modelTable = ModelTable()
    vehicleTable = VehicleTable()

    self.modelModel = FkTableModel(
      table_name=modelTable.table_name(),
      schema=[
        DisplaySchemaColumn(column_name="model.model_id", header="id"),
        DisplaySchemaColumn(column_name="model.type_id", header="type"),
        DisplaySchemaColumn(column_name="model.speed", header="speed"),
      ]
    )
    self.vehicleModel = FkTableModel(
      table_name=vehicleTable.table_name(),
      schema=[
        DisplaySchemaColumn(column_name="vehicle.vehicle_id", header="id"),
        DisplaySchemaColumn(column_name="vehicle.label", header="label"),
        DisplaySchemaColumn(column_name="model.model_id", header="model", fk_options=ForeignKeySpecification(
          reference_table=modelTable.table_name(), 
          join_on="vehicle.model_id = model.model_id", 
          display_columns=["model.label"],
          additional_columns=[
            AdditionalColumn(column_name="model.speed", header="speed")
          ]
        )),
      ]
    )

    self.modelTableView.setModel(self.modelModel)
    self.vehicleTableView.setModel(self.vehicleModel)
    
    fk_column_delegate = FkColumnDelegate()

    self.modelTableView.setItemDelegate(fk_column_delegate)
    self.vehicleTableView.setItemDelegate(fk_column_delegate)

    # self.modelAddBtn.clicked.connect(
    #   lambda _: self.modelModel.appendRow([]))
    self.modelClearBtn.clicked.connect(
      self.modelModel.reset)
    self.modelSaveBtn.clicked.connect(
      self.modelModel.save)
    self.modelModel.modelReset.connect(
      self.modelTableView.resizeColumnsToContents)
    self.modelModel.data_changed.connect(
      self.modelTableView.resizeColumnsToContents)

    # self.modelTableView.resizeColumnsToContents()
    # self.vehicleTableView.resizeColumnsToContents()

def main():
  QApplication.setStyle(QStyleFactory.create("fusion"))
  app = QApplication(sys.argv)
  main_window = MainWindow()
  main_window.show()
  sys.exit(app.exec_())


if __name__ == '__main__':
  main()