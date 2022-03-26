from PyQt5.QtCore import (
  Qt, 
  QAbstractTableModel, 
  QVariant, 
  QModelIndex,
  pyqtSignal,
)
from PyQt5.QtGui import QBrush, QColor
from typing import List, Optional, Union, Tuple, Callable
from collections import namedtuple
from copy import deepcopy
from db import query, connect_to_db
from enum import IntEnum

AuxiliaryColumn = namedtuple("AuxiliaryColumn", ["column_name", "header"])

class ChangedState(IntEnum):
  NONE = 0
  UPDATED = 1
  CREATED = 2
  DELETED = 4

class ForeignKeySpecification:
  def __init__(
    self, 
    reference_table: str, 
    join_on: str, 
    display_columns: List[str],
    display_format: str = "{0}",
    auxiliary_columns: List[AuxiliaryColumn] = []
  ) -> None:
    self.reference_table = reference_table
    self.join_on = join_on
    self.display_columns = display_columns
    self.display_format = display_format
    self.auxiliary_columns = auxiliary_columns


class DeleteButtonColumn:
  def __init__(self):
    pass


class FkTableModelColumn:
  def __init__(self, id_value: int, schema: ForeignKeySpecification):
    self.id_value = id_value
    self.schema = schema


class DisplaySchemaColumn:
  def __init__(self, column_name: str, header: str, default_value: Union[str, int, float], fk_options: Optional[ForeignKeySpecification] = None, isDeleteBtn: bool = False) -> None:
    self.column_name = column_name
    self.header = header
    self.fk_options = fk_options
    self.default_value = default_value
    self.isDeleteBtn = isDeleteBtn

  def is_fk(self) -> bool:
    return self.fk_options is not None
    

def strip_table_name(raw: str) -> str:
  return raw.split(".")[-1]


class FkTableModel(QAbstractTableModel):
  data_changed = pyqtSignal(QModelIndex, QModelIndex, Qt.ItemDataRole)

  def __init__(self, table_name: str, schema: List[DisplaySchemaColumn], onError: Callable[[str], None], clearError: Callable[[], None], parent=None, *args):
    QAbstractTableModel.__init__(self, parent, *args)
    self.table_name = table_name
    self._schema = schema + [DisplaySchemaColumn("Delete", "Delete", DeleteButtonColumn(), None, True)]
    self.onError = onError
    self.clearError = clearError
    self._query_rows = []
    self._joins = set()
    self._query_rows_to_schema = []
    for i, col in enumerate(self._schema):
      if not col.isDeleteBtn:
        self._query_rows.append(col.column_name)
        self._query_rows_to_schema.append(i)
      if col.is_fk():
        self._joins.add(f"LEFT JOIN {col.fk_options.reference_table} ON {col.fk_options.join_on}")
        for display_column in col.fk_options.display_columns:
          self._query_rows.append(display_column)
          self._query_rows_to_schema.append(i)
        for aux_column in col.fk_options.auxiliary_columns:
          self._query_rows.append(aux_column.column_name)
          self._query_rows_to_schema.append(i)
          
    self._uneditable_columns = set()
    self._uneditable_columns.add(0)
    self._displayed_columns_to_schema = [] # [(schema_index, schema_auxiliary_column_index), ...]

    for i, col in enumerate(self._schema):
      self._displayed_columns_to_schema.append((i, None))
      if col.is_fk() and len(col.fk_options.auxiliary_columns) > 0:
        for a in range(len(col.fk_options.auxiliary_columns)):
          self._displayed_columns_to_schema.append((i, a))
          self._uneditable_columns.add(len(self._displayed_columns_to_schema) - 1)

    self._local_data = []

    self._make_query()
    self._resetChanged()

  def _make_query(self):
    self.beginResetModel()
    self._local_data = []
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
      row_result.append([DeleteButtonColumn()])
      self._local_data.append(row_result)
    self.endResetModel()

  def _resetChanged(self):
    self._changed = [[ChangedState.NONE for _ in row] for row in self._local_data]
    self._changed_row = [ChangedState.NONE for _ in self._local_data]

  def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> QVariant:
    if orientation == Qt.Horizontal and role == Qt.DisplayRole:
      schema_column_index, schema_aux_column_index = self._displayed_columns_to_schema[section]
      schema_column = self._schema[schema_column_index]
      if schema_aux_column_index is None:
        return QVariant(schema_column.header)
      else:
        return QVariant(schema_column.fk_options.auxiliary_columns[schema_aux_column_index].header)
    return super().headerData(section, orientation, role)

  def update(self, r: int, c: int, value: Union[str, int, float]):
    old = None
    if r < len(self._local_data) and c < len(self._local_data[0]):
      old = deepcopy(self._local_data[r][c])
    
    schema_column_index, _ = self._displayed_columns_to_schema[c]
    if self._schema[schema_column_index].isDeleteBtn:
      self._changed_row[r] ^= ChangedState.DELETED
    else: 
      self._local_data[r][schema_column_index] = value
    
    if (old is None or old != value) and not self._schema[schema_column_index].isDeleteBtn:
      self._changed[r][c] |= ChangedState.UPDATED 
      self._changed_row[r] |= ChangedState.UPDATED 
    self.clearError()

  def setData(self, index: QModelIndex, value: Union[str, int, float], role: Qt.ItemDataRole):
    if role == Qt.EditRole:
      self.update(index.row(), index.column(), value)
      self.data_changed.emit(index, index, role)
      return True

  def rowCount(self, parent) -> int:
    return len(self._local_data)

  def columnCount(self, parent) -> int:
    if len(self._local_data):
      return len(self._displayed_columns_to_schema)
    return 0

  def reset(self) -> None:
    self.beginResetModel()
    self._make_query()
    self._resetChanged()
    self.endResetModel()
    self.clearError()

  def _delete_statement_for_row(self, row: List[List[Union[str, float, int]]]) -> Tuple[str, List[List[Union[str, float, int]]]]:
    id_name = self._schema[0].column_name
    id_value = row[0][0]
    return f"""DELETE FROM {self.table_name} WHERE {id_name} = ?;""", [id_value]

  def _insert_statement_for_row(self, row: List[List[Union[str, float, int]]]) -> Tuple[str, List[List[Union[str, float, int]]]]:
    col_names = []
    col_values = []
    for i, c in enumerate(row):
      if i == 0:
        continue # id row not set
      col_names.append(strip_table_name(self._schema[i].column_name))
      col_values.append(c[0])
    return f"""INSERT INTO {self.table_name} ({", ".join(col_names)}) VALUES({', '.join(['?' for _ in col_names])});""", col_values

  def _update_statement_for_row(self, row: List[List[Union[str, float, int]]], changed_row: List[int]) -> Tuple[str, List[List[Union[str, float, int]]]]:
    col_names = []
    col_values = []
    id_name = self._schema[0].column_name
    id_value = row[0][0]
    for i, c in enumerate(row):
      if changed_row[i] & ChangedState.UPDATED:
        col_names.append(strip_table_name(self._schema[i].column_name))
        col_values.append(c[0])
    return f"""UPDATE {self.table_name} SET {", ".join([cn + ' = ?' for cn in col_names])} WHERE {id_name} = ?;""", col_values + [id_value]

  def _flush_changes(self) -> None:
    statements = []
    for i, row in enumerate(self._local_data):
      if self._changed_row[i] & ChangedState.CREATED and self._changed_row[i] & ChangedState.DELETED:
        continue
      if self._changed_row[i] & ChangedState.DELETED:
        statements.append(self._delete_statement_for_row(row))
      if self._changed_row[i] & ChangedState.CREATED:
        statements.append(self._insert_statement_for_row(row))
      if self._changed_row[i] & ChangedState.UPDATED:
        statements.append(self._update_statement_for_row(row, self._changed[i]))

    conn = connect_to_db()
    for sql, fields in statements:
      query(sql, fields)
    conn.commit()

  def save(self) -> None:
    self.beginResetModel()
    try:
      self._flush_changes()
      self._make_query()
      self._resetChanged()
      self.clearError()
    except Exception as e:
      self.onError(e)
    finally:
      self.endResetModel()

  def _default_row(self) -> List[Union[str, int, float]]:
    row = []
    for column in self._schema:
      values = []
      values.append(column.default_value)
      if column.is_fk():
        for _ in range(len(column.fk_options.display_columns)):
          values.append("")
        for _ in range(len(column.fk_options.auxiliary_columns)):
          values.append(None)
      row.append(values)
    return row

  def appendRow(self) -> None:
    rc = len(self._local_data)
    self.beginInsertRows(QModelIndex(), rc, rc)
    row = self._default_row()
    self._local_data.append(row)
    self._changed_row.append(ChangedState.CREATED)
    self._changed.append([ChangedState.CREATED for _ in row])
    self.endInsertRows()
    self.clearError()

  def data(self, index, role) -> QVariant:
    if not index.isValid():
      return QVariant()
    if role == Qt.DisplayRole or role == Qt.EditRole:
      schema_column_index, aux_column_index = self._displayed_columns_to_schema[index.column()]
      schema_column = self._schema[schema_column_index]

      raw_data = self._local_data[index.row()][schema_column_index]
      if schema_column.is_fk():
        if aux_column_index is not None:
          return QVariant(raw_data[1 + len(schema_column.fk_options.display_columns) + aux_column_index])
        else:
          if role == Qt.DisplayRole:
            display_columns_data = raw_data[1 : len(schema_column.fk_options.display_columns) + 1]
            formatted = schema_column.fk_options.display_format.format(*display_columns_data)
            return QVariant(formatted)
          elif role == Qt.EditRole:
            return QVariant(FkTableModelColumn(raw_data[0], schema_column))
      elif schema_column.isDeleteBtn:
        if role == Qt.DisplayRole:
          return QVariant("Delete")
        elif role == Qt.EditRole:
          return QVariant(raw_data[0])
      else:
        return QVariant(raw_data[0])

    if role == Qt.BackgroundRole:
      schema_column_index, _ = self._displayed_columns_to_schema[index.column()]
      deleted_row = self._changed_row[index.row()] & ChangedState.DELETED
      created_row = self._changed_row[index.row()] & ChangedState.CREATED
      updated = self._changed[index.row()][schema_column_index] & ChangedState.UPDATED
      uneditable = index.column() in self._uneditable_columns

      if deleted_row:
        if uneditable:
          return QVariant(QBrush(QColor(0xbc, 0x54, 0x4b)))
        else:
          return QVariant(QBrush(QColor(0xff, 0x00, 0x00)))
      elif created_row:
        if uneditable:
          return QVariant(QBrush(QColor(0x3d, 0xed, 0x97)))
        else:
          return QVariant(QBrush(QColor(0x99, 0xed, 0xc3)))
      elif updated:
        if uneditable:
          return QVariant(QBrush(QColor(0x99, 0xbf, 0x00)))
        else:
          return QVariant(QBrush(QColor(0xdf, 0xff, 0x00)))
      else:
        if uneditable:
          return QVariant(QBrush(QColor(0xe6, 0xe6, 0xe6)))
        else:
          return QVariant()

    return QVariant()

  def flags(self, index):
    if index.column() in self._uneditable_columns:
      return Qt.ItemIsEnabled | Qt.ItemIsSelectable
    return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable