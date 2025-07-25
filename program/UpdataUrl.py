import requests
import json
import time
# from bs4 import BeautifulSoup
import re
import os
import sys


class VPN:
    def __init__(self, *urls):
        """pre set"""
        self.url = urls
        self.cookies = {}
        self.headers = {
            # 'Connection': 'keep-alive',
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        }
        self.data = {}

    def look_for(self):
        """look context"""
        for url in self.url:
            # 对网址中的日期进行调整
            url = self.updataUrl(url)
            try:
                res = requests.get(url, headers=self.headers )
            except Exception as e:
                print(f'出现错误：{e}')
                continue
            # 显示响应编码格式
            print(f"响应编码格式：{res.encoding}, 响应期望格式：{res.apparent_encoding}")
            # 指定编码格式
            res.encoding = 'utf-8'
            restext = res.text
            fileDir = os.path.dirname(os.path.dirname(__file__))
            filePath = os.path.join(fileDir, 'free')
            if not os.path.exists(filePath):
                os.makedirs(filePath)
            hostUrl, fixName = re.search(r'https://(.+)\..*?/.*(\..+)', url).group(1, 2)
            # 注意！ re模块sub方法的pattern会转义两次
            # 处理不要字符
            hostUrl = re.sub(r'(?:^www\.)|\.github$', '', hostUrl)
            # 替换字符
            hostUrl = re.sub(r'\.', '_', hostUrl)
            fileName = hostUrl + fixName
            filePath = os.path.join(filePath, fileName)
            # 下载文件
            with open(filePath, 'w+', encoding='utf-8') as f:
                f.write(restext)
                print(f' {fileName} 更新完成')
            # restext = re.findall('[\u4e00-\u9fa5]+', restext)
            # self.preLook(restext)

    def preLook(self, restext):
        """print result"""
        try:
            print(restext)
        except UnicodeEncodeError as e:
            print(restext.encode('utf-8'))
            print(f'出错：{e}')

    def updataUrl(self, url):
        """return data"""
        yearData = time.strftime("/%Y/", time.localtime())
        monthData = time.strftime("/%m/", time.localtime())
        timeData = time.strftime("%Y%m%d", time.localtime())
        newUrl = re.sub(r'/\d{2}/', monthData, url)
        newUrl = re.sub(r'/\d{4}/', yearData, newUrl)
        newUrl = re.sub(r'([/-])\d{8}', fr"\g<1>{timeData}", newUrl)
        return newUrl


a = VPN(
#'https://clashnode.com/wp-content/uploads/2023/07/20230721.yaml',

'https://v2rayshare.githubrowcontent.com/2025/07/20250719.txt',

'https://v2rayshare.githubrowcontent.com/2025/07/20250719.yaml',

'https://nodefree.githubrowcontent.com/2025/07/20250719.txt',

'https://nodefree.githubrowcontent.com/2025/07/20250719.yaml',

'https://www.freeclashnode.com/uploads/2024/05/0-20240531.txt',

'https://node.freeclashnode.com/uploads/2025/07/0-20250719.yaml'

# 'https://freeclash.org/wp-content/uploads/2024/05/0531.yaml',

# 'https://freeclash.org/wp-content/uploads/2024/05/0531.txt',

# 'https://a.nodeshare.xyz/uploads/2025/7/20250719.txt',

# 'https://tglaoshiji.github.io/nodeshare/2024/6/20240601.yaml'

)
a.look_for()
