# -*- coding: utf-8 -*-
import re
from bson.objectid import ObjectId
from kcwebs.config import mongo as mongodb
class mongo:
    __config=mongodb
    __clientobj=None
    __dbobj=None
    __tabobj=None
    def __setconn(self):
        import pymongo
        if not self.__clientobj:
            if self.__config['retryWrites']:
                strs='mongodb://'+self.__config['host']+':'+self.__config['port']+'/'
            else:
                strs='mongodb://'+self.__config['host']+':'+self.__config['port']+'/?retryWrites=false'
            self.__clientobj = pymongo.MongoClient(strs)
        self.__dbobj = self.__clientobj[self.__config['db']]
        if self.__config['user'] and self.__config['password']:
            self.__dbobj.authenticate(self.__config['user'],self.__config['password']) #账号密码认证
        self.__tabobj=self.__dbobj[self.__table]
    def connect(self,config):
        """设置mongo链接信息 

        参数 config 参考配置信息格式  可以设置数据库名（以字符串形式）

        返回 mongodb对象
        """
        if config:
            if isinstance(config,dict):
                if "host" in config:
                    self.__config['host']=config['host']
                if "port" in config:
                    self.__config['port']=config['port']
                if "user" in config:
                    self.__config['user']=config['user']
                if "password" in config:
                    self.__config['password']=config['password']
                if "db" in config:
                    self.__config['db']=config['db']
            elif isinstance(config,str):
                self.__config['db']=config
            else:
                print("config类型错误,设置连接不生效")
        return self
    def getobj(self):
        "获取mongodb链接实例"
        self.__setconn()
        return self.__tabobj
    __order=None
    def order(self,order):
        """设置排序
        
        order [('_id', -1)]
        """
        self.__order=order
        return self
    def select(self,id=None):
        """查询所有文档

        返回 文档列表
        """
        
        self.__setconn()
        if id:
            self.where('_id',id)
        lists=[]
        if self.__field:
            arr=self.__tabobj.find(self.__where,self.__field,sort=self.__order)
        else:
            arr=self.__tabobj.find(self.__where,sort=self.__order)
        print(self.__order)
        if self.__limit:
            if self.__limit[1]:
                arr.limit(self.__limit[1])
                arr.skip(self.__limit[0])
            else:
                arr.limit(self.__limit[0])
        for k in arr:
            try: k['_id']
            except: pass
            else: k['_id']=str(k['_id'])
            lists.append(k)
        self.__None()
        return lists
    def find(self,id=None):
        """查询一条文档
        
        返回 文档内容
        """
        self.__setconn()
        if id:
            self.where('_id',id)
        if self.__field:
            arr = self.__tabobj.find_one(self.__where,self.__field)
        else:
            arr = self.__tabobj.find_one(self.__where)
        try: arr['_id']
        except: pass
        else: arr['_id']=str(arr['_id'])
        self.__None()
        return arr
    def countlist(self):
        """查询文档数量和所有文档
        
        返回 文档数量,文档列表
        """
        self.__setconn()
        lists=[]
        if self.__field:
            arr=self.__tabobj.find(self.__where,self.__field)
        else:
            arr=self.__tabobj.find(self.__where)
        if self.__limit:
            if self.__limit[1]:
                arr.limit(self.__limit[1])
                arr.skip(self.__limit[0])
            else:
                arr.limit(self.__limit[0])
        for k in arr:
            try: k['_id']
            except: pass
            else: k['_id']=str(k['_id'])
            lists.append(k)
        self.__None()
        return arr.count(),lists
    def count(self):
        """查询文档数量
        
        返回 文档数量
        """
        self.__setconn()
        count=self.__tabobj.find(self.__where,{}).count()
        self.__None()
        return count
    def update(self,data,multi=True):
        """文档更新
         
        参数 data 要更新的内容  格式：{"name":"测试","age":20}

        multi 默认True  是否全部更新
        """
        #{ "count" : { $gt : 3 } } , { $set : { "test2" : "OK"} }
        self.__setconn()
        # print(self.__where)
        # print({"$set":data})
        ar=self.__tabobj.update(self.__where,{"$set":data},multi=multi)
        self.__None()
        return ar
    def delete(self,id=None):
        """文档删除 删除条件是where函数
        """
        self.__setconn()
        if id:
            self.where('_id',id)
        if self.__where:
            # print(self.__where)
            # exit()
            bo=self.__tabobj.remove(self.__where)
            self.__None()
            if bo:
                return bo['n']
            else:
                return 0
        else:
            self.__None()
            return 0
    def deleteAll(self,id=None):
        """删所有文档除
        """
        self.__setconn()
        bo=self.__tabobj.remove({})
        self.__None()
        if bo:
            return bo['n']
        else:
            return 0
    def insert(self,dicts):
        """插入文档 单条插入或多条插入

        参数 dicts 要插入的内容 单条格式：{"name":"测试","age":20}  。     多条格式：[{"name":"测试","age":20},{"name":"测试","age":20}]

        返回插入的数量
        
        """
        self.__setconn()
        co=0
        if isinstance(dicts,dict):
            if self.__tabobj.insert_one(dicts):
                co=1
        elif isinstance(dicts,list):
            lens=len(dicts)
            if lens>100:
                raise RuntimeError('列表数量超过最大限制100')
            if self.__tabobj.insert_many(dicts):
                co=lens
        return co
    __table=""
    def table(self,table):
        """设置集合名

        参数 table：str 表名
        """
        self.__table=table
        return self
    def __None(self):
        "清除所有赋值条件"
        # self.__lock=None
        # self.__distinct=None
        # self.__join=None
        # self.__joinstr=''
        # self.__alias=None
        # self.__having=None
        # self.__group=None
        # self.__group1=None
        # self.__order=None
        # self.__order1=None
        mongo.__limit=[]
        mongo.__field={}
        mongo.__where={}
        mongo.__table=None
        mongo.__order=None
    __where={}
    def where(self,where = None,*wheres):
        """设置过滤条件  

        参数 where：str 字符串 或 列表
       
        传入方式:

        "id",2 表示id='2'

        "id","in",2,3,4 ...表示 id=2 or id=3 or id=4 ...

        "id","or",2,3,4 ...表示 id=2 or id=3 or id=4 ...

        "id","neq",1 表示 id 不等于 '1'

        eq 等于
        neq 不等于
        gt 大于
        egt 大于等于
        lt 小于
        elt 小于等于
        like LIKE
        """
        # print("wheres",wheres)  {'comments':re.compile('abc')}
        if isinstance(where,dict):
            self.__where=where
        elif isinstance(where,list):
            # import re [("name","eq",'冯坤'),"and",("aa","like",'%wfweaf')]
            # print(re.compile('abc'))
            #{"likes": {$gt:50}, "name": "冯坤","title": "MongoDB 教程"}
            #{"likes":'dav', $or: [{"by": "菜鸟教程"},{"title": "MongoDB 教程"}]}
            zd={}
            t=''
            for k in where:
                if isinstance(k,tuple):
                    if k[1]=='eq':
                        if t=='or':
                            zd['$or'].append({k[0]:k[2]})
                        else:
                            zd[k[0]]=k[2]
                    elif k[1]=='like':
                        if t=='or':
                            zd['$or'].append({k[0]:re.compile(re.sub('%','',k[2]))})
                        else:
                            zd[k[0]]=re.compile(re.sub('%','',k[2]))
                    else:
                        if t=='or':
                            zd['$or'].append({k[0]:{'$'+k[1]:k[2]}})
                        else:
                            n=self.__operator(k[1])
                            zd[k[0]]={n:k[2]}
                elif isinstance(k,str):
                    if k=='or':
                        t=k
                        zd['$or']=[]
            self.__where=zd
            # print(zd)
            # exit()
        elif isinstance(where,str) and len(wheres)==1:
            wheres=list(wheres)
            if where=='_id':
                wheres[0]=ObjectId(wheres[0])
            self.__where[where]=wheres[0]
        elif isinstance(where,str) and len(wheres)==2:
            wheres=list(wheres)
            if where=='_id':
                wheres[1]=ObjectId(wheres[1])
            if wheres[0] == 'eq':
                self.__where[where]=wheres[1]
            elif wheres[0]=='like':
                 self.__where[where]=re.compile(re.sub('%','',wheres[1]))
            else:
                n=self.__operator(wheres[0])
                self.__where[where]={n:wheres[1]}
        elif isinstance(where,str) and isinstance(wheres,tuple):
            #{$or: [{key1: value1}, {key2:value2}]}
            # self.__where={'$or': [{where: wheres[0]}, {where:wheres[1]}]}
            # print(wheres)
            lists=[]
            for k in wheres:
                lists.append({where:k})
            self.__where={'$or': lists}
        # print(self.__where)
        return self
    __field={}
    def field(self,field = "*"):
        """设置过滤显示条件

        参数 field：str 字符串
        """
        if field and field!='*':
            field=field.split(",")
            zd={}
            for f in field:
                zd[f]=1
            self.__field=zd
        return self
    __limit=[]
    def limit(self,offset, length = None):
        """设置查询数量

        参数 offset：int 起始位置

        参数 length：int 查询数量
        """
        offset=int(offset)
        length=int(length)
        if length==None:
            length=offset
            offset=0
        # elif offset > 0:
        #     offset=offset*length-length
        self.__limit=[offset,length]
        return self
    def page(self,offset, length = None):
        """设置分页查询

        参数 offset：int 页码

        参数 length：int 页面数量
        """
        offset=int(offset)
        length=int(length)
        if length==None:
            length=offset
            offset=0
        elif offset > 0:
            offset=offset*length-length
        self.__limit=[offset,length]
        return self
    def __operator(self,strs):
        """运算符转换
        参数 strs 待转的字符串
        返回 已转换的运算符

        符号定义
            eq 等于
            neq 不等于
            gt 大于
            egt 大于等于
            lt 小于
            elt 小于等于
        """
        strss=strs.upper()
        if strss == 'NEQ':
            k='$ne'
        elif strss == 'GT':
            k='$gt'
        elif strss == 'EGT':
            k='$gte'
        elif strss == 'LT':
            k='$lt'
        elif strss == 'ELT':
            k='$lte'
        else:
            k=strss
        return k