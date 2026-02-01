# -*- coding: utf-8 -*-
from kcwebs.config import session as kcwssession
from . import globals as kcwsglobals
import time,random,hashlib,kcwcache
from datetime import datetime
def __md5(strs):
    m = hashlib.md5()
    m.update(strs.encode())
    return m.hexdigest()
def set(name,value,expire=None):
    "设置session"
    if not expire:
        expire=kcwssession['expire']
    HTTP_COOKIE=kcwsglobals.HEADER.HTTP_COOKIE
    SESSIONID="SESSIONID"+__md5(str(name)+str(kcwssession['prefix']))[0:8]  #######
    try: 
        HTTP_COOKIE=HTTP_COOKIE.split(";")
    except:
        token=None
    else:
        token=None
        for k in HTTP_COOKIE:
            if SESSIONID in k:
                token=k.split("=")[1]
    if not token:
        strs="kcws"+str(time.time())+str(random.randint(0,9))
        token=__md5(strs)
    kcwsglobals.set_cookie=SESSIONID+"="+token+";expires="+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')+"; Max-Age=%d;Path=/" % (int(expire)*10)
    return kcwcache.cache.set_config(kcwssession).set_cache(token,value,expire)
def get(name):
    "获取session"
    HTTP_COOKIE=kcwsglobals.HEADER.HTTP_COOKIE
    try:
        HTTP_COOKIE=HTTP_COOKIE.split(";")
    except:
        return None
    SESSIONID="SESSIONID"+__md5(str(name)+str(kcwssession['prefix']))[0:8]  #########
    token=''
    for k in HTTP_COOKIE:
        if SESSIONID in k:
            token=k.split("=")[1]
    v=kcwcache.cache.set_config(kcwssession).get_cache(token)
    return v
def rm(name):
    "删除session"
    HTTP_COOKIE=kcwsglobals.HEADER.HTTP_COOKIE
    try:
        HTTP_COOKIE=HTTP_COOKIE.split(";")
    except:
        return None
    SESSIONID="SESSIONID"+__md5(str(name)+str(kcwssession['prefix']))[0:8]  #######
    token=''
    for k in HTTP_COOKIE:
        if SESSIONID in k:
            token=k.split("=")[1]
    kcwcache.cache.set_config(kcwssession).del_cache(token)
    kcwsglobals.set_cookie=SESSIONID+"="+token+";expires="+datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')+"; Max-Age=2"
    return True

