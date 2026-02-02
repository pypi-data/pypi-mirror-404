# -*- coding: utf-8 -*-
from .autoload import *
# 初始化数据库
model_app_path=os.getcwd()+"/app/common/file/sqlite/app"
if os.path.exists(os.getcwd()+"/app/common/"):
    class modelsqliteintapp(model.model):
        config={'type':'sqlite'}
        config={'type':'sqlite','db':model_app_path}
        model.dbtype.conf=config
    class model_app_role(modelsqliteintapp):
        "白名单角色"
        table="role" 
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "admin_id":model.dbtype.int(LEN=11,DEFAULT=0),
            "icon":model.dbtype.varchar(LEN=128,DEFAULT=''),        
            "title":model.dbtype.varchar(LEN=128,DEFAULT=''),
            "describes":model.dbtype.varchar(LEN=256,DEFAULT=''),
            "types":model.dbtype.varchar(LEN=8,DEFAULT='user'),
            "roleroute":model.dbtype.varchar(LEN=2048,DEFAULT='[]'),  #所包含的路由（所拥有的权限）
            "updtime":model.dbtype.int(LEN=11,DEFAULT=0),           #登录时间
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
        }
    try:
        sqlite('role',model_app_path).find()
    except:
        model_app_role=model_app_role()
        model_app_role.create_table()
        sqlite("role",model_app_path).insert({"icon":"","admin_id":0,"title":"开拓者","describes":"该角色具备了所有的权限，甚至可以毁灭整个系统","types":"system","roleroute":"[]","updtime":times(),"addtime":times()})
    class model_app_blacklistrole(modelsqliteintapp):
        "黑名单角色"
        table="blacklistrole" 
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "admin_id":model.dbtype.int(LEN=11,DEFAULT=0),
            "icon":model.dbtype.varchar(LEN=128,DEFAULT=''),        
            "title":model.dbtype.varchar(LEN=128,DEFAULT=''),
            "describes":model.dbtype.varchar(LEN=256,DEFAULT=''),
            "types":model.dbtype.varchar(LEN=8,DEFAULT='user'),
            "roleroute":model.dbtype.varchar(LEN=2048,DEFAULT='[]'),  #黑名单路由（限制黑名单的访问权限）
            "updtime":model.dbtype.int(LEN=11,DEFAULT=0),           #登录时间
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
        }
    try:
        sqlite('blacklistrole',model_app_path).find()
    except:
        model_app_blacklistrole=model_app_blacklistrole()
        model_app_blacklistrole.create_table()
    class model_app_admin(modelsqliteintapp):
        "管理员"
        table="admin" 
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "icon":model.dbtype.varchar(LEN=512,DEFAULT=''),
            "username":model.dbtype.varchar(LEN=32,DEFAULT=''),     #用户名
            "password":model.dbtype.varchar(LEN=32,DEFAULT=''),     #登录密码 MD5值
            "phone":model.dbtype.varchar(LEN=11,DEFAULT=''),        #手机
            "nickname":model.dbtype.varchar(LEN=64,DEFAULT=''),     #昵称
            "name":model.dbtype.varchar(LEN=8,DEFAULT=''),          #姓名
            "role":model.dbtype.int(LEN=8,DEFAULT=0),          #白名单角色id
            "blacklistrole":model.dbtype.int(LEN=8,DEFAULT=0), #黑名单角色id
            "logintime":model.dbtype.int(LEN=11,DEFAULT=0),         #登录时间
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
        }
    try:
        t=sqlite('admin',model_app_path).find()
        if t and not is_index(t,'blacklistrole'): #添加字段
            sqlite('admin',model_app_path).execute("ALTER TABLE 'admin' ADD  'blacklistrole' INT NOT NULL DEFAULT '0'")
    except:
        password="111111"
        model_admins=model_app_admin()
        model_admins.create_table()
        sqlite("admin",model_app_path).insert({"username":"kcws","password":md5("kcws"+str(password)),"phone":"","nickname":"kcws-linux控制板","name":"","role":1,'blacklistrole':0,"logintime":times(),"addtime":times()})
    class model_app_admin_log(modelsqliteintapp):
        "管理员操作日志"
        table="admin_log" 
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "user_id":model.dbtype.int(LEN=11,DEFAULT=0),           #用户id（管理员id）
            "title":model.dbtype.varchar(LEN=32,DEFAULT=''),        #日志标题
            "method":model.dbtype.varchar(LEN=8,DEFAULT='GET'),     #请求类型
            "modular":model.dbtype.varchar(LEN=32,DEFAULT=''),      #请求模块
            "plug":model.dbtype.varchar(LEN=32,DEFAULT=''),         #请求插件
            "controller":model.dbtype.varchar(LEN=32,DEFAULT=''),   #请求控制器
            "function":model.dbtype.varchar(LEN=32,DEFAULT=''),     #请求控制器方法
            "routeparam":model.dbtype.varchar(LEN=11,DEFAULT=''),   #路由参数
            "getparam":model.dbtype.varchar(LEN=64,DEFAULT=''),     #GET参数
            "dataparam":model.dbtype.text(),     #body参数
            "remote_addr":model.dbtype.varchar(LEN=64,DEFAULT=''),  #请求物理ip
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0)            #添加时间
        }
    try:
        sqlite('admin_log',model_app_path).find()
    except:
        model_app_admin_log=model_app_admin_log()
        model_app_admin_log.create_table()
    class model_intapp_menu(modelsqliteintapp):
        "顶部和左边菜单 表"
        table="menu" 
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "pid":model.dbtype.int(LEN=11,DEFAULT=0),
            "sort":model.dbtype.int(LEN=11,DEFAULT=0), #排序 降序
            "admin_id":model.dbtype.int(LEN=11,DEFAULT=0),          #所属管理员 0表示所有管理员拥有
            "icon":model.dbtype.varchar(LEN=512,DEFAULT=''),
            "title":model.dbtype.varchar(LEN=32,DEFAULT=''),        #菜单标题
            "url":model.dbtype.varchar(LEN=32,DEFAULT=''),          #菜单地址
            "types":model.dbtype.varchar(LEN=11,DEFAULT=''),    #  left,header
        }
        def add(title,icon,url,types='left',pid=0,admin_id=0,sort=2000):
            "添加菜单"
            if not sqlite('menu',model_app_path).where("url='"+url+"' and admin_id='"+str(admin_id)+"' and types='"+types+"' and pid="+str('pid')).count():
                sqlite('menu',model_app_path).insert({'title':title,'icon':icon,'url':url,"types":types,"pid":pid,"admin_id":admin_id,"sort":sort})
        def delete(id='',title='',types="left",pid=0,admin_id=0,sort=2000):
            "删除菜单"
            if id:
                sqlite('menu',model_app_path).where("id="+str(id)+"").delete()
            elif title and pid:
                sqlite('menu',model_app_path).where("title='"+title+"' and pid="+str(pid)).delete()
            elif title and sort:
                sqlite('menu',model_app_path).where("title='"+title+"' and sort='"+str(sort)+"'").delete()
            elif title and types:
                sqlite('menu',model_app_path).where("title='"+title+"' and types='"+types+"'").delete()
            else:
                sqlite('menu',model_app_path).where("title='"+title+"' and admin_id='"+str(admin_id)+"'").delete()
            

    try:
        sqlite('menu',model_app_path).find()
    except:
        model_intapp_menu=model_intapp_menu()
        model_intapp_menu.create_table()

    class model_intapp_plug(modelsqliteintapp):
        "已安装的插件"
        table="plug"
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "name":model.dbtype.varchar(LEN=256,DEFAULT=''),
            "title":model.dbtype.varchar(LEN=256,DEFAULT=''),
            "describes":model.dbtype.varchar(LEN=1024,DEFAULT=''),
            "edition":model.dbtype.varchar(LEN=32,DEFAULT=''),
            "modular":model.dbtype.varchar(LEN=64,DEFAULT=''),
            "icon":model.dbtype.varchar(LEN=128,DEFAULT=''),
            "role":model.dbtype.text(),
            "menu":model.dbtype.int(LEN=11,DEFAULT=1),
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0)
        }
    try:
        t=sqlite('plug',model_app_path).find()
        if t and not is_index(t,'menu'): #添加字段
            sqlite('plug',model_app_path).execute("ALTER TABLE 'plug' ADD  'menu' INT(11) NOT NULL DEFAULT 1")
    except:
        model_intapp_plug=model_intapp_plug()
        model_intapp_plug.create_table()
        role=[{"name":'首页',"value":'/index/index/index/home'},
            {"name":'导航列表',"value":'/index/index/index/menu'},
            {"name":'系统信息',"value":'/index/index/index/homes'},
            {"name":'磁盘分区',"value":'/index/index/index/disk'},
            {"name":'cpu和内存以及网络',"value":'/index/index/index/cpume'},
            {"name":'进程列表',"value":'/index/index/index/process'},
            {"name":'shell执行能力',"value":'/index/index/index/shell'},
            {"name":'管理员',"value":'/index/index/admin'},
            {"name":'计划任务',"value":'/index/index/plan'},
            {"name":'任务队列',"value":'/index/index/task'},
            {"name":'系统配置',"value":'/index/index/setup'},
            {"name":'模块管理',"value":'/index/index/modular'},
            {"name":'插件管理',"value":'/index/index/plug'},
            {"name":'导航管理',"value":'/index/index/menu'}]
        sqlite('plug',model_app_path).insert({
            "name":"index",
            "title":"intapp容器",
            "describes":'',
            "edition":'0',
            "modular":'intapp',
            "icon":'',
            "role":json_encode(role),
            "addtime":times()
        })

    class model_app_start(modelsqliteintapp):
        "启动项"
        table="start"
        fields={
            "id":model.dbtype.int(LEN=11,PRI=True,A_L=True),        #设置id为自增主键
            "name":model.dbtype.varchar(LEN=128,DEFAULT=''),        #名字
            "icon":model.dbtype.varchar(LEN=128,DEFAULT=''),
            "types":model.dbtype.varchar(LEN=128,DEFAULT='shell'),  #类型
            "value":model.dbtype.varchar(LEN=512,DEFAULT=''),
            "admin_id":model.dbtype.int(LEN=11),
            "updtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
            "addtime":model.dbtype.int(LEN=11,DEFAULT=0),            #添加时间
        }
    try:
        sqlite('start',model_app_path).find()
    except Exception as e:
        model_app_starts=model_app_start()
        model_app_starts.create_table()