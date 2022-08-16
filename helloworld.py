import sys
from PyQt5.QtWidgets import QApplication,QWidget,QDesktopWidget
from PyQt5.QtGui import QIcon


class Sample(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.initUI()

    def initUI(self):
        self.setGeometry(1200,600,450,220)
        self.setWindowTitle('Hello,world!')
        self.setWindowIcon(QIcon("nmck_bb.ico"))
        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp=QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

if __name__ == '__main__':
    app = QApplication(sys.argv)
    sp = Sample()
    sp.show()
    sys.exit(app.exec_())