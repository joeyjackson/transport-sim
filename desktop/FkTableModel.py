from PyQt5.QtCore import (
  Qt, 
  QAbstractTableModel, 
  QVariant, 
  QModelIndex,
  pyqtSignal,
)
from PyQt5.QtGui import QBrush, QColor
from typing import List, Optional, Union
from collections import namedtuple
from db import query

AdditionalColumn = namedtuple("AdditionalColumn", ["column_name", "header"])

class ForeignKeySpecification:
  def __init__(
    self, 
    reference_table: str, 
    join_on: str, 
    display_columns: List[str],
    display_format: str = "{0}",
    additional_columns: List[AdditionalColumn] = []
  ) -> None:
    self.reference_table = reference_table
    self.join_on = join_on
    self.display_columns = display_columns
    self.display_format = display_format
    self.additional_columns = additional_columns


class FkTableModelColumn:
  def __init__(self, id_value: int, schema: ForeignKeySpecification):
    self.id_value = id_value
    self.schema = schema


class DisplaySchemaColumn:
  def __init__(self, column_name: str, header: str, fk_options: Optional[ForeignKeySpecification] = None) -> None:
    self.column_name = column_name
    self.header = header
    self.fk_options = fk_options

  def is_fk(self) -> bool:
    return self.fk_options is not None
    

class FkTableModel(QAbstractTableModel):
  data_changed = pyqtSignal(QModelIndex, QModelIndex, Qt.ItemDataRole)

  def __init__(self, table_name: str, schema: List[DisplaySchemaColumn], parent=None, *args):
    QAbstractTableModel.__init__(self, parent, *args)
    self.table_name = table_name
    self._schema = schema
    self._query_rows = []
    self._joins = set()
    self._query_rows_to_schema = []
    for i, col in enumerate(schema):
      self._query_rows.append(col.column_name)
      self._query_rows_to_schema.append(i)
      if col.is_fk():
        self._joins.add(f"JOIN {col.fk_options.reference_table} ON {col.fk_options.join_on}")
        for display_column in col.fk_options.display_columns:
          self._query_rows.append(display_column)
          self._query_rows_to_schema.append(i)
        for additional_column in col.fk_options.additional_columns:
          self._query_rows.append(additional_column.column_name)
          self._query_rows_to_schema.append(i)
          
    self._uneditable_columns = set()
    self._uneditable_columns.add(0)
    self._displayed_columns_to_schema = [] # [(schema_index, schema_additional_column_index), ...]

    for i, col in enumerate(schema):
      self._displayed_columns_to_schema.append((i, None))
      if col.is_fk() and len(col.fk_options.additional_columns) > 0:
        for a in range(len(col.fk_options.additional_columns)):
          self._displayed_columns_to_schema.append((i, a))
          self._uneditable_columns.add(len(self._displayed_columns_to_schema) - 1)

    self._query_results = []

    self._make_query()
    # self._resetChanged()

  def _make_query(self):
    self.beginResetModel()
    self._query_results = []
    for row in query(f"""SELECT {", ".join(self._query_rows)} FROM {self.table_name}{"".join([" " + j for j in self._joins])};"""):
      row_result = []

      curr_schema_col = 0
      col_results = []
      for i, column in enumerate(row):
        schema_column_index = self._query_rows_to_schema[i]
        if curr_schema_col == schema_column_index:
          col_results.append(column)
        else:
          row_result.append(col_results)
          curr_schema_col += 1
          col_results = [column]
      row_result.append(col_results)
      self._query_results.append(row_result)
    self.endResetModel()

  # def _resetChanged(self, value=False):
  #   self._changed = [[value for _ in row] for row in self._data]

  def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
    if orientation == Qt.Horizontal and role == Qt.DisplayRole:
      schema_column_index, schema_additional_column_index = self._displayed_columns_to_schema[section]
      schema_column = self._schema[schema_column_index]
      if schema_additional_column_index is None:
        return QVariant(schema_column.header)
      else:
        return QVariant(schema_column.fk_options.additional_columns[schema_additional_column_index].header)
    return super().headerData(section, orientation, role)

  def update(self, r: int, c: int, value: Union[str, int, float]):
    # old = None
    # if r < len(self._last_snapshot) and c < len(self._last_snapshot[0]):
    #   old = self._last_snapshot[r][c]
    
    # TODO
    schema_column_index, addtional_columns_index = self._displayed_columns_to_schema[c]
    if isinstance(value, list):
      self._query_results[r][schema_column_index] = value
    else:
      self._query_results[r][schema_column_index][0] = value
    
    # self._changed[r][c] = old is None or old != value

  def setData(self, index: QModelIndex, value: Union[str, int, float], role: Qt.ItemDataRole):
    if role == Qt.EditRole:
      self.update(index.row(), index.column(), value)
      self.data_changed.emit(index, index, role)
      return True

  def rowCount(self, parent) -> int:
    return len(self._query_results)

  def columnCount(self, parent) -> int:
    if len(self._query_results):
      return len(self._displayed_columns_to_schema)
    return 0

  def reset(self) -> None:
    self.beginResetModel()
    # self._data = deepcopy(self._last_snapshot)
    # self._resetChanged()
    self.endResetModel()

  def save(self) -> None:
    self.beginResetModel()
    # self._last_snapshot = deepcopy(self._data)
    # self._resetChanged()
    self.endResetModel()

  def appendRow(self, row) -> None:
    rc = len(self._data)
    self.beginInsertRows(QModelIndex(), rc, rc)
    self._data.append(row)
    # self._changed.append([True for _ in row])
    self.endInsertRows()

  def data(self, index, role) -> QVariant:
    if not index.isValid():
      return QVariant()
    if role == Qt.DisplayRole or role == Qt.EditRole:
      schema_column_index, additional_column_index = self._displayed_columns_to_schema[index.column()]
      raw_data = self._query_results[index.row()][schema_column_index]

      schema_column = self._schema[schema_column_index]
      if not schema_column.is_fk():
        return QVariant(raw_data[0])
      else:
        if additional_column_index is not None:
          return QVariant(raw_data[1 + len(schema_column.fk_options.display_columns) + additional_column_index])
        else:
          if role == Qt.DisplayRole:
            display_columns_data = raw_data[1 : len(schema_column.fk_options.display_columns) + 1]
            formatted = schema_column.fk_options.display_format.format(*display_columns_data)
            return QVariant(formatted)
          elif role == Qt.EditRole:
            return QVariant(FkTableModelColumn(raw_data[0], schema_column))

    if role == Qt.BackgroundRole:
      if index.column() in self._uneditable_columns:
        return QVariant(QBrush(QColor(230, 230, 230)))
      # if self._changed[index.row()][index.column()]:
      #   return QVariant(QBrush(QColor(223, 255, 0)))
      # return QVariant()
    return QVariant()

  def flags(self, index):
    if index.column() in self._uneditable_columns:
      return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable