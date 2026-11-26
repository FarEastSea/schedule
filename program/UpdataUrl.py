from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import re
import sys
import time

import requests


class VPN:
    def __init__(self, *urls: str) -> None:
        """pre set"""
        self.url: tuple[str, ...] = urls
        self.request_timeout: tuple[int, int] = (5, 10)
        self.cookies: dict[str, str] = {}
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
            ),
        }
        self.data: dict[str, str] = {}
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def _fetch_one(self, original_url: str, filePath: str) -> bool:
        url = self.updataUrl(original_url)
        try:
            res = self.session.get(url, timeout=self.request_timeout)
            res.raise_for_status()
            print(f"响应编码格式：{res.encoding}, 响应期望格式：{res.apparent_encoding}")
            res.encoding = res.apparent_encoding or 'utf-8'
            restext = res.text

            match = re.search(r'https://(.+)\..*?/.*(\..+)', url)
            if match is None:
                raise ValueError(f'无法从 URL 推导文件名：{url}')
            hostUrl, fixName = match.group(1, 2)
            hostUrl = re.sub(r'(?:^www\.)|\.github$', '', hostUrl)
            hostUrl = re.sub(r'\.', '_', hostUrl)
            fileName = hostUrl + fixName
            targetPath = os.path.join(filePath, fileName)

            with open(targetPath, 'w', encoding='utf-8') as f:
                f.write(restext)
            print(f' {fileName} 更新完成')
            return True
        except requests.exceptions.Timeout:
            print(f'请求超时，已跳过：{url}')
        except requests.exceptions.RequestException as e:
            print(f'请求失败，已跳过：{url}，错误：{e}')
        except Exception as e:
            print(f'处理失败，已跳过：{url}，错误：{e}')
        return False

    def look_for(self) -> tuple[int, int]:
        """look context"""
        success_count = 0
        failure_count = 0
        fileDir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        filePath = os.path.join(fileDir, 'free')
        os.makedirs(filePath, exist_ok=True)

        if not self.url:
            return 0, 0

        max_workers = min(4, len(self.url))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = [executor.submit(self._fetch_one, original_url, filePath) for original_url in self.url]
            for future in as_completed(futures):
                if future.result():
                    success_count += 1
                else:
                    failure_count += 1

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
    'https://www.freeclashnode.com/uploads/2024/05/0-20240531.txt',
    'https://node.freeclashnode.com/uploads/2025/07/0-20250719.yaml',
)

if __name__ == '__main__':
    success_count, _ = a.look_for()
    if success_count == 0:
        sys.exit('所有订阅地址均更新失败，终止后续提交流程。')
