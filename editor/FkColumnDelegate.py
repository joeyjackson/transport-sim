from PyQt5.QtCore import Qt, QModelIndex, QAbstractItemModel
from PyQt5.QtWidgets import QStyledItemDelegate, QWidget, QStyleOptionViewItem, QComboBox
from FkTableModel import FkTableModelColumn, DisplaySchemaColumn, DeleteButtonColumn
from db import query
from typing import List, Union
from PyQt5.QtWidgets import QPushButton
from PyQt5.QtCore import Qt

class DeleteButtonDelegate(QStyledItemDelegate):
  def __init__(self, parent=None, *args):
    QStyledItemDelegate.__init__(self, parent, *args)

  def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
    data = index.data(Qt.EditRole)
    if isinstance(data, DeleteButtonColumn):
      btn = QPushButton("Delete", parent)
      btn.clicked.connect(self.currentIndexChanged)
      return btn
    else:
      return super(DeleteButtonDelegate, self).createEditor(parent, option, index)

  def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
    data = index.data(Qt.EditRole)
    if isinstance(data, DeleteButtonColumn):
      pass
    else:
      super(DeleteButtonDelegate, self).setEditorData(editor, index)
      
  def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
    data = index.data(Qt.EditRole)
    if isinstance(data, DeleteButtonColumn):
      model.setData(index, True, Qt.EditRole)
    else:
      super(DeleteButtonDelegate, self).setModelData(editor, model, index)
      
  def currentIndexChanged(self):
    self.commitData.emit(self.sender())


class FkColumnDelegateComboBox(QComboBox):
  def __init__(self, options: List[List[Union[str, int, float]]], schema: DisplaySchemaColumn, parent=None, *args) -> None:
    QComboBox.__init__(self, parent, *args)
    self.options = options
    display_options = [schema.fk_options.display_format.format(*row[1 : len(schema.fk_options.display_columns) + 1]) for row in self.options]
    self.insertItems(0, display_options)
    self.setInsertPolicy(QComboBox.NoInsert)

  def setIndex(self, id_value: int) -> None:
    matches = [i for i in range(len(self.options)) if self.options[i][0] == id_value]
    if len(matches) == 1:
      self.setCurrentIndex(matches[0])

  def currentOption(self) -> List[Union[str, int, float]]:
    return self.options[self.currentIndex()]

class FkColumnDelegate(DeleteButtonDelegate):
  def __init__(self, parent=None, *args):
    DeleteButtonDelegate.__init__(self, parent, *args)

  def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
    data = index.data(Qt.EditRole)
    if isinstance(data, FkTableModelColumn):
      to_query = [data.schema.fk_options.foreign_column_name] + data.schema.fk_options.display_columns + [x.column_name for x in data.schema.fk_options.auxiliary_columns]
      query_results = query(f"""SELECT {", ".join(to_query)} FROM {data.schema.fk_options.reference_table}{"".join([" " + j for j in data.schema.fk_options.additional_joins])} ORDER BY {data.schema.fk_options.foreign_column_name};""")
      options = [list(row) for row in query_results]

      editor = FkColumnDelegateComboBox(options, data.schema, parent)
      return editor
    else:
      return super(FkColumnDelegate, self).createEditor(parent, option, index)

  def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
    data = index.data(Qt.EditRole)
    if isinstance(data, FkTableModelColumn):
      editor.setIndex(data.id_value)
    else:
      super(FkColumnDelegate, self).setEditorData(editor, index)

  def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
    data = index.data(Qt.EditRole)
    if isinstance(data, FkTableModelColumn):
      model.setData(index, editor.currentOption(), Qt.EditRole)
    else:
      super(FkColumnDelegate, self).setModelData(editor, model, index)

  def updateEditorGeometry(self, editor, option, index):
    editor.setGeometry(option.rect)