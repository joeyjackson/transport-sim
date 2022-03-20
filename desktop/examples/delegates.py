from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QStyledItemDelegate, QSpinBox

class MyHexSpinboxDelegate(QStyledItemDelegate):
  def __init__(self, parent=None, *args):
    QStyledItemDelegate.__init__(self, parent, *args)
    
  def createEditor(self, parent, option, index):
    editor = QSpinBox(parent)
    editor.setFrame(False)
    editor.setMinimum(0)
    editor.setMaximum(1000000)
    return editor

  def setEditorData(self, editor, index):
    # We know that the editor widget is a spin box, but we could have provided 
    # different editors for different types of data in the model, in which case 
    # we would need to ensure we are using the appropriate editor's member 
    # functions
    value = index.model().data(index, Qt.EditRole).value()
    try:
      value = int(value, 0)
    except ValueError as e:
      print("err:", e)
      value = 0
    editor.setValue(value)

  def setModelData(self, editor, model, index):
    editor.interpretText()
    value = editor.value()
    value = hex(value)
    model.setData(index, value, Qt.EditRole)

  def updateEditorGeometry(self, editor, option, index):
    editor.setGeometry(option.rect)
  