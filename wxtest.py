import threading
import os
import time
import sys
import random
import ctypes
import inspect
import base64
import datetime
#from wxpy import *
import urllib.request
import urllib.parse
import urllib.error
import re
import http.cookiejar
import xml.dom.minidom
import sys
import math
import subprocess
import json
import threading
uuid = ''
tip = 0
deviceId = 'e000000000000000'
Tqueue = []
base_uri = ''
redirect_uri = ''
skey = ''
wxsid = ''
wxuin = ''
pass_ticket = ''
SyncKey = {}
BaseRequest = {}
ContactList = []
My = []


def TaskLoop(timeout=180):
    def action_mainloop():
        while True:
            try:
                if len(Tqueue) < 1:
                    taskid = action_getqrcode()
                    start_time = time.time()
                    time.sleep(1)
                if time.time() - start_time > timeout:
                    start_time = time.time()
            except Exception as identifier:
                print('error' + identifier)
    mainloopthread = threading.Thread(target=action_mainloop)
    mainloopthread.start()


def ReadMessageFromFile():
    with open('message.txt', 'r', encoding='UTF-8') as f:
        msg = f.read()
        return msg


def getUUID():
    global uuid
    url = 'https://login.weixin.qq.com/jslogin'
    params = {
        'appid': 'wx782c26e4c19acffb',
        'fun': 'new',
        'lang': 'zh_CN',
        '_': int(time.time()),
    }
    request = urllib.request.Request(
        url=url, data=urllib.parse.urlencode(params).encode(encoding='UTF8'))
    response = urllib.request.urlopen(request)
    data = response.read()
    regx = r'window.QRLogin.code = (\d+); window.QRLogin.uuid = "(\S+?)"'
    pm = re.search(regx, str(data))
    code = pm.group(1)
    uuid = pm.group(2)
    if code == '200':
        return True
    return False


def showQRImage():
    global tip
    url = 'https://login.weixin.qq.com/qrcode/' + uuid
    params = {
        't': 'webwx',
        '_': int(time.time()),
    }
    request = urllib.request.Request(
        url=url, data=urllib.parse.urlencode(params).encode(encoding='UTF-8'))
    response = urllib.request.urlopen(request)
    tip = 1
    QRImagePath = './static/images/{}.png'.format(uuid)
    f = open(QRImagePath, 'wb')
    f.write(response.read())
    f.close()
    return QRImagePath


def writeinfo(taskid):
    with open('info.txt', 'r') as f:
        result = f.read()
        rs = result.split()
    with open('info.txt', 'w') as f:
        for i in rs:
            if not i == taskid:
                print('写入' + i)
                f.write(i + ' ')


def removeQueueAndDelQRImage(taskid, msg):
    Tqueue.remove(taskid)
    if os.path.exists(taskid):
        os.remove(taskid)
        print(msg + taskid)


def action_getqrcode():
    def action(taskid, _uuid):
        """
        等待连接
        """
        print('等待{}连接'.format(_uuid))

        while True:
            waitForLoginResult = waitForLogin(_uuid)
            if waitForLoginResult[0] != '408':
                waitForLoginResult = waitForLogin(_uuid)
                """
                    登录成功
                """
                if waitForLoginResult[0] == '200':
                    writeinfo(taskid)
                    print('流程等待扫码->成功')
                    _redirect_uri = waitForLoginResult[1]
                    _base_uri = waitForLoginResult[2]
                    loginResult = login(_redirect_uri)
                    print('登录流程结束')
                    _BaseRequest = loginResult[1]
                    _skey = loginResult[2]
                    _wxsid = loginResult[3]
                    _wxuin = loginResult[4]
                    _pass_ticket = loginResult[5]
                    if not loginResult[0]:
                        removeQueueAndDelQRImage(taskid, '登录失败,删除二维码')
                        return
                    else:
                        print('流程Login->成功')
                        webwxinitResult = webwxinit(
                            _base_uri, _BaseRequest, _pass_ticket, _skey)
                        _My = webwxinitResult[1]
                        if not webwxinitResult[0]:
                            removeQueueAndDelQRImage(taskid, '初始化失败,删除二维码')
                            return
                        else:
                            print('流程初始化->成功!')
                            print('读取通讯录')
                            _MemberList = webwxgetcontact(
                                _base_uri, _pass_ticket, _skey, _My)
                            MemberCount = len(_MemberList)
                            print('通讯录好友数量{}'.format(MemberCount))
                            # 获取将要发送的消息
                            msg = ReadMessageFromFile()
                            for i in range(0, MemberCount):
                                send2UserName = _MemberList[i]['UserName']
                                sendMsg(_My['UserName'], send2UserName,
                                        msg, _base_uri, _pass_ticket, _BaseRequest, i)
                            print('准备下一个任务...')
                            Tqueue.remove(taskid)
                            #
                            return
            elif waitForLoginResult[0] == '408':
                writeinfo(taskid)
                removeQueueAndDelQRImage(taskid, '二维码过期...删除...')
                return
        # print('结束??????????????????????????????????????????????????????????')
        Tqueue.remove(taskid)
        writeinfo(taskid)
    try:
        opener = urllib.request.build_opener(
            urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        urllib.request.install_opener(opener)
        if not getUUID():
            print(u'获取uuid失败')
            return ''
        else:
            image_path = showQRImage()
            Tqueue.append(image_path)
            print('获取二维码成功' + image_path)

            with open('info.txt', 'a') as f:
                f.write(image_path + ' ')

            t = threading.Thread(target=action, args=(image_path, uuid))
            t.start()
            return image_path
    except Exception as identifier:
        return ''


def is_friend_and_is_test(f):
    return len(f) > 4 and f.name[-4:] == '(测试)'


def waitForLogin(uid):
    global tip, base_uri, redirect_uri
    url = 'https://login.weixin.qq.com/cgi-bin/mmwebwx-bin/login?tip=%s&uuid=%s&_=%s' % (
        tip, uid, int(time.time()))
    request = urllib.request.Request(url=url)
    response = urllib.request.urlopen(request)
    data = response.read()
    regx = r'window.code=(\d+);'
    pm = re.search(regx, str(data))
    code = pm.group(1)
    if code == '201':  # 已扫描
        print(u'成功扫描,请在手机上点击确认以登录..................................................')
        tip = 0
    elif code == '200':  # 已登录
        print(u'正在登录...')
        regx = r'window.redirect_uri="(\S+?)";'
        pm = re.search(regx, str(data))
        redirect_uri = pm.group(1) + '&fun=new'
        base_uri = redirect_uri[:redirect_uri.rfind('/')]
    elif code == '408':
        print('超时...')
    return (code, redirect_uri, base_uri)


def login(r_url):
    print('进入登录流程')
    global skey, wxsid, wxuin, pass_ticket, BaseRequest
    request = urllib.request.Request(url=r_url)
    response = urllib.request.urlopen(request)
    data = response.read()
    print('读取登录数据')
    doc = xml.dom.minidom.parseString(data)
    root = doc.documentElement
    for node in root.childNodes:
        if node.nodeName == 'skey':
            skey = node.childNodes[0].data
        elif node.nodeName == 'wxsid':
            wxsid = node.childNodes[0].data
        elif node.nodeName == 'wxuin':
            wxuin = node.childNodes[0].data
        elif node.nodeName == 'pass_ticket':
            pass_ticket = node.childNodes[0].data
    if skey == '' or wxsid == '' or wxuin == '' or pass_ticket == '':
        return (False,)
    BaseRequest = {
        'Uin': int(wxuin),
        'Sid': wxsid,
        'Skey': skey,
        'DeviceID': deviceId,
    }
    return (True, BaseRequest, skey, wxsid, wxuin, pass_ticket)


def webwxinit(b_url, b_req, _pass_ticket, _skey):
    # print('进入初始化流程')
    global SyncKey
    url = b_url + \
        '/webwxinit?pass_ticket=%s&skey=%s&r=%s' % (
            _pass_ticket, _skey, int(time.time()))
    params = {
        'BaseRequest': b_req
    }
    # print('准备请求初始化数据1')
    request = urllib.request.Request(
        url=url, data=json.dumps(params).encode('utf-8'))
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = urllib.request.urlopen(request)
    # print('请求初始化数据2')
    data = response.read()
    # print('读取初始化数据')
    global ContactList, My
    dic = json.loads(data.decode())
    # print('解析初始化数据')
    ContactList = dic['ContactList']
    My = dic['User']
    ErrMsg = dic['BaseResponse']['ErrMsg']
    Ret = dic['BaseResponse']['Ret']
    if Ret != 0:
        return (False,)
    return (True, My)


def webwxgetcontact(b_url, p_t, _skey, _My):
    url = b_url + \
        '/webwxgetcontact?pass_ticket=%s&skey=%s&r=%s' % (
            pass_ticket, skey, int(time.time()))
    # print('准备请求通讯录数据1')
    request = urllib.request.Request(url=url)
    request.add_header('ContentType', 'application/json; charset=UTF-8')
    response = urllib.request.urlopen(request)
    # print('准备请求通讯录数据2')
    data = response.read()
    data = data.decode('utf-8', 'replace')
    # print('解析通讯录数据')
    dic = json.loads(data)
    # print('通讯录读取成功!')
    MemberList = dic['MemberList']
    SpecialUsers = ['newsapp', 'fmessage', 'filehelper', 'weibo', 'qqmail', 'fmessage', 'tmessage', 'qmessage',
                    'qqsync', 'floatbottle', 'lbsapp', 'shakeapp', 'medianote', 'qqfriend', 'readerapp', 'blogapp',
                    'facebookapp', 'masssendapp', 'meishiapp', 'feedsapp', 'voip', 'blogappweixin', 'weixin',
                    'brandsessionholder', 'weixinreminder', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c',
                    'officialaccounts', 'notification_messages', 'wxid_novlwrv3lqwv11', 'gh_22b87fa7cb3c', 'wxitil',
                    'userexperience_alarm', 'notification_messages']
    # print('检查通讯录数据')
    for i in range(len(MemberList) - 1, -1, -1):
        Member = MemberList[i]
        if Member['VerifyFlag'] & 8 != 0:  # 公众号/服务号
            MemberList.remove(Member)
        elif Member['UserName'] in SpecialUsers:  # 特殊账号
            MemberList.remove(Member)
        elif Member['UserName'].find('@@') != -1:  # 群聊
            MemberList.remove(Member)
        elif Member['UserName'] == _My['UserName']:  # 自己
            MemberList.remove(Member)
    # print('检查通讯录数据完成')
    return MemberList


def sendMsg(MyUserName, ToUserName, msg, _base_uri, _pass_ticket, b_req, index):
    try:
        """
        发送消息
        """
        print('准备发送' + ToUserName + '第' + str(index))
        url = _base_uri + '/webwxsendmsg?pass_ticket=%s' % (_pass_ticket)
        params = {
            "BaseRequest": b_req,
            "Msg": {"Type": 1, "Content": msg, "FromUserName": MyUserName, "ToUserName": ToUserName},
        }
        json_obj = json.dumps(params, ensure_ascii=False).encode(
            'utf-8')  # ensure_ascii=False防止中文乱码
        time.sleep(1)
        # print(url)
        # print(json_obj)
        # print('开始发送')
        request = urllib.request.Request(url=url, data=json_obj)
        request.add_header('ContentType', 'application/json; charset=UTF-8')
        urllib.request.urlopen(request)
    except Exception as identifier:
        print(identifier)
    # 测试
    # response = urllib.request.urlopen(request)
    # data = response.read()
    # print('发送完成')


########################################################################
if __name__ == "__main__":
    TaskLoop()
#########################################################################
