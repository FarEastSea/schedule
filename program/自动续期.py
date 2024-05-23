import requests
import sys
import os
import json
import time
import datetime
import pytz
from dateutil.relativedelta import *
from dateutil.parser import parse
from selenium import webdriver
from selenium.webdriver.chromium.options import ChromiumOptions
from selenium.webdriver.chromium.service import ChromiumService
from selenium.webdriver.common.by import By


# web延期
class renew:
    """renew web app"""

    def __init__(self, username, password):
        self.driver = None
        self.username = username
        self.password = password

    def first(self):
        """初始化"""
        _Options = ChromiumOptions()
        _Options.add_argument(
            'user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 Edg/107.0.1418.24"')
        _Options.add_argument("--headless")
        _Options.add_argument("-incognito")
        _Options.add_argument("--incognito")

        try:
            self.driver = webdriver.chromium(options=_Options)
        except Exception as e:
            print(f'chrome错误：{e}')
            sys.exit()

    def login(self):
        """登录"""
        url = 'https://www.pythonanywhere.com/login/'
        self.driver.get(url)

        inputEleList  = self.driver.find_elements(By.XPATH,"//p/input")
        username = inputEleList[0]
        username.send_keys(self.username)
        password = inputEleList[1]
        password.send_keys(self.password)
        password.submit()

    def extend_App(self):
        """延期"""

        # javascript_code = f"""
        #         var xhr = new XMLHttpRequest();
        #         xhr.open("GET", "https://www.pythonanywhere.com/api/v0/user/farsea/webapps/farsea.pythonanywhere.com/ssl/", false);
        #         xhr.setRequestHeader('Connection', 'close');
        #         xhr.send();
        #         var re = {{"responseText":xhr.responseText,"responseHeaders":xhr.getAllResponseHeaders(),"status":xhr.status}};
        #         return JSON.stringify(re);
        #         """
        # res = driver.execute_script(javascript_code)
        # res = json.loads(res)
        # print(res)

        url = "https://www.pythonanywhere.com/user/farsea/webapps/#tab_id_farsea_pythonanywhere_com"
        self.driver.get(url)
        extend_btn = self.driver.find_element(By.XPATH,'//div/form/input[position()=2][@class="btn btn-warning webapp_extend"]')
        extend_btn.click()

    def verify(self):
        expiry_time = self.driver.find_element(By.XPATH, '//p[@class="webapp_expiry"]/strong')
        expiry_time = expiry_time.text

        # 服务器时区
        # timeZone = datetime.datetime.now().astimezone().tzname()
        # 另一种方法，使用 time 模块
        # timeZone = time.strftime("%Z")

        # CST 中国标准时间
        tz = pytz.timezone('UTC')
        date_UTC_Now = datetime.datetime.now(tz)
        date_UTC_Later = date_UTC_Now + relativedelta(months=3)
        date_UTC = datetime.datetime.strftime(date_UTC_Later, "%A %d %B %Y")

        # 检验过期时间是否是三个月后的今天
        verify_status = expiry_time == date_UTC
        return verify_status

    def run(self):
        """运行"""
        self.first()
        self.login()
        self.extend_App()
        RenewResult = self.verify()
        self.driver.quit()

        # 根据运行结果判断是否成功，返回对应状态值
        if RenewResult:
            sys.exit(0)
        else:
            sys.exit(1)
        # 调用命令行设置环境变量，测试后不行，无法传递到父环境
        # command = f'setx RenewResult {RenewResult} /m'
        # os.system(command)


username = os.getenv('WEBAPP_USERNAME')
password = os.getenv('WEBAPP_PASSWORD')
a = renew(username, password)
a.run()

