import os
import time
import re
import hmac
import hashlib
import json
import urllib
import socket
from logger import Logger
try:
    # python3.x
    import urllib.request as urllib2
    import http.cookiejar as cookielib
    import http.client as httplib
except ImportError:
    # python2.x
    import urllib2 
    import cookielib
    import httplib

log = Logger('huawei_debug.log', level='info')

class HUAWEI_WiFi_Management(object):
    def __init__(self):
        #get token before login and after login
        self.webserver_token_url = "http://192.168.8.1/api/webserver/token"
        #login url and three times post ulr
        self.login_url = "http://192.168.8.1/html/index.html"
        self.privacynoticeinfo_url = "http://192.168.8.1/api/app/privacynoticeinfo"
        self.challenge_login_url = "http://192.168.8.1/api/user/challenge_login"
        self.authentication_login_url = "http://192.168.8.1/api/user/authentication_login"
        #home url
        self.content_url = "http://192.168.8.1/html/content.html"
        #reboot url
        self.onlineupg_url = "http://192.168.8.1/api/system/onlineupg"
        self.reboot_url = "http://192.168.8.1/api/device/control"

        # login post parameters 
        self.RequestVerificationToken = ''
        self.SessionID = ''
        self.firstnonce = ''
        self.servernonce = ''
        self.finalnonce = ''
        # self.clientproof = ''
        
        #login headers
        self.headers = {
            "__RequestVerificationToken": self.RequestVerificationToken,
            "_ResponseSource": "Broswer",
            "Accept": "*/*",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie":self.SessionID,
            "Connection": "keep-alive",
            "Referer": "http://192.168.8.1/html/index.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",  
            "X-Requested-With": "XMLHttpRequest"  
        }

        #content headers
        self.content_headers = {
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Cookie":self.SessionID,
            "Connection": "keep-alive",
            "Referer": "http://192.168.8.1/html/index.html",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36 Edge/17.17134",  
            "Upgrade-Insecure-Requests": "1" #DO NOT DELETE!
        } 
    

    def IsWork(self, path = "/"):
        baidu = "www.baidu.com"     #http
        taobao = "www.taobao.com"  #http
        try:
            conn = httplib.HTTPConnection(baidu)
            conn.request("HEAD", "/")
            state = conn.getresponse().status
            if state == 200:
                log.logger.info('work!')
                return True
            else:
                log.logger.error('baidu connect failed')
                time.sleep(5)
                conn = httplib.HTTPConnection(taobao)
                conn.request("HEAD", "/")
                state = conn.getresponse().status
                if state == 200:
                    log.logger.info('work!')
                    return True
                else:
                    log.logger.error('toabao connect failed')
                    return False      
        except httplib.HTTPException as e:
            log.logger.error(e)
            return False

    def GetPostDate(self, request):

        curpath = os.path.dirname(os.path.realpath(__file__))
        xmlpath = os.path.join(curpath, request)
        with open(xmlpath) as fp:
            date = fp.read()
        return date


    def GetCookie(self):
        cookie=cookielib.CookieJar()
        handler=urllib2.HTTPCookieProcessor(cookie)
        opener=urllib2.build_opener(handler)
        opener.open(self.login_url)

        for item in cookie:
            if item.name == 'SessionID':
                self.SessionID = 'SessionID='+item.value
                # log.logger.info(SessionID)
                self.headers['Cookie'] = self.SessionID
                return True
        return False

    def GetLoginToken(self):
        try:
            request = urllib2.Request(self.webserver_token_url)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            log.logger.error('Error code: '+e.code)
            return False
        except urllib2.URLError as e:
            log.logger.error('Reason: '+ e.reason)
            return False
            
        webserver_token = response.read().decode('utf8')
        log.logger.info(webserver_token)
        try:
            # log.logger.info(re.findall(r"<token>(.+?)</token>",webserver_token))
            Token = re.findall(r"<token>(.+?)</token>",webserver_token)
            # log.logger.info(Token[0][32:])
            self.RequestVerificationToken = Token[0][32:]
            self.headers['__RequestVerificationToken'] = self.RequestVerificationToken
            return True
        except:
            return False

    def GetContentToken(self):
        request = urllib2.Request(self.content_url,headers=self.content_headers)
        try:
            response = urllib2.urlopen(request)
            content = response.read().decode('utf8')
        except urllib2.URLError as e:
            log.logger.error (e.reason)

        # log.logger.info(content)
        try:
            Token = re.findall(r"<meta name=\"csrf_token\" content=\"(.+?)\">",content)
            log.logger.info('%s %s '%(Token[0], Token[1]))
            self.RequestVerificationToken = Token[1] #onlineupg post
            self.headers['Referer'] = self.content_url
            self.headers['__RequestVerificationToken'] = self.RequestVerificationToken
            return True
        except:
            return False





    def TheFirstPost(self):
        privacynoticeinfo = self.GetPostDate('privacynoticeinfo')
        # log.logger.info(privacynoticeinfo)
        log.logger.info(self.headers['__RequestVerificationToken'])
        try:
            request = urllib2.Request(self.privacynoticeinfo_url,data = privacynoticeinfo.encode('utf-8'), headers = self.headers)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            log.logger.error('Error code: '+ e.code)
        except urllib2.URLError as e:
            log.logger.error('Reason: ' + e.reason)
                       
        #get response headers information
        self.RequestVerificationToken = response.info().getheader('__RequestVerificationToken')
        log.logger.info(self.RequestVerificationToken)
        
        #get token
        # for key, value in info.items():
        #     log.logger.info("%s = %s" % (key, value))
        #     if key == '__RequestVerificationToken':
        #         self.RequestVerificationToken = value
        #         log.logger.info(self.RequestVerificationToken)
        #         break
        self.headers['__RequestVerificationToken'] = self.RequestVerificationToken
        #get response information
        log.logger.info(response.read().decode('utf8'))

        
    
    def TheSecondPost(self):
        challenge_login = self.GetPostDate('challenge_login')
        log.logger.info(self.headers['__RequestVerificationToken'])
        try:
            self.firstnonce = re.findall(r"<firstnonce>(.+?)</firstnonce>",challenge_login)[0]
            request = urllib2.Request(self.challenge_login_url,data = challenge_login.encode('utf-8'), headers = self.headers)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            log.logger.error('Error code: '+e.code)
        except urllib2.URLError as e:
            log.logger.error('Reason: '+ e.reason)
        #get response headers information
        self.RequestVerificationToken = response.info().getheader('__RequestVerificationToken')
        log.logger.info(self.RequestVerificationToken)
        #get token
        # for key, value in info.items():
        #     # log.logger.info("%s = %s" % (key, value))
        #     if key == '__RequestVerificationToken':
        #         self.RequestVerificationToken = value
        #         # log.logger.info(RequestVerificationToken)
        #         break
        self.headers['__RequestVerificationToken'] = self.RequestVerificationToken
        #get response information
        # log.logger.info(response.read().decode())
        re_servernonce = response.read().decode('utf8')
        log.logger.info(re_servernonce)
        try:
            self.servernonce = re.findall(r"<servernonce>(.+?)</servernonce>",re_servernonce)[0]
        # log.logger.info(servernonce)
            self.finalnonce = self.servernonce
        except:
            pass

    def TheThirdPost(self):
        authentication_login = self.GetPostDate('authentication_login')
        authentication_login = re.sub(r'<finalnonce>(.+?)</finalnonce>', '<finalnonce>' + self.servernonce + '</finalnonce>', authentication_login)

        # get clientproof
        message = "c84ac99f8923034e845ae935c3fea1bb831d17882fe1f823e22a8cdf7078468e"
        ckey = "71b26f7f2499aca61c04fdcee4f3791b21f11b0d65a1a0b449307c42b22ef8e5"

        news=bytearray.fromhex(message)
        # log.logger.info(news)     
        skey = self.firstnonce + ',' + self.finalnonce + ',' + self.finalnonce
        signature = hmac.new(bytearray(skey, encoding = "utf8"),msg=news, digestmod=hashlib.sha256).hexdigest()

        # log.logger.info(signature)
        re_signature = (hex(int(ckey,16) ^ int(signature,16))) #int(long)
        # log.logger.info(re_signature)
        # log.logger.info(type(re_signature))
        # log.logger.info(re_signature[2:])
        clientproof = re_signature[2:-1] #  Only applicable to python2.x ,"0x--str--L"


        authentication_login = re.sub(r'<clientproof>(.+?)</clientproof>', '<clientproof>' + clientproof + '</clientproof>', authentication_login)

        log.logger.info(authentication_login)

        log.logger.info(self.headers['__RequestVerificationToken'])
        log.logger.info(json.dumps(self.headers))
        try:
            request = urllib2.Request(self.authentication_login_url,data = authentication_login.encode('utf-8'), headers = self.headers)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            log.logger.error('Error code: ' + e.code)
        except urllib2.URLError as e:
            log.logger.error('Reason: ' + e.reason)
        #get response headers information
        
        re_cookie = response.info().getheader('Set-Cookie')
        if re_cookie != None:
            log.logger.info(re_cookie)
            re_SessionID = re.findall(r"SessionID=(.+?);",re_cookie)[0]
            self.SessionID = 'SessionID=' + re_SessionID
            log.logger.info(self.SessionID)
        #get token
        # for key, value in info.items():
        #     # log.logger.info("%s = %s" % (key, value))
        #     if key == 'Set-Cookie':
        #         re_SessionID = re.findall(r"SessionID=(.+?);",value)[0]
        #         self.SessionID = 'SessionID=' + re_SessionID
        #         log.logger.info(self.SessionID)
        #         break
        self.headers['Cookie'] = self.SessionID
        self.content_headers['Cookie'] = self.SessionID
        log.logger.info(response.read().decode())


    def onlineupgPost(self):
        onlinupg_login = {"action":"check","data":{"UpdateAction":1}}
        try:
            request = urllib2.Request(self.onlineupg_url, data = json.dumps(onlinupg_login).encode('utf-8'), headers = self.headers)
            response = urllib2.urlopen(request)
        except urllib2.HTTPError as e:
            log.logger.error('Error code: ' + e.code)
        except urllib2.URLError as e:
            log.logger.error('Reason: ' + e.reason)

        self.RequestVerificationToken = response.info().getheader('__RequestVerificationToken')
        log.logger.info(self.RequestVerificationToken)
        #get token
        # for key, value in info.items():
        #     # log.logger.info("%s = %s" % (key, value))
        #     if key == '__RequestVerificationToken':
        #         self.RequestVerificationToken = value
        #         # log.logger.info(RequestVerificationToken)
        #         break
        self.headers['__RequestVerificationToken'] = self.RequestVerificationToken
        log.logger.info(response.read().decode())
    
    def RebootPost(self):
        #reboot
        reboot_login = "<?xml version=\"1.0\" encoding=\"UTF-8\"?><request><Control>1</Control></request>"  
        try:    
            request = urllib2.Request(self.reboot_url,data = reboot_login.encode('utf-8'), headers = self.headers)
            response = urllib2.urlopen(request)    
        except urllib2.HTTPError as e:
            log.logger.error('Error code: '+e.code)
        except urllib2.URLError as e:
            log.logger.error('Reason: '+ e.reason)  
        
        # info = response.info()
        # log.logger.info(info)
        re = response.read().decode()
        log.logger.info(re)
        if "<response>OK</response>" in re:
            log.logger.info("reboot success")
            return True
        else:
            return False



    def IsLogin(self):
        self.GetCookie()
        self.GetLoginToken()
        self.TheFirstPost()
        self.TheSecondPost()
        self.TheThirdPost()
    
    def IsReboot(self):        
        self.IsLogin()
        self.GetContentToken()
        self.onlineupgPost()
        return self.RebootPost()   
   
        
    
    def run(self):
        os.system('udhcpc')
        NetworkStatus = {}
        NetworkStatus['Network'] = '4G'     
        status = False
        flaseTime = 0
        while True:
            status = self.IsWork()
            NetworkStatus['Status'] = status
            try:
                with open('/tmp/stat/network.stat', 'w') as StatusFile:
                    json.dump(NetworkStatus, StatusFile)
            except Exception as e:
                log.logger.error('Network status write error ' + str(e))         
            if status:
                time.sleep(900) #15mins
                flaseTime = 0
            else:
                flaseTime += 1
                time.sleep(10)
            if flaseTime > 3: # 3 times ,reboot
                flaseTime = 0
                self.IsReboot()
                time.sleep(30)

        


if __name__ == "__main__":
    wifi =  HUAWEI_WiFi_Management()
    wifi.run()
    # wifi.IsLogin()
    # wifi.IsReboot()
    # wifi.IsWork()  
