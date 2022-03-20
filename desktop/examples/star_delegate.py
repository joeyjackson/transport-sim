from PyQt5.QtCore import Qt, QModelIndex, QRect, QSize, QPointF, pyqtSignal, QAbstractItemModel
from PyQt5.QtWidgets import QStyledItemDelegate, QStyle, QWidget, QStyleOptionViewItem
from PyQt5.QtGui import QPainter, QPalette, QPolygonF, QPaintEvent, QMouseEvent, QBrush, QColor
from math import cos, sin
from enum import Enum
from typing import Optional

_starPolygon: QPolygonF = QPolygonF() 
_starPolygon << QPointF(1.0, 0.5)
for i in range(1, 5):
  _starPolygon << QPointF(
    0.5 + 0.5 * cos(0.8 * i * 3.14), 
    0.5 + 0.5 * sin(0.8 * i * 3.14))

_diamondPolygon: QPolygonF = QPolygonF()
_diamondPolygon << QPointF(0.4, 0.5) \
  << QPointF(0.5, 0.4) \
  << QPointF(0.6, 0.5) \
  << QPointF(0.5, 0.6) \
  << QPointF(0.4, 0.5)

class StarRating:
  class EditMode(Enum):
    Editable = 0
    ReadOnly = 1

  PaintingScaleFactor = 20

  def __init__(self, starCount: int = 1, maxStarCount: int = 5) -> None:
    self._starCount = starCount
    self._maxStarCount = maxStarCount

  def paint(self, painter: QPainter, rect: QRect, palette: QPalette, mode: EditMode, bgColor: Optional[QBrush] = None) -> None:
    painter.save()
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setPen(Qt.NoPen)
    painter.setBrush(palette.highlight() if mode == StarRating.EditMode.Editable else palette.windowText())

    if bgColor is not None:
      x, y, w, h = rect.x(), rect.y(), rect.width(), rect.height()
      painter.fillRect(x, y, w, h, bgColor)

    yOffset: int = (rect.height() - self.PaintingScaleFactor) / 2
    painter.translate(rect.x(), rect.y() + yOffset)
    painter.scale(self.PaintingScaleFactor, self.PaintingScaleFactor)
    for i in range(self._maxStarCount):
      if (i < self._starCount):
        painter.drawPolygon(_starPolygon, Qt.WindingFill)
      elif (mode == StarRating.EditMode.Editable):
        painter.drawPolygon(_diamondPolygon, Qt.WindingFill)
      painter.translate(1.0, 0.0)
    painter.restore()

  def sizeHint(self) -> QSize:
    return self.PaintingScaleFactor * QSize(self._maxStarCount, 1)

  def starCount(self) -> int:
    return self._starCount
  
  def maxStarCount(self) -> int:
    return self._maxStarCount
  
  def setStarCount(self, starCount: int) -> None:
    self._starCount = starCount
  
  def setMaxStarCount(self, maxStarCount: int) -> None:
    self._maxStarCount = maxStarCount

class StarEditor(QWidget):
  editingFinished = pyqtSignal()

  def __init__(self, parent=None, *args):
    QWidget.__init__(self, parent, *args)
    self.setMouseTracking(True)
    self.setAutoFillBackground(True)
    self._starRating = StarRating()

  def paintEvent(self, event: QPaintEvent) -> None:
    painter = QPainter(self)
    self._starRating.paint(painter, self.rect(), self.palette(), StarRating.EditMode.Editable)

  def mouseMoveEvent(self, event: QMouseEvent) -> None:
    star: int = self._starAtPosition(event.x())
    if (star != self._starRating.starCount() and star != -1):
      self._starRating.setStarCount(star)
      self.update()

  def mouseReleaseEvent(self, event: QMouseEvent) -> None:
    self.editingFinished.emit()

  def sizeHint(self) -> QSize:
    return self._starRating.sizeHint()

  def setStarRating(self, starRating: StarRating, index: QModelIndex) -> None:
    self._starRating = starRating

  def starRating(self) -> StarRating:
    return self._starRating

  def _starAtPosition(self, x: int) -> int:
    star: int = (x // (self._starRating.sizeHint().width() // self._starRating.maxStarCount())) + 1
    if (star <= 0 or star > self._starRating.maxStarCount()):
      return -1
    return star


class StarDelegate(QStyledItemDelegate):
  def __init__(self, parent=None, *args):
    QStyledItemDelegate.__init__(self, parent, *args)

  def paint(self, painter: QPainter, option: QStyleOptionViewItem, index: QModelIndex) -> None:
    starRating = index.data()
    bgColor = index.model().data(index, Qt.BackgroundRole).value()
    if isinstance(starRating, StarRating):
      if option.state & QStyle.State_Selected:
        painter.fillRect(option.rect, option.palette.highlight())
      starRating.paint(painter, option.rect, option.palette, StarRating.EditMode.ReadOnly, bgColor)
    else:
      super(StarDelegate, self).paint(painter, option, index)

  def sizeHint(self, option: QStyleOptionViewItem, index: QModelIndex) -> QSize:
    starRating = index.data()
    if isinstance(starRating, StarRating):
      return starRating.sizeHint()
    else:
      return super(StarDelegate, self).sizeHint(option, index)

  def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: QModelIndex) -> QWidget:
    starRating = index.data()
    if isinstance(starRating, StarRating):
      editor = StarEditor(parent)
      editor.editingFinished.connect(self.commitAndCloseEditor)
      return editor
    else:
      return super(StarDelegate, self).createEditor(parent, option, index)

  def setEditorData(self, editor: QWidget, index: QModelIndex) -> None:
    starRating = index.data()
    if isinstance(starRating, StarRating):
      editor.setStarRating(starRating, index)
    else:
      super(StarDelegate, self).setEditorData(editor, index)

  def setModelData(self, editor: QWidget, model: QAbstractItemModel, index: QModelIndex) -> None:
    starRating = index.data()
    if isinstance(starRating, StarRating):
      model.setData(index, editor.starRating(), Qt.EditRole)
    else:
      super(StarDelegate, self).setModelData(editor, model, index)

  def commitAndCloseEditor(self):
    editor = self.sender()
    self.commitData.emit(editor)
    self.closeEditor.emit(editor)


