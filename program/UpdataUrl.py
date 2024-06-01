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
            "User-Agent":"Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36",
        }
        self.data = {}

    def look_for(self):
        """look context"""
        for url in self.url:
            url = self.updataUrl(url)
            res = requests.get(url, headers=self.headers )
            restext = res.text
            fileDir = os.path.dirname(os.path.dirname(__file__))
            filePath = os.path.join(fileDir, 'free')
            if not os.path.exists(filePath):
                os.makedirs(filePath)
            hostUrl, fixName = re.search('https://(.+?)\..*(\..+)', url).group(1, 2)
            fileName = hostUrl + fixName
            filePath = os.path.join(filePath, fileName)
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
        timeData = time.strftime("/%Y%m%d", time.localtime())
        newUrl = re.sub('/\d{2}/', monthData, url)
        newUrl = re.sub('/\d{4}/', yearData, newUrl)
        newUrl = re.sub('[/-]\d{8}', timeData, newUrl)
        return newUrl


a = VPN(
#'https://clashnode.com/wp-content/uploads/2023/07/20230721.yaml',

'https://v2rayshare.com/wp-content/uploads/2024/05/20240531.txt',
        'https://v2rayshare.com/wp-content/uploads/2023/05/20230513.yaml',

'https://nodefree.org/dy/2024/05/20240531.txt',

'https://nodefree.org/dy/2023/07/20230716.yaml',
 'https://www.freeclashnode.com/uploads/2024/05/0-20240531.txt',

'https://www.freeclashnode.com/uploads/2024/05/0-20240531.yaml',

'https://clashgithub.com/wp-content/uploads/rss/20240601.txt',

'https://clashgithub.com/wp-content/uploads/rss/20240601.yml',

'https://node.oneclash.cc/2024/05/20240531.txt',

'https://node.oneclash.cc/2024/05/20240531.yaml',

'https://freeclash.org/wp-content/uploads/2024/05/0531.yaml',

'https://freeclash.org/wp-content/uploads/2024/05/0531.txt',

'https://node.wenode.cc/2024/05/20240531.txt',

'https://node.wenode.cc/2024/05/20240531.yaml',

'https://tglaoshiji.github.io/nodeshare/2024/6/20240601.txt',

'https://tglaoshiji.github.io/nodeshare/2024/6/20240601.yaml'

)
a.look_for()
