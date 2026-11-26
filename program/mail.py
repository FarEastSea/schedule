from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
import os
import smtplib
import sys


class mail:
    """send mail"""

    def __init__(self, mail_host, mail_port, sender_name, sender_username, password, receiver_name, receiver_username):
        # 第三方 SMTP 服务
        self.mail_host = mail_host
        self.mail_port = mail_port
        self.mail_user = sender_username
        self.mail_pass = password

        self.sender = sender_name
        self.receiver_name = receiver_name
        self.receivers = receiver_username

    def _send_message(self, message):
        try:
            with smtplib.SMTP(self.mail_host, self.mail_port, timeout=15) as server:
                server.starttls()
                server.login(self.mail_user, self.mail_pass)
                server.sendmail(self.mail_user, [self.receivers], message.as_string())
            print("邮件发送成功")
            return True
        except smtplib.SMTPException as e:
            print("Error: 无法发送邮件")
            print(e)
            return False

    def send_mail(self, sub, msg):
        """for auto send mail"""
        message = MIMEText(msg, 'plain', 'utf-8')
        message['From'] = formataddr((self.sender, self.mail_user))
        message['To'] = formataddr((self.receiver_name, self.receivers))
        message['Subject'] = sub
        return self._send_message(message)

    def send_mail_file(self):
        """for auto send mail with file"""
        message = MIMEMultipart()
        message['From'] = formataddr((self.sender, self.mail_user))
        message['To'] = formataddr((self.receiver_name, self.receivers))
        message['Subject'] = '明天去看电影吧'
        message.attach(MIMEText('为什么刚才发不了', 'plain', 'utf-8'))

        filePath = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'yaml')
        for f in os.listdir(filePath):
            with open(os.path.join(filePath, f), 'rb') as file:
                text = file.read()
            att1 = MIMEText(text, 'base64', 'utf-8')
            att1["Content-Type"] = 'application/octet-stream'
            att1["Content-Disposition"] = f'attachment; filename="{f}"'
            message.attach(att1)

        return self._send_message(message)

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

        img_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '123.jpg')
        with open(img_path, 'rb') as fp:
            msgImage = MIMEImage(fp.read())
        msgImage.add_header('Content-ID', '<image1>')
        msgRoot.attach(msgImage)

        return self._send_message(msgRoot)


if __name__ == '__main__':
    mail_host = "smtp.qq.com"
    mail_port = 587
    sender_name = os.getenv('SENDER_NAME') or ''
    sender_username = os.getenv('SENDER_USERNAME')
    password = os.getenv('PASSWORD')
    receiver_name = os.getenv('RECEIVER_NAME') or os.getenv('receiver_name') or ''
    receiver_username = os.getenv('RECEIVER_USERNAME')

    if not (sender_username and password and receiver_username):
        print("错误：邮件环境变量 SENDER_USERNAME、PASSWORD 或 RECEIVER_USERNAME 未设置")
        sys.exit(1)

    m = mail(mail_host, mail_port, sender_name, sender_username, password, receiver_name, receiver_username)
    ok = m.send_mail('pythonAnywhere自动续期任务触发', '海底月是天上月，眼前人是心上人🧡')
    if not ok:
        sys.exit(1)
