import requests
import threading
import os
import re
import json


class QQZone:
    """get msg list"""

    def __init__(self, sCookie, fileName='Zone/result.txt', ImgDir='Zone/Img'):
        """
        set requests config
        look for 20 each search is the bast result
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
        self.params = {
            'uin': '',
            'g_tk': '412342335',
            'pos': 0,
            'num': 20
        }
        self.result = []
        self.fileName = fileName
        self.imgDir = ImgDir

    def get_MsgList(self):
        response = requests.request("GET", self.url, headers=self.headers, params=self.params, cookies=self.cookies)
        print(response.cookies)
        print()
        resText = response.text
        ResTextNew = re.search('.*?\((.*)\).*', resText).group(1)
        resObj = json.loads(ResTextNew)
        msglist = resObj['msglist']
        herSayList = []
        if msglist:
            for msg in msglist:
                msgStatus = {'conten': msg['content'],
                             'createDay': msg['createTime'],
                             'createTime': msg['created_time']
                             }
                if msg.get('pic'):
                    msgStatus['picUrl'] = msg['pic'][0]['pic_id']
                herSayList.append(msgStatus)
            self.result.extend(herSayList)
            return True
        else:
            return False

    def get_AllPage_Msg(self, QQ, startNum=0, Num=20):
        """get msg from all pages"""

        Continue_Status = True
        self.params['uin'] = QQ
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
                for i in self.result:
                    vertifyData = [time['createTime'] for time in Result]
                    if i['createTime'] not in vertifyData:
                        Result.append(i)
            Result.sort(key=lambda x: x['createTime'], reverse=True)
            self.result = Result
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
            imgUrl = img['picUrl']
            imgTime = img['createTime']
            lock = threading.RLock()
            thread = threading.Thread(target=self.thread_Request, args=(imgUrl, imgTime, lock), name=str(imgTime), daemon=True)
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


scookie = os.getenv('cookies')
qq = os.getenv('QQ')
a = QQZone(scookie)
b = a.get_AllPage_Msg(qq)