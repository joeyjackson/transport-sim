from PyQt5.QtCore import (
  Qt, 
  QAbstractTableModel, 
  QVariant, 
  QModelIndex,
  pyqtSignal
)
from PyQt5.QtGui import QBrush, QColor
from copy import deepcopy

class MyTableModel(QAbstractTableModel):
  data_changed = pyqtSignal(QModelIndex, QModelIndex, Qt.ItemDataRole)

  def __init__(self, data, parent=None, *args):
    QAbstractTableModel.__init__(self, parent, *args)
    self._last_snapshot = deepcopy(data)
    self._data = deepcopy(data)
    self._resetChanged()

  def _resetChanged(self, value=False):
    self._changed = [[value for _ in row] for row in self._data]

  def update(self, r, c, value):
    old = None
    if r < len(self._last_snapshot) and c < len(self._last_snapshot[0]):
      old = self._last_snapshot[r][c]
    self._data[r][c] = value
    self._changed[r][c] = old is None or old != value

  def setData(self, index, value, role):
    if role == Qt.EditRole:
      self.update(index.row(), index.column(), value)
      self.data_changed.emit(index, index, role)
      return True

  def rowCount(self, parent) -> int:
    return len(self._data)

  def columnCount(self, parent) -> int:
    if len(self._data):
      return len(self._data[0])
    return 0

  def reset(self) -> None:
    self.beginResetModel()
    self._data = deepcopy(self._last_snapshot)
    self._resetChanged()
    self.endResetModel()

  def save(self) -> None:
    self.beginResetModel()
    self._last_snapshot = deepcopy(self._data)
    self._resetChanged()
    self.endResetModel()

  def appendRow(self, row) -> None:
    rc = len(self._data)
    self.beginInsertRows(QModelIndex(), rc, rc)
    self._data.append(row)
    self._changed.append([True for _ in row])
    self.endInsertRows()

  def data(self, index, role) -> QVariant:
    if not index.isValid():
      return QVariant()
    if role == Qt.DisplayRole or role == Qt.EditRole:
      return QVariant(self._data[index.row()][index.column()])
    if role == Qt.BackgroundRole:
      if self._changed[index.row()][index.column()]:
        return QVariant(QBrush(QColor(223, 255, 0)))
      return QVariant()
    return QVariant()

  def flags(self, index):
    if index.column() > 0:
      return Qt.ItemIsSelectable | Qt.ItemIsEnabled | Qt.ItemIsEditable
    return Qt.ItemIsSelectable | Qt.ItemIsEnabled