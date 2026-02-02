# -*- coding: utf-8 -*-
from .redis import *
database['type']='mysql' # 数据库类型  目前支持mysql和sqlite
database['debug']=False  #是否开启数据库调试描述
database['host']=['127.0.0.1']#服务器地址 [地址1,地址2,地址3...] 多个地址分布式(主从服务器)下有效
database['port']=[3306] #端口 [端口1,端口2,端口3...]
database['user']=['root']  #用户名 [用户名1,用户名2,用户名3...]
database['password']=['root']  #密码 [密码1,密码2,密码3...]
database['db']=['test']  #数据库名 [数据库名1,数据库名2,数据库名3...]
database['charset']='utf8mb4'   #数据库编码默认采用utf8mb4
database['pattern']=False # True数据库长连接模式 False数据库短连接模式  注：建议web应用有效，cli应用方式下，如果长时间运行建议使用mysql().close()关闭
database['cli']=False # 是否以cli方式运行
database['dbObjcount']=1 # 连接池数量（单个数据库地址链接数量），数据库链接实例数量 mysql长链接模式下有效
database['deploy']=0 # 数据库部署方式:0 集中式(单一服务器),1 分布式(主从服务器)  mysql数据库有效
database['master_num']=1 #主服务器数量 不能超过host服务器数量  （等于服务器数量表示读写不分离：主主复制。  小于服务器表示读写分离：主从复制。） mysql数据库有效
database['master_dql']=False #主服务器是否可以执行dql语句 是否可以执行select语句  主服务器数量大于等于host服务器数量时必须设置True
database['break']=0 #断线重连次数，0表示不重连。 注：cli模式下 10秒进行一次重连并且连接次数是当前配置的300倍

#mongodb配置
mongo['host']='127.0.0.1'
mongo['port']='27017'
mongo['user']=''
mongo['password']=''
mongo['db']='test'
mongo['retryWrites']=False #是否支持重新写入

#sqlite配置
sqlite['db']='kcwslicuxweb' #sqlite数据库文件