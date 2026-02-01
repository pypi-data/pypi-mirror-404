# -*- coding: utf-8 -*-
from kcwebs import config
import kcwsqlite
class model:
    table=None
    fields={}
    __db=None
    config=config.database
    def __init__(self):
        if not self.table:
            self.table=self.__class__.__name__
        self.__db=kcwsqlite.sqlite.connect(self.config).table(self.table)
    def create_table(self):
        "创建表"
        sqlist=[]
        for k in self.fields.keys():
            sqlist.append(k+" "+self.fields[k])
        # print(self.table)
        sqls="create table "+self.table+" ("
        for k in sqlist:
            sqls=sqls+k+", "
        sqls=sqls[:-2]+")"
        # print(sqls)
        self.__db.execute(sqls)
    def find(self):
        return self.__db.find()
    def select(self):
        lists=self.__db.select()
        # print(lists)
        return lists
    def insert(self,data):
        return self.__db.insert(data)
    def update(self,data):
        return self.__db.update(data)
    def startTrans(self):
        "开启事务,仅对 update方法、delete方法、install方法有效"
        self.__db.startTrans()
    def commit(self):
        """事务提交

        增删改后的任务进行提交
        """
        self.__db.commit()
    def rollback(self):
        """事务回滚

        增删改后的任务进行撤销
        """
        self.__db.rollback()
    def where(self,where = None,*wheres):
        """设置过滤条件

        传入方式:
        "id",2 表示id='2'

        "id","in",2,3,4,5,6,...表示 id in (2,3,4,5,6,...)

        "id","or",2,3,4,5,6,...表示 id=2 or id=3 or id=4...

        [("id","gt",6000),"and",("name","like","%超")] 表示 ( id > "6000" and name LIKE "%超" )

        "id","eq",1 表示 id = '1'

        eq 等于
            neq 不等于
            gt 大于
            egt 大于等于
            lt 小于
            elt 小于等于
            like LIKE
        """
        self.__db.where(where,*wheres)
        return self
    def field(self,field = "*"):
        """设置过滤显示条件

        参数 field：str 字符串
        """
        self.__db.field(field)
        return self
    __limit=[]
    def limit(self,offset, length = None):
        """设置查询数量

        参数 offset：int 起始位置

        参数 length：int 查询数量
        """
        self.__db.limit(offset, length)
        return self
    def order(self,strs=None,*strs1):
        """设置排序查询

        传入方式:

        "id desc"

        "id",'name','appkey','asc'

        "id",'name','appkey'   不包含asc或desc的情况下 默认是desc

        ['id','taskid',{"task_id":"desc"}]
        """
        self.__db.order(strs=None,*strs1)
        return self
    __distinct=None
    def distinct(self,bools=None):
        "用于返回唯一不同的值,配合field方法使用生效,消除所有重复的记录，并只获取唯一一次记录。"
        self.__db.distinct(bools)
        return self
    def deltableall(self):
        "删除当前数据库所有表格 mysql有效"
        if self.conf['type']=='mysql':
            a=self.__db.execute("SELECT concat('DROP TABLE IF EXISTS ', table_name, ';') FROM information_schema.tables WHERE table_schema = 'core1';")
            for k in a:
                self.__db.execute(k["concat('DROP TABLE IF EXISTS ', table_name, ';')"])
        



class dbtype:
    conf=model.config
    def int(LEN=16,DEFAULT=False,NULL=False,UNIQUE=False,PRI=False,A_L=False):
        # print(dbtype.conf['type'])
        if dbtype.conf['type']=='mysql':
            strs="INT("+str(LEN)+")"
            if DEFAULT:
                strs=strs+" DEFAULT "+str(DEFAULT)
            if NULL:
                strs=strs+" NULL"
            else:
                strs=strs+" NOT NULL"
            if UNIQUE:
                strs=strs+" UNIQUE"
            if PRI:
                strs=strs+" PRIMARY KEY"
            if A_L:
                strs=strs+" AUTO_INCREMENT"
        else:
            strs="INTEGER"
            if DEFAULT:
                strs=strs+" DEFAULT "+str(DEFAULT)
            if NULL:
                strs=strs+" NULL"
            else:
                strs=strs+" NOT NULL"
            if UNIQUE:
                strs=strs+" UNIQUE"
            if PRI:
                strs=strs+" PRIMARY KEY"
            if A_L:
                strs=strs+" AUTOINCREMENT"
        return strs
    def varchar(LEN=32,DEFAULT=False,NULL=False,UNIQUE=False,INDEX=False,FULLTEXT=False):
        strs="VARCHAR("+str(LEN)+")"
        if DEFAULT:
            strs=strs+" DEFAULT "+str(DEFAULT)
        elif DEFAULT=='':
            strs=strs+" DEFAULT ''"
        if NULL:
            strs=strs+" NULL"
        else:
            strs=strs+" NOT NULL"
        if UNIQUE:
            strs=strs+" UNIQUE"
        if INDEX:
            strs=strs+" INDEX"
        if FULLTEXT:
            strs=strs+" FULLTEXT"
        return strs
    def text(NULL=False):
        if dbtype.conf['type']=='mysql':
            strs="TEXT CHARACTER SET utf8 COLLATE utf8_general_ci"
        else:
            strs="TEXT"
        if NULL:
            strs=strs+" NULL"
        else:
            strs=strs+" NOT NULL"
        return strs
    def char(LEN=16,DEFAULT=False,NULL=False,UNIQUE=False,INDEX=False):
        strs=" CHAR("+str(LEN)+")"
        if DEFAULT:
            strs=strs+" DEFAULT "+str(DEFAULT)
        elif DEFAULT=='':
            strs=strs+" DEFAULT ''"
        if NULL:
            strs=strs+" NULL"
        else:
            strs=strs+" NOT NULL"
        if UNIQUE:
            strs=strs+" UNIQUE"
        if INDEX:
            strs=strs+" INDEX"
        return strs
    def decimat(LEN="10,2",DEFAULT=False,NULL=False,UNIQUE=False,INDEX=False):
        "小数类型"
        strs="DECIMAL("+str(LEN)+")"
        if DEFAULT:
            strs=strs+" DEFAULT "+str(DEFAULT)
        elif DEFAULT=='':
            strs=strs+" DEFAULT ''"
        if NULL:
            strs=strs+" NULL"
        else:
            strs=strs+" NOT NULL"
        if UNIQUE:
            strs=strs+" UNIQUE"
        if INDEX:
            strs=strs+" INDEX"
        return strs
    def date(NULL=False):
        strs=" DATE"
        if NULL:
            strs=strs+" NULL"
        else:
            strs=strs+" NOT NULL"
        return strs