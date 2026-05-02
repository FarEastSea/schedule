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
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


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
            self.driver = webdriver.Chrome(options=_Options)
        except Exception as e:
            print(f'chrome错误：{e}')
            sys.exit(1)

    def login(self):
        """登录"""
        url = 'https://www.pythonanywhere.com/login/'
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)
        inputEleList = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//p/input")))
        username = inputEleList[0]
        username.send_keys(self.username)
        password = inputEleList[1]
        password.send_keys(self.password)
        password.submit()
        # 等待登录跳转完成
        wait.until(EC.url_changes(url))

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
        wait = WebDriverWait(self.driver, 15)
        extend_btn = wait.until(EC.element_to_be_clickable((By.XPATH, '//div/form/input[position()=2][@class="btn btn-warning webapp_extend"]')))
        extend_btn.click()
        # 等待按钮重新可用，确认页面已刷新
        wait.until(EC.staleness_of(extend_btn))

    def verify(self):
        wait = WebDriverWait(self.driver, 15)
        expiry_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="webapp_expiry"]/strong')))
        expiry_time = expiry_elem.text

        # 服务器时区
        # timeZone = datetime.datetime.now().astimezone().tzname()
        # 另一种方法，使用 time 模块
        # timeZone = time.strftime("%Z")

        # CST 中国标准时间
        tz = pytz.timezone('UTC')
        date_UTC_Now = datetime.datetime.now(tz)
        date_UTC_Later = date_UTC_Now + relativedelta(months=1)
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
            print("续期成功！到期时间已更新为一个月后。")
            sys.exit(0)
        else:
            print("续期失败！请检查页面到期时间是否正确更新。")
            sys.exit(1)
        # 调用命令行设置环境变量，测试后不行，无法传递到父环境
        # command = f'setx RenewResult {RenewResult} /m'
        # os.system(command)


username = os.getenv('WEBAPP_USERNAME')
password = os.getenv('WEBAPP_PASSWORD')

if not username or not password:
    print("错误：环境变量 WEBAPP_USERNAME 或 WEBAPP_PASSWORD 未设置")
    sys.exit(1)

a = renew(username, password)
a.run()

