import requests
import sys
import os
import json


class renew:
  """renew web app"""

  def renew(self, cookie):
    url = "https://www.pythonanywhere.com/api/v0/user/farsea/webapps/farsea.pythonanywhere.com/ssl/"

    headers = {
      'Accept': '*/*',
      'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
      'Connection': 'close',
      'Cookie': cookie,
      'Referer': 'https://www.pythonanywhere.com/user/farsea/webapps/',
      'Sec-Fetch-Dest': 'empty',
      'Sec-Fetch-Mode': 'cors',
      'Sec-Fetch-Site': 'same-origin',
      'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36 Edg/115.0.1901.183',
      'X-Requested-With': 'XMLHttpRequest',
      'dnt': '1',
      'sec-ch-ua': '"Not/A)Brand";v="99", "Microsoft Edge";v="115", "Chromium";v="115"',
      'sec-ch-ua-mobile': '?0',
      'sec-ch-ua-platform': '"Windows"',
      'sec-gpc': '1'
    }
    response = requests.request("GET", url, headers=headers)
    res = json.loads(response.text)
    print(res['cert_type'])
    RenewResult = res['cert_type'] == 'pythonanywhere-subdomain'
    if RenewResult:
      sys.exit(0)
    else:
      sys.exit(1)
    # 调用命令行设置环境变量，测试后不行，无法传递到父环境
    # command = f'setx RenewResult {RenewResult} /m'
    # os.system(command)


a = renew()
a.renew(os.getenv('WEBAPP_COOKIE'))
