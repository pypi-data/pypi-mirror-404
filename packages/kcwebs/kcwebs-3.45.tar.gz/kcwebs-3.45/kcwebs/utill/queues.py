from queue import Queue
from .db import model
import threading,time,os,hashlib,random,traceback,multiprocessing,kcwsqlite
queuesdbpath=os.path.split(os.path.realpath(__file__))[0]+"/Queues"
class model_kcwebs_task(model.model):
    "任务"
    config={'type':'sqlite','db':queuesdbpath}
    model.dbtype.conf=config
    table="model_kcwebs_queues" 
    fields={
        "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
        "taskid":model.dbtype.varchar(LEN=32,DEFAULT=''),        #设置id为自增主键
        "title":model.dbtype.varchar(LEN=1024,DEFAULT=''),      #名称
        "describes":model.dbtype.varchar(LEN=2048,DEFAULT=''),  #描述
        "code":model.dbtype.int(LEN=11,DEFAULT=2),              #状态码 0成功 1失败 2等待中 3正在执行  4完成
        "msg":model.dbtype.text(),                              #状态描述
        "error":model.dbtype.text(),                            #异常信息
        "start":model.dbtype.varchar(LEN=11,DEFAULT=0),             #进度条起始值
        "end":model.dbtype.int(LEN=11,DEFAULT=100),               #进度条结束值
        "starts":model.dbtype.varchar(LEN=11,DEFAULT=0),             #每秒钟进度条起始值增加多少
        "addtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
        "endtime":model.dbtype.int(LEN=11,DEFAULT=0),            #结束时间
        "updtime":model.dbtype.int(LEN=11,DEFAULT=0)            #更新时间
    }
class Queues():
    __globalqueue=None
    __processglobalqueue=None
    def __start():
        if not Queues.__globalqueue:
            if not os.path.isfile(queuesdbpath):
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            try:
                kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").find()
            except:
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            Queues.__globalqueue=Queue()
            t=threading.Thread(target=Queues.__messagequeue,daemon=True)
            t.start()
    __scripttask=None
    __scripttasklist=[]
    def __script():
        if not Queues.__scripttask:
            if not os.path.isfile(queuesdbpath):
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            try:
                kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").find()
            except:
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            Queues.__scripttask=Queue()
            t=threading.Thread(target=Queues.__taskmessagequeue,daemon=True)
            t.start()
            t=threading.Thread(target=Queues.__taskmessagequeue_zx,daemon=True)
            t.start()
    
    def __taskmessagequeue_zx():
        time.sleep(10)
        while True:
            for value in Queues.__scripttasklist:
                try:
                    kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":3,"error":""})
                except:
                    pass
                else:
                    if value['args']:
                        try:
                            value['target'](*value['args'])
                        except:
                            kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                        else:
                            kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
                    else:
                        try:
                            value['target']()
                        except:
                            kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                        else:
                            kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
            time.sleep(1)
    def __taskmessagequeue():
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=2 and updtime<"+str(int(time.time())-86400*7)).delete()
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=3 and updtime<"+str(int(time.time())-1200)).delete()
        while True:
            if not Queues.__scripttask.empty():
                value=Queues.__scripttask.get()
                Queues.__scripttasklist.append(value)
            else:
                time.sleep(0.01)
    def __startprocess():
        if not Queues.__processglobalqueue:
            if not os.path.isfile(queuesdbpath):
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            try:
                kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").find()
            except:
                model_kcwebs_tasks=model_kcwebs_task()
                model_kcwebs_tasks.create_table()
            Queues.__processglobalqueue=multiprocessing.Queue()
            t=multiprocessing.Process(target=Queues._messagequeueprocess,args=(Queues.__processglobalqueue,),daemon=True)
            # t.daemon=True
            t.start()
    def _messagequeueprocess(processglobalqueue):
        """不支持外部调用"""
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=2 and updtime<"+str(int(time.time())-86400*7)).delete()
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=3 and updtime<"+str(int(time.time())-1200)).delete()
        pid = os.getpid()
        pdfile=os.path.split(os.path.realpath(__file__))[0][:-6]+'/pid/queues_pid_'+str(pid) #pid存放文件
        f=open(pdfile,'w')
        f.write(str(pid))
        f.close()
        while True:
            if not processglobalqueue.empty():
                value=processglobalqueue.get()
                kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":3,"error":""})
                if value['args']:
                    try:
                        value['target'](*value['args'])
                    except:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                    else:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
                else:
                    try:
                        value['target']()
                    except:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                    else:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
            else:
                time.sleep(0.01)
    def __messagequeue():
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=2 and updtime<"+str(int(time.time())-86400*7)).delete()
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code=3 and updtime<"+str(int(time.time())-1200)).delete()
        while True:
            if not Queues.__globalqueue.empty():
                value=Queues.__globalqueue.get()
                kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":3,"error":""})
                if value['args']:
                    try:
                        value['target'](*value['args'])
                    except:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                    else:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
                else:
                    try:
                        value['target']()
                    except:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":1,'endtime':int(time.time()),'updtime':int(time.time()),"error":str(traceback.format_exc())})
                    else:
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid = '"+value['task']['taskid']+"' and code!=4").update({"code":4,"start":100,'endtime':int(time.time()),'updtime':int(time.time())})
            else:
                time.sleep(0.01)
    def delhist():
        """清除任务历史记录(包括 成功的 失败的 已完成的)"""
        return kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code","in",0,1,4).delete()
    def delwhere(where):
        "通过where条件删除 (不推荐使用)"
        return kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where(where).delete()
    def seltitle(title):
        "通过标题查询 (不推荐使用)"
        try:
            return kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("title='"+title+"'").select()
        except:
            return ''
    def setfield(taskid,key,value):
        """设置指定字段(不建议使用)"""
        try:
            return kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).update({key:value})
        except:
            return False
    def setstart(taskid,start=0.001,describes=None):
        """增加进度条起始位置
        
        start 支持0.001到10
        """
        if start>=0.001 and start<=10:
            arr=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).find()
            if arr:
                start+=round(float(arr['start']),3)
                if start>=0.01 and start <=99.99:
                    dqsjc=int(time.time())-arr['updtime'] #当前时间差
                    if dqsjc>=1:
                        starts=round(float((float(start)-float(arr['start']))/dqsjc),3)
                        upddate={"start":start,'starts':starts,'updtime':int(time.time())}
                        if describes:
                            upddate['describes']=describes
                        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).update(upddate)
                    return True
                else:
                    return False
            else:
                return False
        else:
            False
    def insert(target,args=None,title="默认任务",describes='',msg='',taskid=None,start=0,updtime=0,types=''): #add_queue
        """添加队列
        
        target 方法名  必须

        args 方法参数 非必须  如 (参数1,参数2)

        title 任务名称

        describes 任务描述

        msg 状态描述

        taskid 任务id

        start 进度条开始位置 （建议1到50）

        updtime 进度条更新时间

        types process表示使用进程执行 否则使用线程执行

        return taskid
        """
        if types=='process':
            Queues.__startprocess()
        else:
            Queues.__start()
        ttt=int(time.time())
        
        end=100
        if not updtime:
            updtime=ttt
        if not taskid:
            m = hashlib.md5()
            m.update((str(ttt)+str(random.randint(100000,999999))).encode(encoding='utf-8'))
            taskid=m.hexdigest()
        else:
            arr=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).find()
            if arr:
                if arr['code'] in [2,3]:
                    return taskid
                else:
                    kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).delete()
        task={"taskid":taskid,"title":title,"describes":describes,"code":2,"msg":msg,"error":"","start":start,"end":end,"addtime":ttt,'starts':0,'endtime':0,'updtime':updtime}
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").insert(task)
        key={"target":target,"args":args,"task":task}
        if types=='process':
            Queues.__processglobalqueue.put(key)
        else:
            Queues.__globalqueue.put(key)
        return taskid
    def inserttask(target,args=None,title="默认任务",msg='',taskid=None,start=0,updtime=0): #add_queue
        """添加后台任务
        
        target 方法名  必须

        args 方法参数 非必须  如 (参数1,参数2)

        title 任务名称

        describes 任务描述

        msg 状态描述

        taskid 任务id

        start 进度条开始位置 （建议1到50）

        updtime 进度条更新时间

        return taskid
        """
        Queues.__script()
        ttt=int(time.time())
        
        end=100
        if not updtime:
            updtime=ttt
        if not taskid:
            m = hashlib.md5()
            m.update((str(ttt)+str(random.randint(100000,999999))).encode(encoding='utf-8'))
            taskid=m.hexdigest()
        else:
            arr=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).find()
            if arr:
                return taskid
        describes='后台任务脚本'
        task={"taskid":taskid,"title":title,"describes":describes,"code":2,"msg":msg,"error":"","start":start,"end":end,"addtime":ttt,'starts':0,'endtime':0,'updtime':updtime}
        kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").insert(task)
        key={"target":target,"args":args,"task":task}
        Queues.__scripttask.put(key)
        return taskid
    def getall(pagenow=1,pagesize=20,where=None):
        """获取全部队列

        code 1获取失败的任务   2获取等待中的任务   3获取正在执行中的任务  4获取执行完成的任务

        return list
        """
        if not os.path.isfile(queuesdbpath):
            model_kcwebs_tasks=model_kcwebs_task()
            model_kcwebs_tasks.create_table()
        try:
            lists=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).where(where).table("model_kcwebs_queues").order("id desc").page(pagenow,pagesize).select()
            count=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).where(where).table("model_kcwebs_queues").count()
            return lists,count
        except:
            model_kcwebs_tasks=model_kcwebs_task()
            model_kcwebs_tasks.create_table()
            return [],0
    def status(taskid):
        """获取任务状态
        
        taskid  任务id

        return dict
        """
        arr=kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("taskid",taskid).find()
        if arr:
            arr['start']=float(arr['start'])
            dqsjc=arr['updtime']-arr['addtime']
            if dqsjc and arr['start']>=1:
                arr['starts']=round(float(arr['start'])/dqsjc,3)
            else:
                try:
                    arr['starts']=round(float(arr['starts']),3)
                except:
                    arr['starts']=0
        return arr
    def iscomplete():
        """判断对列中的任务是否全部执行完成
        
        return Boolean
        """
        if kcwsqlite.sqlite.connect(queuesdbpath,th_lock=True).table("model_kcwebs_queues").where("code","in",2,3).count():
            return True
        else:
            return False
