import requests,json,time
import smtplib
from email.mime.text import MIMEText
from loguru import logger

sender = "noreply@cinea.com.cn"

def send_mail(sub,content,recivers):
    me="成绩查询服务 <noreply@cinea.com.cn>"
    msg=MIMEText(content,_subtype='html',_charset='gb2312')
    msg['Subject']=sub
    msg['From']=me
    msg['To']=";".join(recivers)
    try:  
        s = smtplib.SMTP_SSL("smtpdm.aliyun.com",465)
        s.ehlo("SQPSCORESERVICE")
        s.login(sender,"zsyZSY20030810")  #登陆服务器
        s.sendmail(me, recivers, msg.as_string())  #发送邮件
        s.close()  
        return True
    except Exception as e:  
        logger.error(e)
        raise e

def getDataOnce(cookie,snum)->requests.Response: 
    headers={
        "cookie":cookie,
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "user-agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.66 Safari/537.36 Edg/103.0.1264.44",
        "referer":"https://1.tongji.edu.cn/oldStysteMyGrades"    
    }
    try:
        rawres = requests.get(url=f"https://1.tongji.edu.cn/api/scoremanagementservice/scoreGrades/getMyGrades?studentId={snum}&_t={int(time.time()*1000)}",headers=headers)
    except Exception as e:
        logger.error(e)
        raise e
    if rawres.status_code!=200:
            logger.warning(f"从1系统查询错误。错误码{rawres.status_code}，响应体{rawres.text}")
    return rawres
    
def queryScores(cookie,basicData,term,mail):
    grades = []
    for courses in basicData[term]['creditInfo']:
        grades.append(courses['id'])

    def query_once():
        rawres = getDataOnce(cookie)
        try:
            res = json.loads(rawres.text)
        except:
            logger.error(f"查询成绩时出现异常！HTTP状态码：{rawres.status_code}")
            return 1
        if 'code' not in res or res['code']!=200:
            logger.error(f"查询成绩时出现异常！1系统返回的信息：{rawres.text}")
            return 1
        newgrades=[]
        if term not in res['data']['term']:
            return 0
        for courses in res['data']['term'][term]['creditInfo']:
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
            message += f"<hr>当前本学期绩点<b>{res['data']['term'][0]['averagePoint']}</b>，总绩点<b>{res['data']['totalGradePoint']}</b><br>已修学分<b>{res['data']['actualCredit']}</b>，挂科学分<b>{res['data']['failingCredits']}</b>。</p><p>本邮件由Cinea Works服务器自动发送。</p>"
            send_mail("新出成绩提醒",message,[mail])
            return 0

