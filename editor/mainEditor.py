import sys
from PyQt5 import uic
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QStyleFactory, QGridLayout, QPushButton, QTableView, QWidget, QHeaderView
from FkTableModel import FkTableModel, DisplaySchemaColumn, ForeignKeySpecification, AuxiliaryColumn
from db import ModelTable, VehicleTable, HubTable, PathTable, MovementTable, logger
from FkColumnDelegate import FkColumnDelegate

QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)  # enable highdpi scaling
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)  # use highdpi icons

Ui_Interface, _ = uic.loadUiType('mainEditor.ui')

class MainWindow(QMainWindow, Ui_Interface):
  def __init__(self, parent=None):
    super().__init__(parent)
    self.setupUi(self)

    self.models = [
      FkTableModel(
        table_name=ModelTable().table_name(),
        schema=[
          DisplaySchemaColumn(column_name="model.model_id", header="id", default_value=None),
          DisplaySchemaColumn(column_name="model.type_id", header="type", default_value=0),
          DisplaySchemaColumn(column_name="model.label", header="label", default_value=""),
          DisplaySchemaColumn(column_name="model.speed", header="speed", default_value=0.),
        ],
        onError=self.setErrorLabel,
        clearError=self.clearErrorLabel,
      ),
      FkTableModel(
        table_name=VehicleTable().table_name(),
        schema=[
          DisplaySchemaColumn(column_name="vehicle.vehicle_id", header="id", default_value=None),
          DisplaySchemaColumn(column_name="vehicle.label", header="label", default_value="--"),
          DisplaySchemaColumn(column_name="vehicle.model_id", header="model", default_value=0,
            fk_options=ForeignKeySpecification(
              reference_table="model", 
              join_on="vehicle.model_id = model.model_id", 
              foreign_column_name="model.model_id",
              display_columns=["model.label"],
              auxiliary_columns=[
                AuxiliaryColumn(column_name="model.speed", header="speed")
              ]
            )
          ),
        ],
        onError=self.setErrorLabel,
        clearError=self.clearErrorLabel,
      ),
      FkTableModel(
        table_name=HubTable().table_name(),
        schema=[
          DisplaySchemaColumn(column_name="hub.hub_id", header="id", default_value=None),
          DisplaySchemaColumn(column_name="hub.label", header="label", default_value=""),
          DisplaySchemaColumn(column_name="hub.posX", header="X", default_value=0.),
          DisplaySchemaColumn(column_name="hub.posY", header="Y", default_value=0.),
        ],
        onError=self.setErrorLabel,
        clearError=self.clearErrorLabel,
      ),
      FkTableModel(
        table_name=PathTable().table_name(),
        schema=[
          DisplaySchemaColumn(column_name="path.path_id", header="id", default_value=None),
          DisplaySchemaColumn(column_name="path.start_hub_id", header="start", default_value=0,
            fk_options=ForeignKeySpecification(
              reference_table="hub AS s_hub", 
              join_on="path.start_hub_id = s_hub.hub_id", 
              foreign_column_name="s_hub.hub_id",
              display_columns=["s_hub.label"]
            )
          ),
          DisplaySchemaColumn(column_name="path.end_hub_id", header="end", default_value=0,
            fk_options=ForeignKeySpecification(
              reference_table="hub AS e_hub", 
              join_on="path.end_hub_id = e_hub.hub_id", 
              foreign_column_name="e_hub.hub_id",
              display_columns=["e_hub.label"]
            )
          ),
        ],
        onError=self.setErrorLabel,
        clearError=self.clearErrorLabel,
      ),
      FkTableModel(
        table_name=MovementTable().table_name(),
        schema=[
          DisplaySchemaColumn(column_name="movement.movement_id", header="id", default_value=None),
          DisplaySchemaColumn(column_name="movement.timestamp", header="timestamp", default_value=0),
          DisplaySchemaColumn(column_name="movement.vehicle_id", header="vehicle", default_value=0,
            fk_options=ForeignKeySpecification(
              reference_table="vehicle", 
              join_on="movement.vehicle_id = vehicle.vehicle_id", 
              foreign_column_name="vehicle.vehicle_id",
              display_columns=["vehicle.label"]
            )
          ),
          DisplaySchemaColumn(column_name="movement.path_id", header="path", default_value=0,
            fk_options=ForeignKeySpecification(
              reference_table="path", 
              join_on="movement.path_id = path.path_id",
              additional_joins=["LEFT JOIN hub s_hub ON path.start_hub_id = s_hub.hub_id", "LEFT JOIN hub e_hub ON path.end_hub_id = e_hub.hub_id"], 
              foreign_column_name="path.path_id",
              display_columns=["s_hub.label", "e_hub.label"],
              display_format="{0} -> {1}"
            )
          ),
        ],
        onError=self.setErrorLabel,
        clearError=self.clearErrorLabel,
      )
    ]

    self.fk_column_delegate = FkColumnDelegate()

    for model in self.models:
      tab = QWidget()
      layout = QGridLayout()
      tab.setLayout(layout)
      clearBtn = QPushButton("Clear and Refresh", tab)
      clearBtn.clicked.connect(model.reset)
      layout.addWidget(clearBtn, 1, 0)

      saveBtn = QPushButton("Save Changes", tab)
      saveBtn.clicked.connect(model.save)
      layout.addWidget(saveBtn, 1, 1)

      addBtn = QPushButton("Add Row", tab)
      addBtn.clicked.connect(model.appendRow)
      layout.addWidget(addBtn, 1, 2)

      view = QTableView(tab)
      view.setModel(model)
      view.setItemDelegate(self.fk_column_delegate)
      view.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
      layout.addWidget(view, 0, 0, 1, 3)
    
      self.tabWidget.addTab(tab, model.table_name)

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