import requests
import threading
import os
import re
import json
import time


class QQZone:
    """get msg list"""

    def __init__(self, QQ, token, sCookie, fileName='Zone/result.txt', ImgDir='Zone/Img'):
        """
        set requests config
        look for 20 each search is the best result
        don't change it at most time
        """

        self.url = "https://user.qzone.qq.com/proxy/domain/taotao.qq.com/cgi-bin/emotion_cgi_msglist_v6"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.154 Safari/537.36",
            'Connection': 'close'
        }
        self.cookies = {}
        for i in json.loads(sCookie):
            self.cookies[i['name']] = i['value']
        self.uin = QQ
        self.params = {
            'uin': self.uin,
            # 别忘了更新
            'g_tk': token,
            'pos': 0,
            'num': 20
        }
        self.result = []
        self.fileName = fileName
        self.imgDir = ImgDir

    def get_MsgList(self):
        response = requests.request("GET", self.url, headers=self.headers, params=self.params, cookies=self.cookies)
        resText = response.text
        ResTextNew = re.search('.*?\((.*)\).*', resText).group(1)
        resObj = json.loads(ResTextNew)
        msglist = resObj['msglist']
        herSayList = []
        if msglist:
            for msg in msglist:
                # 判断时区
                timeZone = time.strftime('%Z')
                # CST 中国标准时间
                if timeZone == '中国标准时间':
                    createData = time.strftime("%Y年%m月%d日 %H:%M", time.localtime(msg['created_time']))
                else:
                    createData = time.strftime("%Y年%m月%d日 %H:%M", time.localtime(msg['created_time']+8*60*60))
                msgStatus = {'name': msg['name'],
                             'content': msg['content'],
                             'createDay': msg['createTime'],
                             'createData': createData,
                             'createTime': msg['created_time'],
                             'lastmodify': msg['lastmodify'],
                             'source_name': msg['source_name']
                             }
                if msg.get('pic'):
                    msgStatus['picUrl'] = []
                    for img in msg['pic']:
                        msgStatus['picUrl'].append(img['pic_id'])
                herSayList.append(msgStatus)
            self.result.extend(herSayList)
            return True
        else:
            return False

    def get_AllPage_Msg(self, startNum=0, Num=20):
        """get msg from all pages"""

        Continue_Status = True
        self.params['pos'] = startNum
        self.params['num'] = Num
        while Continue_Status:
            status = self.get_MsgList()
            if status:
                self.params['pos'] += 20
            else:
                Continue_Status = False
        self.write_ResultFile()
        return self.result

    def checkout_and_sort(self):
        """check out with exist file"""

        if os.path.exists(self.fileName):
            with open(self.fileName, 'r') as f:
                txt = f.read()
                Result = json.loads(txt)
                for i in Result:
                    # 验证数据集
                    vertifyData_Create = []
                    vertifyData_Modify = []
                    for message in self.result:
                        vertifyData_Create.append(message['createTime'])
                        if message.get('lastmodify'):
                            vertifyData_Modify.append(message['lastmodify'])
                    # 判断是否添加保存数据
                    if i.get('lastmodify') in (0, None):
                        if i['createTime'] not in vertifyData_Create:
                            self.result.append(i)
                    else:
                        if i['lastmodify'] not in vertifyData_Modify:
                            self.result.append(i)
            # 重新排序
            self.result.sort(key=lambda x: x['createTime'], reverse=True)
        else:
            if not os.path.exists(os.path.dirname(self.fileName)):
                os.makedirs(os.path.dirname(self.fileName))
            with open(self.fileName, 'w') as f:
                f.close()

    def write_ResultFile(self):
        """create a result file"""

        os.chdir(os.path.dirname(os.path.dirname(__file__)))
        # check out file and sort it
        self.checkout_and_sort()
        # create index
        with open(f'{self.fileName}', 'r+') as f:
            f.write(json.dumps(self.result))
        # create Img
        self.downloadImg()


    def downloadImg(self):
        """download picture"""

        imgList = [{'picUrl': img['picUrl'], 'createTime': img['createTime']} for img in self.result if img.get('picUrl')]
        threadList = []
        for img in imgList:
            imgUrlList = img['picUrl']
            imgTime = img['createTime']
            lock = threading.RLock()
            for imgUrl in imgUrlList:
                FileName_ImgTime = f"{imgTime}_{imgUrlList.index(imgUrl)}"
                thread = threading.Thread(target=self.thread_Request, args=(imgUrl, FileName_ImgTime, lock), name=str(FileName_ImgTime), daemon=True)
                thread.start()
                threadList.append(thread)
        for i in threadList:
            i.join()

    def thread_Request(self, imgUrl, imgTime, lock):
        """for threading"""

        dirName = self.imgDir
        lock.acquire()
        if not os.path.exists(f'{os.getcwd()}/{dirName}'):
            os.makedirs(dirName)
        lock.release()
        res = requests.get(imgUrl, headers=self.headers, cookies=self.cookies)
        with open(f'{dirName}/{imgTime}', 'wb+') as f:
            f.write(res.content)


cookie = ''
qq = ''
tk = ''
scookie = os.getenv('QQZONECOOKIES', cookie)
qq = os.getenv('QQ', qq)
tk = os.getenv('QQ_TOKEN', tk)
a = QQZone(qq, tk, scookie)
b = a.get_AllPage_Msg()
print(b)
