import sys
from PySide2.QtWidgets import QApplication,QWidget,QDesktopWidget,QMainWindow
from PySide2.QtGui import QIcon
from Ui_webViewer import Ui_MainWindow


class Sample(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.webview.load('http://www.bing.com')

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