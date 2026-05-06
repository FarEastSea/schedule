import requests
import sys
import time
# from bs4 import BeautifulSoup
import re
import os


class VPN:
    def __init__(self, *urls: str) -> None:
        """pre set"""
        self.url: tuple[str, ...] = urls
        self.request_timeout: tuple[int, int] = (5, 10)
        self.cookies: dict[str, str] = {}
        self.headers = {
            # 'Connection': 'keep-alive',
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
        }
        self.data: dict[str, str] = {}

    def look_for(self) -> tuple[int, int]:
        """look context"""
        success_count = 0
        failure_count = 0
        fileDir = os.path.dirname(os.path.dirname(__file__))
        filePath = os.path.join(fileDir, 'free')
        os.makedirs(filePath, exist_ok=True)

        for original_url in self.url:
            # 对网址中的日期进行调整
            url = self.updataUrl(original_url)
            try:
                res = requests.get(url, headers=self.headers, timeout=self.request_timeout)
                res.raise_for_status()
                # 显示响应编码格式
                print(f"响应编码格式：{res.encoding}, 响应期望格式：{res.apparent_encoding}")
                # 优先使用站点返回的推断编码，避免把非 UTF-8 内容写坏
                res.encoding = res.apparent_encoding or 'utf-8'
                restext = res.text
                match = re.search(r'https://(.+)\..*?/.*(\..+)', url)
                if match is None:
                    raise ValueError(f'无法从 URL 推导文件名：{url}')
                hostUrl, fixName = match.group(1, 2)
                # 注意！ re模块sub方法的pattern会转义两次
                # 处理不要字符
                hostUrl = re.sub(r'(?:^www\.)|\.github$', '', hostUrl)
                # 替换字符
                hostUrl = re.sub(r'\.', '_', hostUrl)
                fileName = hostUrl + fixName
                targetPath = os.path.join(filePath, fileName)
                # 下载文件
                with open(targetPath, 'w+', encoding='utf-8') as f:
                    f.write(restext)
                print(f' {fileName} 更新完成')
                success_count += 1
            except requests.exceptions.Timeout:
                print(f'请求超时，已跳过：{url}')
                failure_count += 1
            except requests.exceptions.RequestException as e:
                print(f'请求失败，已跳过：{url}，错误：{e}')
                failure_count += 1
            except Exception as e:
                print(f'处理失败，已跳过：{url}，错误：{e}')
                failure_count += 1
            # restext = re.findall('[\u4e00-\u9fa5]+', restext)
            # self.preLook(restext)

        print(f'本次更新完成，成功 {success_count} 个，失败 {failure_count} 个')
        return success_count, failure_count

    def preLook(self, restext: str) -> None:
        """print result"""
        try:
            print(restext)
        except UnicodeEncodeError as e:
            print(restext.encode('utf-8'))
            print(f'出错：{e}')

    def updataUrl(self, url: str) -> str:
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

if __name__ == '__main__':
    success_count, _ = a.look_for()
    if success_count == 0:
        sys.exit('所有订阅地址均更新失败，终止后续提交流程。')
