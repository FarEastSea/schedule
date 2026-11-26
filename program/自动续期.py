from html.parser import HTMLParser
import datetime
import os
import re
import sys
from urllib.parse import urljoin

from dateutil.relativedelta import relativedelta
import requests


class _FormParser(HTMLParser):
    """从 HTML 中提取表单 action 与 input 字段（用于纯 HTTP 登录及续期）"""

    def __init__(self):
        super().__init__()
        self.forms = []
        self._current_form = None

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == 'form':
            self._current_form = {
                'action': attr_dict.get('action', ''),
                'method': attr_dict.get('method', 'get').lower(),
                'inputs': [],
            }
        elif tag == 'input' and self._current_form is not None:
            self._current_form['inputs'].append(attr_dict)

    def handle_endtag(self, tag):
        if tag == 'form' and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None


class renew:
    """PythonAnywhere Web 应用自动续期（优先纯 HTTP 请求，异常时自动回退 Selenium）"""

    BASE_URL = 'https://www.pythonanywhere.com'
    USER_AGENT = (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    )

    def __init__(self, username, password):
        self.driver = None
        self.username = username
        self.password = password
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.USER_AGENT})
        self.timeout = (10, 20)

    @staticmethod
    def _expected_expiry_text():
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        target_utc = now_utc + relativedelta(months=1)
        return target_utc.strftime("%A %d %B %Y")

    @staticmethod
    def _parse_forms(html_text):
        parser = _FormParser()
        parser.feed(html_text)
        return parser.forms

    @staticmethod
    def _extract_expiry_text(html_text):
        match = re.search(
            r'<p[^>]*class=["\'][^"\']*webapp_expiry[^"\']*["\'][^>]*>(?:(?!</p>).)*?<strong>(.*?)</strong>',
            html_text,
            re.IGNORECASE | re.DOTALL,
        )
        if not match:
            return ''
        return re.sub(r'\s+', ' ', match.group(1)).strip()

    def _run_http(self):
        """纯 HTTP 登录并提交延期表单，避免启动浏览器"""
        login_url = f'{self.BASE_URL}/login/'
        login_res = self.session.get(login_url, timeout=self.timeout)
        login_res.raise_for_status()

        login_forms = self._parse_forms(login_res.text)
        login_form = next(
            (
                f for f in login_forms
                if any(inp.get('type', '').lower() == 'password' for inp in f['inputs'])
            ),
            None,
        )
        if login_form is None:
            raise RuntimeError('未能从登录页解析到登录表单')

        payload = {}
        username_field = None
        password_field = None
        for inp in login_form['inputs']:
            name = inp.get('name')
            if not name:
                continue
            inp_type = inp.get('type', 'text').lower()
            if inp_type == 'password':
                password_field = name
            elif inp_type in ('text', 'email') and username_field is None:
                username_field = name
            elif 'value' in inp and inp_type in ('hidden', 'submit'):
                payload[name] = inp['value']

        if not username_field or not password_field:
            raise RuntimeError('登录表单缺少用户名或密码字段')

        payload[username_field] = self.username
        payload[password_field] = self.password
        if 'csrfmiddlewaretoken' not in payload and self.session.cookies.get('csrftoken'):
            payload['csrfmiddlewaretoken'] = self.session.cookies.get('csrftoken')

        post_login_url = urljoin(login_url, login_form['action'] or login_url)
        auth_res = self.session.post(
            post_login_url,
            data=payload,
            headers={'Referer': login_url},
            timeout=self.timeout,
        )
        auth_res.raise_for_status()
        if '/login' in auth_res.url.rstrip('/'):
            raise RuntimeError('HTTP 登录失败，可能遇到验证码或二次验证')

        if '/user/' in auth_res.url:
            webapps_url = urljoin(auth_res.url.rstrip('/') + '/', 'webapps/')
        else:
            webapps_url = f'{self.BASE_URL}/user/{self.username}/webapps/'
        webapps_res = self.session.get(webapps_url, timeout=self.timeout)
        webapps_res.raise_for_status()

        webapps_forms = self._parse_forms(webapps_res.text)
        extend_form = next(
            (
                f for f in webapps_forms
                if any('webapp_extend' in inp.get('class', '') for inp in f['inputs'])
            ),
            None,
        )
        if extend_form is None:
            raise RuntimeError('未能在 Webapps 页面找到 webapp_extend 表单')

        extend_payload = {}
        for inp in extend_form['inputs']:
            name = inp.get('name')
            if name and 'value' in inp:
                extend_payload[name] = inp['value']
        if 'csrfmiddlewaretoken' not in extend_payload and self.session.cookies.get('csrftoken'):
            extend_payload['csrfmiddlewaretoken'] = self.session.cookies.get('csrftoken')

        extend_url = urljoin(webapps_url, extend_form['action'])
        extend_res = self.session.post(
            extend_url,
            data=extend_payload,
            headers={'Referer': webapps_url},
            timeout=self.timeout,
        )
        extend_res.raise_for_status()

        expiry_text = self._extract_expiry_text(extend_res.text)
        if not expiry_text:
            check_res = self.session.get(webapps_url, timeout=self.timeout)
            check_res.raise_for_status()
            expiry_text = self._extract_expiry_text(check_res.text)

        if not expiry_text:
            raise RuntimeError('未能解析续期后的到期时间')

        expected = self._expected_expiry_text()
        print(f'HTTP 模式检查到期时间: 页面={expiry_text}, 期望={expected}')
        return expiry_text == expected

    def first(self):
        """初始化 Selenium 浏览器（回退模式）"""
        from selenium import webdriver
        from selenium.webdriver.chromium.options import ChromiumOptions

        _Options = ChromiumOptions()
        _Options.add_argument(f'user-agent="{self.USER_AGENT}"')
        _Options.add_argument("--headless")
        _Options.add_argument("--incognito")
        _Options.add_argument("--no-sandbox")
        _Options.add_argument("--disable-dev-shm-usage")

        try:
            self.driver = webdriver.Chrome(options=_Options)
        except Exception as e:
            print(f'chrome错误：{e}')
            sys.exit(1)

    def login(self):
        """登录"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        url = f'{self.BASE_URL}/login/'
        self.driver.get(url)

        wait = WebDriverWait(self.driver, 15)
        inputEleList = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//p/input")))
        inputEleList[0].send_keys(self.username)
        inputEleList[1].send_keys(self.password)
        inputEleList[1].submit()
        wait.until(EC.url_changes(url))

    def extend_App(self):
        """延期"""
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        domain_tab = f"tab_id_{self.username}_pythonanywhere_com"
        url = f"{self.BASE_URL}/user/{self.username}/webapps/#{domain_tab}"
        self.driver.get(url)
        wait = WebDriverWait(self.driver, 15)
        extend_btn = wait.until(
            EC.element_to_be_clickable((By.XPATH, '//div/form/input[position()=2][@class="btn btn-warning webapp_extend"]'))
        )
        extend_btn.click()
        wait.until(EC.staleness_of(extend_btn))

    def verify(self):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import WebDriverWait

        wait = WebDriverWait(self.driver, 15)
        expiry_elem = wait.until(EC.presence_of_element_located((By.XPATH, '//p[@class="webapp_expiry"]/strong')))
        expiry_time = expiry_elem.text.strip()
        expected = self._expected_expiry_text()
        print(f'Selenium 模式检查到期时间: 页面={expiry_time}, 期望={expected}')
        return expiry_time == expected

    def _run_selenium(self):
        self.first()
        try:
            self.login()
            self.extend_App()
            return self.verify()
        finally:
            if self.driver is not None:
                self.driver.quit()

    def run(self):
        """优先执行纯 HTTP 续期，失败时回退 Selenium"""
        try:
            RenewResult = self._run_http()
        except Exception as http_err:
            print(f'HTTP 快速模式未完成，回退 Selenium 模式：{http_err}')
            RenewResult = self._run_selenium()

        if RenewResult:
            print("续期成功！到期时间已更新为一个月后。")
            sys.exit(0)
        else:
            print("续期失败！请检查页面到期时间是否正确更新。")
            sys.exit(1)


if __name__ == '__main__':
    username = os.getenv('WEBAPP_USERNAME')
    password = os.getenv('WEBAPP_PASSWORD')

    if not username or not password:
        print("错误：环境变量 WEBAPP_USERNAME 或 WEBAPP_PASSWORD 未设置")
        sys.exit(1)

    app = renew(username, password)
    app.run()
