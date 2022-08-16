import Ui_checkScore
import sys
from PyQt5.QtWidgets import QApplication,QDialog
from PyQt5.QtGui import QIcon
from loguru import logger

class MainDialog(QDialog):
    def __init__(self,parent=None) -> None:
        super(QDialog,self).__init__(parent)
        self.setWindowTitle("成绩自动监测器")
        self.setWindowIcon(QIcon("nmck_bb.ico"))
        self.ui=Ui_checkScore.Ui_Dialog()
        self.ui.setupUi(self)
        self.setFixedSize(700,600)

if __name__ == '__main__':
    logger.info("程序已经成功启动")
    logger.warning("请勿关闭本黑色窗口，关闭本窗口会直接结束程序")
    app = QApplication(sys.argv)
    dlg = MainDialog()
    dlg.show()
    sys.exit(app.exec_())