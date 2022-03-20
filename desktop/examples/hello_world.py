import PyQt5.QtCore 
import PyQt5.QtGui
from PyQt5.QtWidgets import QApplication, QWidget, QLabel
import sys

def hello_window():
  app = QApplication(sys.argv)
  w = QWidget()
  b = QLabel(w)
  b.setText("Hello World!")
  w.setGeometry(400,400,600,300)
  b.move(50,20)
  w.setWindowTitle("PyQt5")
  w.show()

  sys.exit(app.exec_())

# Same as above but OOP
class window(QWidget):
  def __init__(self, parent = None):
    super(window, self).__init__(parent)
    b = QLabel(self)
    b.setText("Hello World!")
    self.setGeometry(400,400,600,300)
    b.move(50,20)
    self.setWindowTitle("PyQt5")

def main():
  app = QApplication(sys.argv)
  w = window()
  w.show()
  sys.exit(app.exec_())

if __name__ == '__main__':
  # hello_window()
  main()