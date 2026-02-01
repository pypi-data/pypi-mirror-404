# -*- coding: utf-8 -*-
from .autoload import *
model_intapp_index_path=os.getcwd()+"/app/common/file/sqlite/index_index"
class modelsqliteintapp(model.model):
    config={'type':'sqlite'}
    config={'type':'sqlite','db':model_intapp_index_path}
    model.dbtype.conf=config
class model_intapp_interval(modelsqliteintapp):
    "定时任务"
    table="interval"
    fields={
        "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
        "name":model.dbtype.varchar(LEN=128,DEFAULT=''),        #任务名字
        "types":model.dbtype.varchar(LEN=128,DEFAULT='shell'),  #任务类型
        "cycle":model.dbtype.varchar(LEN=8,DEFAULT=''),         #执行周期
        "value":model.dbtype.varchar(LEN=2056,DEFAULT=''),     #要执行的内容
        "year":model.dbtype.varchar(LEN=32,DEFAULT=''),         #年
        "month":model.dbtype.varchar(LEN=32,DEFAULT=''),        #月
        "day":model.dbtype.varchar(LEN=32,DEFAULT=''),          #日
        "week":model.dbtype.varchar(LEN=32,DEFAULT=''),         #周
        "day_of_week":model.dbtype.varchar(LEN=32,DEFAULT=''),  #周几
        "hour":model.dbtype.varchar(LEN=32,DEFAULT=''),         #时
        "minute":model.dbtype.varchar(LEN=32,DEFAULT=''),       #分
        "second":model.dbtype.varchar(LEN=32,DEFAULT=''),       #秒
        "oss":model.dbtype.varchar(LEN=32,DEFAULT=''),          #是否上传到oss
        "iden":model.dbtype.varchar(LEN=32,DEFAULT=''),         #标识
        "addtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
        "updtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
    }
try:
    sqlite('interval',model_intapp_index_path).find()
except Exception as e:
    if 'no such table: interval' in str(e):
        model_intapp_interval=model_intapp_interval()
        model_intapp_interval.create_table()
    else:
        raise Exception(e)
class model_intapp_pythonrun(modelsqliteintapp):
    "项目运行管理"
    table="pythonrun"
    fields={
        "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
        "icon":model.dbtype.varchar(LEN=128,DEFAULT=''),
        "title":model.dbtype.varchar(LEN=128,DEFAULT=''),
        "descs":model.dbtype.varchar(LEN=512,DEFAULT=''),
        "paths":model.dbtype.varchar(LEN=512,DEFAULT=''),           #项目路径
        "filename":model.dbtype.varchar(LEN=32,DEFAULT=''), #运行文件
        "types":model.dbtype.varchar(LEN=32,DEFAULT=''), 
        "other":model.dbtype.varchar(LEN=512,DEFAULT=''),  
        "addtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
        "updtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
    }
try:
    sqlite('pythonrun',model_intapp_index_path).find()
except Exception as e:
    if 'no such table: pythonrun' in str(e):
        model_intapp_pythonrun=model_intapp_pythonrun()
        model_intapp_pythonrun.create_table()
    else:
        raise Exception(e)
class model_intapp_recorddata(modelsqliteintapp):
    "记录数据"
    table="recorddata"
    fields={
        "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
        "types":model.dbtype.int(LEN=11,DEFAULT=1), #1表示模块安装密码  2表示插件安装密码
        "keys":model.dbtype.varchar(LEN=32,DEFAULT=''), #数据内容
        "text":model.dbtype.varchar(LEN=512,DEFAULT=''), #数据内容
        "addtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
    }
try:
    sqlite('recorddata',model_intapp_index_path).find()
except Exception as e:
    if 'no such table: recorddata' in str(e):
        model_intapp_recorddata=model_intapp_recorddata()
        model_intapp_recorddata.create_table()
    else:
        raise Exception(e)
def sqlite(table=None,configss=model_intapp_index_path):
    """sqlite数据库操作实例
    
    参数 table：表名

    参数 configss 数据库配置  可以传数据库名字符串
    """
    import kcwsqlite
    dbs=kcwsqlite.sqlite
    if table is None:
        return dbs
    elif configss:
        return dbs.connect(configss).table(table)
    else:
        return dbs.connect(config.sqlite).table(table)