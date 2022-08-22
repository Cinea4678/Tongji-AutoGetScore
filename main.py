import sys,re,threading,time,requests,json
from PyQt5.QtWidgets import QApplication,QDialog,QMessageBox,QTextEdit,QPushButton,QProgressBar,QMainWindow
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSignal,pyqtBoundSignal,QUrl,QRect
from PyQt5.QtWebEngineWidgets import QWebEngineView,QWebEngineProfile
from PyQt5.QtNetwork import QNetworkCookie
from loguru import logger
import tools
import ui.Ui_checkScore as Ui_checkScore
import ui.Ui_verifyMail as Ui_verifyMail
import ui.Ui_webCookie as Ui_webCookie

stop_flag = False

class LogOutput():
    def __init__(self,updateSignal):
        self.updateSignal=updateSignal
    def info(self,str:str):
        self.updateSignal.emit(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | {str}')
    def warning(self,str:str):
        self.updateSignal.emit(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | <span style="color:#ff0000;">{str}</span>')
    def error(self,str:str):
        self.updateSignal.emit(f'{time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())} | <span style="font-weight:600; color:#ff0000;">{str}</span>')

veLastSendTime = 0  #验证邮件最后发送时间
veLastSendAddr = ''

class queryThread(threading.Thread):
    def __init__(self,logger:LogOutput,pbSignal:pyqtBoundSignal,basicData,delayTime=30,cookie='',term=0,mail='',snum=0):
        threading.Thread.__init__(self)
        self.delay = delayTime
        self.cookie = cookie
        self.term = term
        self.mail = mail
        self.snum=snum
        self.logger = logger
        self.pbSignal=pbSignal
        self.basicData=basicData
    def run(self):
        self.logger.info("查询已开始，正在初始化")
        logger.info("开始查询线程")
        grades = []
        for courses in self.basicData['term'][self.term]['creditInfo']:
            grades.append(courses['id'])
        self.logger.info(f"当前已出{len(grades)}门成绩（如果是新学期则为0门，本数量不影响查询过程）")
        totalChecked = 0
        errors = 0

        def query_once():
            rawres = tools.getDataOnce(self.cookie,self.snum)
            try:
                res = json.loads(rawres.text)
            except:
                logger.error(f"查询成绩时出现异常！HTTP状态码：{rawres.status_code}")
                return 1
            if 'code' not in res or res['code']!=200:
                logger.error(f"查询成绩时出现异常！1系统返回的信息：{rawres.text}")
                return 1
            newgrades=[]
            try:
                res['data']['term'][self.term]
            except:
                return 0
            for courses in res['data']['term'][self.term]['creditInfo']:
                if courses['id'] not in grades:
                    newgrades.append(courses)
            if len(newgrades)==0:
                return 0
            else:
                message = "<h2>新出成绩提醒</h2><p>新出"+str(len(newgrades))+"门成绩</p><hr>"
                for course in newgrades:
                    submsg = f"<p>{course['publicCoursesName']}课程<b>{course['courseName']}</b>，成绩为<b>{course['score']}</b>。</p>"
                    message+=submsg
                    grades.append(course['id'])
                message += f"<hr>当前本学期绩点<b>{res['data']['term'][0]['averagePoint']}</b>，总绩点<b>{res['data']['totalGradePoint']}</b><br>已修学分<b>{res['data']['actualCredit']}</b>，挂科学分<b>{res['data']['failingCredits']}</b>。</p><p>本邮件由成绩查询服务自动发送，若您被骚扰可以将本地址添加黑名单。</p>"
                try:
                    tools.send_mail("新出成绩提醒",message,[self.mail])
                except Exception as e:
                    self.logger.error(f"邮件发送失败：{str(e)}")
                    return 1
                return 0
        
        nowStep=0
        while not stop_flag:
            nowStep+=1
            self.pbSignal.emit(nowStep)
            if nowStep<self.delay:
                time.sleep(1)
                continue
            else:
                self.pbSignal.emit(0)
                nowStep=0
            totalChecked+=1
            if query_once()>0:
                self.logger.warning(f"已完成第{totalChecked}次查询，查询不成功")
                errors+=1
            else:
                self.logger.info(f"已完成第{totalChecked}次查询，查询成功")
                errors=0
            if errors>=5:
                self.logger.error("多次查询失败，已停止查询")
                self.logger.info("发送查询失败通知...")
                tools.send_mail("查询失败提醒","<h2>查询成绩失败</h2><h3>目前已经停止查询，您可能需要更新cookie，具体信息参见程序显示内容。</h3><br><p>本邮件由成绩查询服务自动发送，若您被骚扰可以将本地址添加黑名单。</p>",[self.mail])
                break
        self.logger.info("查询已结束")
        logger.info("停止查询线程")

class networkCheck(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
    def run(self):
        try:
            rres = requests.get("https://www.cinea.com.cn/api/hello")
            if rres.status_code!=200:
                tools.send_mail("服务器下线警告",f"用户无法连接至服务器<br>错误码：{rres.status_code}<br>响应界面<div>{rres.content}</div>")
                QMessageBox.warning(self,"警告","作者的服务器当前不在线，系统已自动向作者发送通知，请您稍等！")
        except Exception as e:
            logger.error(e)
            QMessageBox.warning(self,"警告","您的电脑可能没有连接网络！")
        logger.info("网络测试完成")

stopVerifyCounterdownFlag = False

class getCookieDialog(QMainWindow):

    cookieOkSignal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("登录到1系统")
        self.setFixedSize(600,800)
        self.jsid =""
        self.ssid=""
        self.browser = QWebEngineView()
        QWebEngineProfile.defaultProfile().cookieStore().deleteAllCookies()
        QWebEngineProfile.defaultProfile().cookieStore().cookieAdded.connect(self.listenCookie)
        self.browser.load(QUrl("https://1.tongji.edu.cn"))
        QMessageBox.information(self,"提示","现在请你登录到1系统。\n由于1系统的登录状态每隔一段时间就会失效，所以需要你每次使用时都登录一次，敬请谅解。\n登录完成后，窗口会自动关闭。")
        self.setCentralWidget(self.browser)
    
    def listenCookie(self,cookie:QNetworkCookie):
        if "1.tongji.edu.cn" in cookie.domain():
            if cookie.name() in ["JSESSIONID","sessionid"]:
                if cookie.name()=="JSESSIONID":
                    self.jsid = str(cookie.value(),encoding='utf-8')  
                else:
                    self.ssid = str(cookie.value(),encoding='utf-8')
                if self.jsid !="" and self.ssid!="":
                    self.cookieOkSignal.emit(f"JSESSIONID={self.jsid};sessionid={self.ssid};language=cn")
                    self.destroy(True,True)


class verifyMailDialog(QDialog):
    verifyOKSignal = pyqtSignal(bool)

    class TimeCounterdown(threading.Thread):
        def __init__(self,btn:QPushButton):
            threading.Thread.__init__(self)
            self.btn = btn
        def run(self):
            while not stopVerifyCounterdownFlag:
                diff = int(veLastSendTime+60-time.time())
                if diff>0:
                    btnText = f"重新发送({diff})"
                    self.btn.setText(btnText)
                    self.btn.setDisabled(True)
                else:
                    self.btn.setText("重新发送")
                    self.btn.setDisabled(False)
                time.sleep(1)

    def __init__(self,mail,lastSendTime,parent):
        super().__init__()
        self.ui=Ui_verifyMail.Ui_Dialog()
        self.ui.setupUi(self)
        self.setFixedSize(522,223)
        self.setWindowTitle("验证您的邮箱")

        self.mail = mail
        self.lastTime = lastSendTime
        #self.parent = parent
        self.verifyOKSignal.connect(parent.verifiedMail)
        self.counterdown = self.TimeCounterdown(self.ui.resendBtn)
        global stopVerifyCounterdownFlag
        stopVerifyCounterdownFlag = False
        self.counterdown.start()
    
    def __del__(self):
        logger.info("子窗口调用析构函数")
        global stopVerifyCounterdownFlag
        stopVerifyCounterdownFlag = True
    
    def resend(self):
        global veLastSendTime
        if veLastSendTime+60 - time.time()>0:
            res = json.loads(requests.get(f"https://www.cinea.com.cn/api/sqp/check?mail={self.mail}",params={'code':'ccczzz'}).text)
            veLastSendTime = res["lastSendTime"]

    def accept(self) -> None:
        resp = requests.post("https://www.cinea.com.cn/api/sqp/verify",params={"mail":self.mail,"code":self.ui.varifyCodeLE.text()})
        if resp.status_code == 403:
            QMessageBox.warning(self,"验证码错误","您输入的验证码有误，请重新输入！")
            return
        elif resp.status_code==200:
            self.verifyOKSignal.emit(True)
            return super().accept()
        else:
            QMessageBox.warning(self,"未知错误","发生未知错误，请重试！")
            return
    
    def reject(self) -> None:
        return super().reject()

class MainDialog(QDialog):
    cookie = ''
    finishSignal = pyqtSignal()
    logUpdateSignal = pyqtSignal(str)
    pbarUpdateSignal = pyqtSignal(int)

    def __init__(self,parent=None) -> None:
        super(QDialog,self).__init__(parent)
        self.setWindowIcon(QIcon("nmck_bb.ico"))
        self.ui=Ui_checkScore.Ui_Dialog()
        self.ui.setupUi(self)
        self.setFixedSize(700,612)

        self.setWindowTitle("成绩自动监测器")
        self.ui.mailLineEdt.setReadOnly(True)
        self.ui.mailLineEdt.setText("请先填入cookie")
        
        self.sNum = ''
        self.cookie = ''
        self.gotTerm = False
        self.term = 0
        self.mail = ''
        self.delay = 30
        self.running = False
        self.loggedIn = False
        self.basicInfo = None
        self.logger = LogOutput(self.logUpdateSignal)

        self.finishSignal.connect(self.loadFinish)
        self.finishSignal.emit()
        self.logUpdateSignal.connect(self.updateLog)
        self.pbarUpdateSignal.connect(self.updateBar)

    def updateBar(self,value):
        self.ui.progressBar.setValue(value)

    def updateLog(self,string):
        self.ui.outputWindow.append(string)

    def loadFinish(self):
        logger.info("窗口绘制完成")
        nwc = networkCheck()
        nwc.start()
    
    def login2OS(self):
        if self.sNum == '':
            QMessageBox.warning(self,"提示","请先输入学号再登录1系统")
            return
        self.logindlg = getCookieDialog()
        self.logindlg.cookieOkSignal.connect(self.cookieOK)
        self.logindlg.show()

    def cookieOK(self,cookie:str):
        logger.info("取到了cookie："+cookie)
        self.logger.info("取到了cookie："+cookie)
        self.cookie = cookie
        self.logger.info("获取学生信息中")
        t= requests.get(f"https://1.tongji.edu.cn/api/studentservice/studentDetailInfo/getStatusInfoByStudentId?studentId={self.sNum}&_t={int(time.time()*1000)}",headers={"cookie":self.cookie,"user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36 Edg/103.0.1264.44","referer":"https://1.tongji.edu.cn/oldStysteMyGrades"}).text
        res = json.loads(t)
        self.ui.OSloginstatus.setText("<html><head/><body><p><span style=\" font-weight:600; color:#ff0000;\">已登录</span></p></body></html>")
        self.ui.nameLabel.setText(res['data'][0]['studentName'] if "studentName" in res['data'][0] else "无姓名信息")
        self.ui.facultyLabel.setText(res['data'][0]['cultureProfessionName'] if "cultureProfessionName" in res['data'][0] else "无专业信息")
        self.ui.gradeLabel.setText(str(res['data'][0]['currentGrade']) if "currentGrade" in res['data'][0] else "无年级信息")
        self.logger.info("获取学生信息成功")

    def manualSetCookie(self):
        pass

    # def setCookie(self):
    #     cookie = self.ui.cookieLineEdt.text()
    #     if re.match("^.+=.+$",cookie):
    #         self.cookie = cookie
    #         logger.info(f"设置了cookie: {self.cookie }")
    #         self.logger.info(f"设置了cookie")
    #     else:
    #         QMessageBox.warning(self,"错误","您输入的cookie不正确")
    #         return
    #     try:
    #         rres = tools.getDataOnce(cookie,self.sNum)
    #     except:
    #         QMessageBox.warning(self,"错误","您的电脑可能没有联网")
    #         return
    #     if rres.status_code!=200:
    #         self.logger.warning(f"验证cookie失败。HTTP错误码是{rres.status_code}，服务器返回信息：{rres.text}")
    #         if rres.status_code==401:
    #             QMessageBox.warning(self,"错误","您填入的cookie无法通过1系统验证。请您检查是否出现了以下几种情况：\n\n    1.cookie已经过旧了。cookie中的用于验证您身份的ID有效期很短，一般一段时间未使用就会失效。您可以重新获取一次cookie；\n    2.cookie的格式不正确，例如您可能为cookie带上了双引号。您可以查看输入框下方的教程；\n    3.如果您确定您正确地填入了学号和cookie却还是出现错误的话，请通过右下角的“提交Bug“中的QQ号码与我联系（加好友时注明提交bug）。\n\n")
    #         elif rres.status_code==500:
    #             QMessageBox.warning(self,"错误","1系统暂时宕机，请重新点击确认按钮")
    #         else:
    #             QMessageBox.warning(self,"未知错误","未能从1系统验证您的cookie，您可以截图日志区向我提交bug。")
    #     else:
    #         res = json.loads(rres.text)
    #         self.basicInfo = res['data']
    #         self.ui.selectTermComboBox.removeItem(0)
    #         if len(self.basicInfo['term'])==0:
    #             self.ui.selectTermComboBox.addItem("最新的学期")
    #             QMessageBox.warning(self,"提示","您在成绩系统中目前没有学期信息，若启动查询，将默认查询本学期。\n请放心，这种情况是正常的。")
    #         else:
    #             for term in self.basicInfo['term']:
    #                 self.ui.selectTermComboBox.addItem(term['termName'])
    #         self.ui.mailLineEdt.setReadOnly(False)
    #         self.ui.mailLineEdt.setText("")

    def setMail(self):
        mail = self.ui.mailLineEdt.text()
        if re.match("^\w+@\w+\.[\w\.]+$",mail):
            #邮箱验证模块开始，使用了本人自己的api
            global veLastSendAddr,veLastSendTime
            if veLastSendTime>0 and veLastSendAddr==mail:
                #已经发送过邮件，不用再联网验证
                mdlg = verifyMailDialog(mail,veLastSendTime,self)
                mdlg.exec()
                return
            t = requests.get(f"https://www.cinea.com.cn/api/sqp/check?mail={mail}",params={'code':'ccczzz'}).text
            mailInfo = json.loads(t)
            if mailInfo["needVerify"]:
                veLastSendTime = mailInfo["lastSendTime"]
                veLastSendAddr = mail
                mdlg = verifyMailDialog(mail,veLastSendTime,self)
                mdlg.exec()
                return
            elif not mailInfo["valid"]:
                QMessageBox.warning(self,"错误","此邮箱已被投诉禁用，请更换重试")
            else:
                veLastSendAddr = mail
                self.verifiedMail(True)
        else:
            QMessageBox.warning(self,"错误","您输入的邮箱不正确")

    def verifiedMail(self,ok:bool):
        if ok:
            mail = veLastSendAddr
            logger.info(f"设置了mail: {mail}")
            self.logger.info(f"设置了mail: {mail}")
            self.mail = mail
            #self.ui.setMailSuccessLabel.setVisible(True)

    def setNo(self):
        sNum = self.ui.studentNumberEdit.text()
        if re.match("^[0-9]{4,8}$",sNum):
            logger.info(f"设置了学号: {sNum}")
            self.logger.info(f"设置了学号: {sNum}")
            self.sNum = sNum
            # self.ui.cookieLineEdt.setReadOnly(False)
            # self.ui.cookieLineEdt.setText("")
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
            self.thread = queryThread(self.logger,self.pbarUpdateSignal,self.basicInfo,self.delay,self.cookie,self.term,self.mail,self.sNum)
            self.thread.start()
            self.running = True
        else:
            self.ui.startButton.setText("开始查询")
            stop_flag=True
            self.running = False
            self.logger.info("已发送停止查询信号，您可以直接退出程序")
            self.ui.progressBar.reset()

    def setTerm(self,index:int):
        self.term = index
        logger.info(f"设置了学期: {index}")
        self.logger.info(f"设置了第{index}个学期")
    
    def setTime(self):
        time = self.ui.queryTimeEdit.value()
        self.delay = time
        if time<=10.0:
            QMessageBox.warning(self,"高频查询警告","您正在尝试进行高频率查询，请您务必明确以下几点内容：\n    1.成绩可能每天只出一科，高频查询没有必要；\n    2.高频查询会无意义地增加1系统负担；\n    3.高频查询可能会使您被指控破坏1系统，由此产生的后果将由且仅由您自己承担；\n    4.（最重要）您的高频查询可能会使1系统管理员收紧cookie的有效期，这样大家都没有办法再使用本程序了\n\n因此，本程序暂不允许进行高频查询。将为您调整频率至10秒每次。")
            time=10.0
            self.ui.queryTimeEdit.setValue(10.0)
        self.ui.progressBar.setMinimum(0)
        self.ui.progressBar.setMaximum(int(time))
        logger.info(f"设置了时间: {time}")
        self.logger.info(f"设置了时间: {time}")

if __name__ == '__main__':
    logger.info("程序已经成功启动")
    logger.warning("请勿关闭本黑色窗口，关闭本窗口会直接结束程序（可以最小化，但不要退出）")
    app = QApplication(sys.argv)
    dlg = MainDialog()
    dlg.show()
    sys.exit(app.exec_())