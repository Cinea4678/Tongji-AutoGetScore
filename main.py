import Ui_checkScore
import sys,re,threading,time,requests,json
from PyQt5.QtWidgets import QApplication,QDialog,QMessageBox,QTextEdit
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal
from loguru import logger
import tools

stop_flag = False

class queryThread(threading.Thread):
    def __init__(self,delayTime=30000,cookie='',term=0,mail=''):
        threading.Thread.__init__(self)
        self.delay = delayTime
        self.cookie = cookie
        self.term = term
        self.mail = mail
    def run(self):
        logger.info("开始查询线程")
        while True:
            if stop_flag:
                break
            logger.info("hahaha")
            time.sleep(10)
        logger.info("停止查询线程")

class LogOutput():
    def __init__(self,qte:QTextEdit):
        self.qte=qte
    def info(self,str:str):
        self.qte.append(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | {str}')
    def warning(self,str:str):
        self.qte.append(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | <span style="color:#ff0000;">{str}</span>')
    def error(self,str:str):
        self.qte.append(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | <span style="font-weight:600; color:#ff0000;">{str}</span>')

class MainDialog(QDialog):
    cookie = ''
    finishSignal = pyqtSignal()

    def __init__(self,parent=None) -> None:
        super(QDialog,self).__init__(parent)
        self.setWindowTitle("成绩自动监测器")
        self.setWindowIcon(QIcon("nmck_bb.ico"))
        self.ui=Ui_checkScore.Ui_Dialog()
        self.ui.setupUi(self)
        self.setFixedSize(700,620)

        self.ui.setMailSuccessLabel.setVisible(False)
        self.ui.cookieLineEdt.setReadOnly(True)
        self.ui.cookieLineEdt.setText("请先填入学号")
        
        self.sNum = ''
        self.cookie = ''
        self.gotTerm = False
        self.term = 0
        self.mail = ''
        self.delay = 30
        self.running = False
        self.basicInfo = None
        self.logger = LogOutput(self.ui.outputWindow)

        self.finishSignal.connect(self.loadFinish)
        self.finishSignal.emit()

    def loadFinish(self):
        logger.info("窗口绘制完成")
        try:
            requests.get("https://www.bilibili.com")
        except Exception as e:
            logger.error(e)
            QMessageBox.warning(self,"警告","您的电脑可能没有连接网络！")
        logger.info("网络测试完成")

    def setCookie(self):
        cookie = self.ui.cookieLineEdt.text()
        if re.match("^.+=.+$",cookie):
            self.cookie = cookie
            logger.info(f"设置了cookie: {self.cookie }")
            self.logger.info(f"设置了cookie: {self.cookie }")
        else:
            QMessageBox.warning(self,"错误","您输入的cookie不正确")
            return
        try:
            rres = tools.getDataOnce(cookie,self.sNum)
        except:
            QMessageBox.warning(self,"错误","您的电脑可能没有联网")
            return
        if rres.status_code!=200:
            self.logger.warning(f"验证cookie失败。HTTP错误码是{rres.status_code}，服务器返回信息：{rres.text}")
            if rres.status_code==401:
                QMessageBox.warning(self,"错误","您填入的cookie无法通过1系统验证。请您检查是否出现了以下几种情况：\n\n    1.cookie已经过旧了。cookie中的用于验证您身份的ID有效期很短，一般一段时间未使用就会失效。您可以重新获取一次cookie；\n    2.cookie的格式不正确，例如您可能为cookie带上了双引号。您可以查看输入框下方的教程；\n    3.如果您确定您正确地填入了学号和cookie却还是出现错误的话，请通过右下角的“提交Bug“中的QQ号码与我联系（加好友时注明提交bug）。\n\n")
            elif rres.status_code==500:
                QMessageBox.warning(self,"错误","1系统暂时宕机，请重新点击确认按钮")
            else:
                QMessageBox.warning(self,"未知错误","未能从1系统验证您的cookie，您可以截图日志区向我提交bug。")
        else:
            res = json.loads(rres.text)
            self.basicInfo = res['data']
            if len(self.basicInfo['term'])==0:
                QMessageBox.warning(self,"提示","您目前没有可以查询的学期，若启动查询，将默认查询最新的学期。")

    def setMail(self):
        mail = self.ui.mailLineEdt.text()
        self.ui.setMailSuccessLabel.setVisible(False)
        if re.match("^\w+@\w+\.[\w\.]+$",mail):
            logger.info(f"设置了mail: {mail}")
            self.logger.info(f"设置了mail: {mail}")
            self.mail = mail
            self.ui.setMailSuccessLabel.setVisible(True)
        else:
            QMessageBox.warning(self,"错误","您输入的邮箱不正确")

    def setNo(self):
        sNum = self.ui.studentNumberEdit.text()
        self.ui.setMailSuccessLabel.setVisible(False)
        if re.match("^[0-9]{4,8}$",sNum):
            logger.info(f"设置了学号: {sNum}")
            self.logger.info(f"设置了学号: {sNum}")
            self.sNum = sNum
            self.ui.cookieLineEdt.setReadOnly(False)
            self.ui.cookieLineEdt.setText("")
        else:
            QMessageBox.warning(self,"错误","您输入的学号不正确")

    def startStop(self):
        global stop_flag
        if not self.running:
            if not self.basicInfo or self.mail=='' or self.cookie=='' or self.sNum=='':
                QMessageBox.warning(self,"错误","您还未完成基础配置")
                return
            self.ui.startButton.setText("停止查询")
            stop_flag=False
            self.thread = queryThread(self.delay,self.cookie,self.term,self.mail)
            self.thread.start()
            self.running = True
        else:
            self.ui.startButton.setText("开始查询")
            stop_flag=True
            self.running = False

    def setTerm(self,index:int):
        self.term = index
        logger.info(f"设置了学期: {index}")
    
    def setTime(self):
        time = self.ui.queryTimeEdit.value()
        self.delay = time
        if time<=10.0:
            QMessageBox.warning(self,"高频查询警告","您正在尝试进行高频率查询，请您务必明确以下几点内容：\n    1.成绩可能每天只出一科，高频查询没有必要；\n    2.高频查询会无意义地增加1系统负担；\n    3.高频查询可能会使您被指控破坏1系统，由此产生的后果将由且仅由您自己承担；\n    4.（最重要）您的高频查询可能会使1系统管理员收紧cookie的有效期，这样大家都没有办法再使用本程序了\n\n因此，本程序暂不允许进行高频查询。将为您调整频率至10秒每次。")
            time=10.0  
        logger.info(f"设置了时间: {time}")

if __name__ == '__main__':
    logger.info("程序已经成功启动")
    logger.warning("请勿关闭本黑色窗口，关闭本窗口会直接结束程序（可以最小化，但不要退出）")
    app = QApplication(sys.argv)
    dlg = MainDialog()
    dlg.show()
    sys.exit(app.exec_())