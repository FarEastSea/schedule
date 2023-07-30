import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from email.header import Header
from email.utils import formataddr
import os
import sys
import json


class mail:
    """send mail"""

    def __init__(self, mail_host, mail_port, sender_name, sender_username, password, receiver_name, receiver_username):
        # 第三方 SMTP 服务
        self.mail_host = mail_host  # 设置服务器
        self.mail_port = mail_port
        self.mail_user = sender_username  # 用户名
        self.mail_pass = password  # 口令

        self.sender = sender_name
        self.receiver_name = receiver_name
        self.receivers = receiver_username  # 接收邮件，可设置为你的QQ邮箱或者其他邮箱

    def send_mail(self, sub, msg):
        """for auto send mail"""

        # 可以使用 'html' 格式发送HTML格式的邮件
        message = MIMEText(msg, 'plain', 'utf-8')
        # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['From'] = formataddr((self.sender, self.mail_user))
        # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        message['To'] = formataddr((self.receiver_name, self.receivers))
        message['Subject'] = sub

        try:
            server = smtplib.SMTP(self.mail_host, self.mail_port)  # 发件人邮箱中的SMTP服务器，端口是25
            # server.starttls()
            # 括号中对应的是发件人邮箱账号、邮箱密码
            server.login(self.mail_user, self.mail_pass)
            # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.sendmail(self.mail_user, [self.receivers, ], message.as_string())
            server.quit()  # 关闭连接
            print("邮件发送成功")
        except smtplib.SMTPException as e:
            print("Error: 无法发送邮件")
            print(e)

    def send_mail_file(self):
        """for auto send mail with file"""

        # 创建一个带附件的实例
        message = MIMEMultipart()
        # 括号里的对应发件人邮箱昵称、发件人邮箱账号
        message['From'] = formataddr((self.sender, self.mail_user))
        # 括号里的对应收件人邮箱昵称、收件人邮箱账号
        message['To'] = formataddr((self.receiver_name, self.receivers))
        message['Subject'] = '明天去看电影吧'

        # 邮件正文内容
        # 可以使用 'html' 格式发送HTML格式的邮件
        message.attach(MIMEText('为什么刚才发不了', 'plain', 'utf-8'))

        filePath = os.path.dirname(os.path.dirname(__file__))
        filePath = os.path.join(filePath, 'yaml')
        files = os.listdir(filePath)
        for f in files:
            with open( os.path.join(filePath, f), 'rb') as file:
                text = file.read()
            # 构造附件1，传送当前目录下的 test.txt 文件
            att1 = MIMEText(text, 'base64', 'utf-8')
            att1["Content-Type"] = 'application/octet-stream'
            # 这里的filename可以任意写，写什么名字，邮件中显示什么名字
            att1["Content-Disposition"] = f'attachment; filename="{f}"'
            message.attach(att1)

        try:
            server = smtplib.SMTP(self.mail_host, self.mail_port)  # 发件人邮箱中的SMTP服务器，端口是25
            server.starttls()
            # 括号中对应的是发件人邮箱账号、邮箱密码
            server.login(self.mail_user, self.mail_pass)
            # 括号中对应的是发件人邮箱账号、收件人邮箱账号、发送邮件
            server.sendmail(self.mail_user, [self.receivers, ], message.as_string())
            server.quit()  # 关闭连接
            print("邮件发送成功")
        except smtplib.SMTPException as e:
            print("Error: 无法发送邮件")
            print(e)

    def send_mail_image(self):
        """send mail image"""

        msgRoot = MIMEMultipart('related')
        msgRoot['From'] = formataddr((self.sender, self.mail_user))
        msgRoot['To'] = formataddr((self.receiver_name, self.receivers))
        msgRoot['Subject'] = 'Python SMTP 邮件测试'

        msgAlternative = MIMEMultipart('alternative')
        msgRoot.attach(msgAlternative)

        mail_msg = """
        <p>Python 邮件发送测试...</p>
        <p><a href="http://www.runoob.com">菜鸟教程链接</a></p>
        <p>图片演示：</p>
        <p><img decoding="async" src="cid:image1"></p>
        """
        msgAlternative.attach(MIMEText(mail_msg, 'html', 'utf-8'))

        # 指定图片为当前目录
        with open(os.path.dirname(__file__)+'/123.jpg', 'rb') as fp:
            msgImage = MIMEImage(fp.read())

        # 定义图片 ID，在 HTML 文本中引用
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)

        try:
            smtpObj = smtplib.SMTP(self.mail_host, self.mail_port)
            smtpObj.starttls()
            smtpObj.login(self.mail_user, self.mail_pass)
            smtpObj.sendmail(self.mail_user, [self.receivers, ], msgRoot.as_string())
            smtpObj.quit()
            print("邮件发送成功")
        except smtplib.SMTPException as e:
            print("Error: 无法发送邮件")
            print(e)

mail_host = "smtp.139.com"
mail_port = 25
sender_name = os.getenv('SENDER_NAME')
sender_username = os.getenv('SENDER_USERNAME')
password = os.getenv('PASSWORD')
receiver_name = os.getenv('RECEIVER_NAME')
receiver_username = os.getenv('RECEIVER_USERNAME')
m = mail(mail_host, mail_port, sender_name, sender_username, password, receiver_name, receiver_username)
m.send_mail('pythonAnywhere自动续期任务触发', '海底月是天上月，眼前人是心上人🧡')
