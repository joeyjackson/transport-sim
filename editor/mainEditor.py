import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory
from FkTableModel import FkTableModel, DisplaySchemaColumn, ForeignKeySpecification, AuxiliaryColumn
from db import ModelTable, VehicleTable, logger
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
        DisplaySchemaColumn(column_name="model.model_id", header="id", default_value=None),
        DisplaySchemaColumn(column_name="model.type_id", header="type", default_value=0),
        DisplaySchemaColumn(column_name="model.label", header="label", default_value=""),
        DisplaySchemaColumn(column_name="model.speed", header="speed", default_value=0.),
      ],
      onError=self.setErrorLabel,
      clearError=self.clearErrorLabel,
    )
    self.vehicleModel = FkTableModel(
      table_name=vehicleTable.table_name(),
      schema=[
        DisplaySchemaColumn(column_name="vehicle.vehicle_id", header="id", default_value=None),
        DisplaySchemaColumn(column_name="vehicle.label", header="label", default_value="--"),
        DisplaySchemaColumn(column_name="model.model_id", header="model", default_value=0,
          fk_options=ForeignKeySpecification(
            reference_table=modelTable.table_name(), 
            join_on="vehicle.model_id = model.model_id", 
            display_columns=["model.label"],
            auxiliary_columns=[
              AuxiliaryColumn(column_name="model.speed", header="speed")
            ]
          )
        ),
      ],
      onError=self.setErrorLabel,
      clearError=self.clearErrorLabel,
    )

    self.modelTableView.setModel(self.modelModel)
    self.vehicleTableView.setModel(self.vehicleModel)
    
    self.fk_column_delegate = FkColumnDelegate()

    self.modelTableView.setItemDelegate(self.fk_column_delegate)
    self.vehicleTableView.setItemDelegate(self.fk_column_delegate)

    self.modelAddBtn.clicked.connect(self.modelModel.appendRow)
    self.vehicleAddBtn.clicked.connect(self.vehicleModel.appendRow)
    self.modelClearBtn.clicked.connect(self.modelModel.reset)
    self.vehicleClearBtn.clicked.connect(self.vehicleModel.reset)
    self.modelSaveBtn.clicked.connect(self.modelModel.save)
    self.vehicleSaveBtn.clicked.connect(self.vehicleModel.save)

    # for r in range(self.vehicleModel.rowCount(None)):
    #   res = self.vehicleTableView.openPersistentEditor(self.vehicleModel.index(r, 2))
    #   res = self.vehicleTableView.openPersistentEditor(self.vehicleModel.index(r, 4))
   
    # self.modelModel.modelReset.connect(
    #   self.modelTableView.resizeColumnsToContents)
    # self.modelModel.data_changed.connect(
    #   self.modelTableView.resizeColumnsToContents)

    # self.modelTableView.resizeColumnsToContents()
    # self.vehicleTableView.resizeColumnsToContents()

  def setErrorLabel(self, e) -> None:
    logger.error(e)
    self.err_label.setText(f"<html><head/><body><p><span style=\"color:#ff0000;\">{e}</span></p></body></html>")
    self.err_label.adjustSize()
  
  def clearErrorLabel(self) -> None:
    self.err_label.setText("")
    self.err_label.adjustSize()

def main():
  QApplication.setStyle(QStyleFactory.create("fusion"))
  app = QApplication(sys.argv)
  main_window = MainWindow()
  main_window.show()
  sys.exit(app.exec_())


if __name__ == '__main__':
  main()