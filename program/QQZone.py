from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import json
import os
import re
import sys
import threading

import requests


CST_TZ = datetime.timezone(datetime.timedelta(hours=8))


class QQZone:
    """抓取并完整增量备份 QQ 空间动态及图片（保留所有历史、已删除及修改版本）"""

    def __init__(
        self,
        QQ,
        token,
        sCookie,
        fileName='Zone/result.txt',
        ImgDir='Zone/Img',
        manifestFile='Zone/img_manifest.json',
    ):
        self.url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
        self.headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 6.1; WOW64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/33.0.1750.154 Safari/537.36"
            ),
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.request_timeout = (5, 15)
        self.image_timeout = (5, 20)

        parsed_cookies = json.loads(sCookie)
        if isinstance(parsed_cookies, dict):
            self.cookies = dict(parsed_cookies)
        else:
            self.cookies = {item['name']: item['value'] for item in parsed_cookies}

        self.uin = QQ
        self.params = {
            'uin': self.uin,
            'g_tk': token,
            'pos': 0,
            'num': 20,
        }
        self.result = []
        self.fileName = fileName
        self.imgDir = ImgDir
        self.manifestFile = manifestFile

    @staticmethod
    def _version_key(item):
        """生成动态版本的唯一指纹，确保原版与每次修改版都能完整保留且不重复"""
        return (
            item.get('createTime'),
            item.get('lastmodify') or 0,
            item.get('name', ''),
            item.get('content', ''),
            item.get('source_name', ''),
            tuple(item.get('picUrl') or ()),
        )

    @staticmethod
    def _format_cst_time(timestamp):
        return datetime.datetime.fromtimestamp(timestamp, CST_TZ).strftime("%Y年%m月%d日 %H:%M")

    def get_MsgList(self):
        response = self.session.get(
            self.url,
            params=self.params,
            cookies=self.cookies,
            timeout=self.request_timeout,
        )
        response.raise_for_status()

        match = re.search(r'^[^(]*\((.*)\)[^)]*$', response.text.strip(), re.DOTALL)
        if not match:
            raise ValueError("无法解析 QQ 空间接口返回的 JSONP 数据")

        resObj = json.loads(match.group(1))
        if resObj.get('code', 0) != 0:
            raise RuntimeError(
                f"QQ 空间接口返回异常: code={resObj.get('code')}, message={resObj.get('message', '')}"
            )

        msglist = resObj.get('msglist')
        if not msglist:
            return False

        herSayList = []
        for msg in msglist:
            created_time = msg['created_time']
            msgStatus = {
                'name': msg.get('name', ''),
                'content': msg.get('content', ''),
                'createDay': msg.get('createTime', ''),
                'createData': self._format_cst_time(created_time),
                'createTime': created_time,
                'lastmodify': msg.get('lastmodify', 0),
                'source_name': msg.get('source_name', ''),
            }
            if msg.get('pic'):
                pic_urls = [img['pic_id'] for img in msg['pic'] if img.get('pic_id')]
                if pic_urls:
                    msgStatus['picUrl'] = pic_urls
            herSayList.append(msgStatus)

        self.result.extend(herSayList)
        return True

    def get_AllPage_Msg(self, startNum=0, Num=20):
        """完整抓取当前空间可见窗口（通常半年内）的所有动态页，避免漏掉修改过的旧动态"""
        self.params['pos'] = startNum
        self.params['num'] = Num
        while self.get_MsgList():
            self.params['pos'] += Num
        self.write_ResultFile()
        return self.result

    def checkout_and_sort(self):
        """与历史备份合并并保留所有版本，不删除历史、已删或修改前的任意版本"""
        merged = []
        seen = set()

        # 先放入本次抓到的最新动态，再合并历史备份中所有不完全相同的旧版本
        candidates = list(self.result)
        if os.path.exists(self.fileName):
            with open(self.fileName, 'r', encoding='utf-8') as f:
                txt = f.read().strip()
            if txt:
                candidates.extend(json.loads(txt))
        else:
            parent = os.path.dirname(self.fileName)
            if parent:
                os.makedirs(parent, exist_ok=True)

        for item in candidates:
            key = self._version_key(item)
            if key not in seen:
                seen.add(key)
                merged.append(item)

        merged.sort(key=lambda x: (x.get('createTime', 0), x.get('lastmodify') or 0), reverse=True)
        self.result = merged

    @staticmethod
    def _atomic_write_json(path, data):
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)
        tmp_path = f"{path}.tmp"
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False)
        os.replace(tmp_path, path)

    def write_ResultFile(self):
        """合并结果写入文件并增量下载新图片"""
        repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(repo_root)
        self.checkout_and_sort()
        self._atomic_write_json(self.fileName, self.result)
        self.downloadImg()

    def _load_or_init_manifest(self):
        if os.path.exists(self.manifestFile):
            with open(self.manifestFile, 'r', encoding='utf-8') as f:
                txt = f.read().strip()
            if txt:
                return json.loads(txt)

        # 首次启用 manifest 时，根据现有 result.txt 和磁盘已有图片回填映射，避免重复下载
        manifest = {}
        claimed_files = set()
        for item in reversed(self.result):
            create_time = item.get('createTime')
            for idx, url in enumerate(item.get('picUrl') or []):
                if url in manifest:
                    continue
                base_name = f"{create_time}_{idx}"
                base_path = os.path.join(self.imgDir, base_name)
                if base_name not in claimed_files and os.path.isfile(base_path) and os.path.getsize(base_path) > 0:
                    manifest[url] = base_name
                    claimed_files.add(base_name)
        return manifest

    def downloadImg(self):
        """增量下载缺失或新版本替换的图片，跳过已下载文件且不覆盖旧版本图片"""
        os.makedirs(self.imgDir, exist_ok=True)
        manifest = self._load_or_init_manifest()
        claimed_files = {
            fname
            for fname in manifest.values()
            if os.path.isfile(os.path.join(self.imgDir, fname)) and os.path.getsize(os.path.join(self.imgDir, fname)) > 0
        }

        tasks = []
        queued_urls = set()
        # 按时间从旧到新分配文件名，优先保持原版图片使用 {createTime}_{idx}
        for item in reversed(self.result):
            create_time = item.get('createTime')
            for idx, url in enumerate(item.get('picUrl') or []):
                if url in queued_urls:
                    continue
                existing_name = manifest.get(url)
                if existing_name:
                    existing_path = os.path.join(self.imgDir, existing_name)
                    if os.path.isfile(existing_path) and os.path.getsize(existing_path) > 0:
                        continue

                base_name = f"{create_time}_{idx}"
                base_path = os.path.join(self.imgDir, base_name)
                if base_name not in claimed_files and not (os.path.isfile(base_path) and os.path.getsize(base_path) > 0):
                    target_name = base_name
                else:
                    url_hash = hashlib.sha1(url.encode('utf-8')).hexdigest()[:8]
                    target_name = f"{create_time}_{idx}_{url_hash}"

                claimed_files.add(target_name)
                queued_urls.add(url)
                tasks.append((url, target_name))

        if not tasks:
            if not os.path.exists(self.manifestFile):
                self._atomic_write_json(self.manifestFile, manifest)
            return

        lock = threading.Lock()
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._download_single_image, url, target_name): (url, target_name)
                for url, target_name in tasks
            }
            for future in as_completed(futures):
                url, target_name = futures[future]
                if future.result():
                    with lock:
                        manifest[url] = target_name

        self._atomic_write_json(self.manifestFile, manifest)

    def _download_single_image(self, imgUrl, fileName):
        try:
            res = self.session.get(imgUrl, cookies=self.cookies, timeout=self.image_timeout)
            res.raise_for_status()
            target_path = os.path.join(self.imgDir, fileName)
            tmp_path = f"{target_path}.tmp"
            with open(tmp_path, 'wb') as f:
                f.write(res.content)
            os.replace(tmp_path, target_path)
            return True
        except Exception as e:
            print(f"下载图片失败，已跳过 {fileName} ({imgUrl}): {e}")
            return False


if __name__ == '__main__':
    scookie = os.getenv('QQZONECOOKIES', '').strip()
    qq = os.getenv('QQ', '').strip()
    tk = os.getenv('QQ_TOKEN', '').strip()
    if not (scookie and qq and tk):
        print("错误：环境变量 QQZONECOOKIES、QQ 或 QQ_TOKEN 未设置")
        sys.exit(1)

    zone = QQZone(qq, tk, scookie)
    result = zone.get_AllPage_Msg()
    print(f"同步完成，累计保留 {len(result)} 条动态版本记录")
