# -*- coding: utf-8 -*-
from .model import *
import math,random,socket,chardet

kcwebps_path_common=os.path.split(os.path.realpath(__file__))[0]
response.kcwebps_path_common=kcwebps_path_common
if get_sysinfo()['uname'][0]=='Linux':
    config.app['appmode']='produc'
def getSignContent(params):
    "字典排序"
    param={}
    for i in sorted (params) : 
        param[i]=params[i]
    i=0
    strs=""
    for k in param:
        if k:
            if isinstance(k,dict):
                k=json_encode(k)
                k=k.replace('"', '')
                k=k.replace("'", '')
            if param[k]:
                if i==0:
                    strs+=str(k)+"="+str(param[k])
                else:
                    strs+="&"+str(k)+"="+str(param[k])
        i+=1
    return strs
def getsign(params):
    "获取签名"
    if is_index(params,'sign'):
        del params['sign']
    content=getSignContent(params)
    # print(content)
    return md5(content)
def exsignpra(self,params):
    "生成签名参数"
    params['time']=times()
    params['rands']=randoms()
    params['sign']=getsign(params)
    return params
def checksign(params,validity=3600):
    if not is_index(params,'sign') or not is_index(params,'time') or not is_index(params,'rands'):
        return -16,'签名参数错误'
    sign=params['sign']
    del params['sign']
    sjc=times()-int(params['time'])
    if sjc>validity or sjc<-3600:
       return -14,'时间错误，请调整设备时间'
    mysign=getsign(params)
    if sign==mysign:
        return 1,'签名验证成功'
    else:
        if is_index(params,'appkey'):
            params['appkey']='appkey'
        if is_index(params,'paympassword'):
            params['paympassword']='paympassword'
        if is_index(params,'loginpwd'):
            params['loginpwd']='loginpwd'
        content=getSignContent(params)
        return -15,'签名错误，签名内容可参考:md5('+content+')'

def serlogin(username,sign,timestamp,random,types="session"):
    """登录方法
    
    username

    sign

    timestamp

    random

    types 登录类型 session浏览器默认会话登录  否则返回account_token
    """
    account_token=''
    if (times()-int(timestamp))>3600 or times()-int(timestamp)<-3600:
        return False,3,"时间戳错误",account_token
    inifo=sqlite('admin',model_app_path).where([('username','eq',username),'or',('phone','eq',username)]).find()
    if not inifo:
        return False,2,"用户名错误",account_token
    # if inifo['id']>100:
    #     return False,-1,"您不是管理员账号",account_token
    usign=md5(str(inifo['username'])+str(inifo['password'])+str(timestamp)+str(random))
    if usign!=sign:
        return False,2,"密码错误",account_token
    inifo['role']=sqlite("role",model_app_path).where('id',inifo['role']).find()
    if is_index(inifo,'blacklistrole'):
        inifo['blacklistrole']=sqlite("blacklistrole",model_app_path).where('id',inifo['blacklistrole']).find()
    else:
        inifo['blacklistrole']=[]
    sqlite('admin',model_app_path).where('id',inifo['id']).update({'logintime':times()})

    
    #根据权限给当前登录用户初始化菜单
    systemrolelist=[ #系统菜单权限
        {'title':'首页','icon':config.domain['kcwebsimg']+'/icon/home.png','url':'/index/index/index/home',"types":"left","pid":0,"admin_id":inifo['id'],"sort":10000},
        {'title':'管理员','icon':config.domain['kcwebsimg']+'/icon/admin.png','url':'/index/index/admin',"types":"left","pid":0,"admin_id":inifo['id'],"sort":10000},
        {'title':'模块管理','icon':config.domain['kcwebsimg']+'/icon/modular.png','url':'/index/index/modular',"types":"left","pid":0,"admin_id":inifo['id'],"sort":10000},
        {'title':'插件管理','icon':config.domain['kcwebsimg']+'/icon/plug.png','url':'/index/index/plug',"types":"left","pid":0,"admin_id":inifo['id'],"sort":10000},
        {'title':'系统配置','icon':config.domain['kcwebsimg']+'/icon/setup.png','url':'/index/index/setup',"types":"left","pid":0,"admin_id":inifo['id'],"sort":10000}
    ]
    plugmenu=sqlite('plug',model_app_path).select()
    for k in plugmenu: #插件菜单权限
        if not is_index(k,'menu'):
            k['menu']=1
        if k['menu']==1 and k['name']!='index':
            systemrolelist.append({'title':k['title'],'icon':k['icon'],'url':'/'+k['modular']+'/'+k['name'],"types":"left","pid":0,"admin_id":inifo['id'],"sort":1000})
    if inifo['role']:
        rolelist=[]
        if inifo['role']['id']==1: #开拓者权限
            rolelist=systemrolelist
        else:
            for k in systemrolelist:
                for kk in json_decode(inifo['role']['roleroute']):
                    # strs=kk.split("/")
                    # print(k['url'],kk)
                    # if k['url'] in kk:
                    #     rolelist.append(k)
                    if k['url'] in kk:
                        # rolelist.append(k)
                        tttt=True
                        for ttt in rolelist:
                            if ttt['title'] == k['title']:
                                tttt=False
                                break
                        if tttt:
                            rolelist.append(k)
        if len(rolelist):
            urlstr="0"
            for k in systemrolelist:
                urlstr+=",'"+k['url']+"'"
            sqlite("menu",model_app_path).where("admin_id="+str(inifo['id'])+" and url in ("+urlstr+")").delete()
            sqlite("menu",model_app_path).insert(rolelist)
    if types=='session': #如果使用sess登录，要分配系统菜单权限
        set_session("userinfo",inifo)
    else:
        account_token=md5(str(username)+str(inifo['password']))
        set_cache(account_token,inifo,86400)
    G.userinfo=inifo
    return True,0,"登录成功",account_token
def check_role():
    t=request.getroutecomponent()
    ts="/"+t[1]+"/"+t[2]+"/"+t[3]+"/"+t[4]
    if G.userinfo['role']:
        roleroute=json_decode(G.userinfo['role']['roleroute'])
    else:
        roleroute=[]
    if G.userinfo['blacklistrole']:
        blacklistrole=json_decode(G.userinfo['blacklistrole']['roleroute'])
    else:
        blacklistrole=[]
    #判断权限黑名单
    status=True
    for k in blacklistrole:
        if k in ts:
            status=False
            break
    if not status:
        if 'GET' == request.HEADER.Method() and not request.args.get('account_token'):
            return response.tpl("/common/html/error",title="无权访问",content="抱歉...，当前页面被黑名单拦截",imgsrc=config.domain['kcwebsimg']+"/icon/suo.png",status="401 error")
        else:
            return errorjson(msg="该操作被黑名单拦截。\r\n"+ts,status="401")
    if ts != '/index/index/index/index' and ts != '/index/index/index/menu' and G.userinfo['role']['id'] !=1:
        status=False
        for k in roleroute:
            if k in ts:
                status=True
                break
        if not status:
            if 'GET' == request.HEADER.Method() and not request.args.get('account_token'):
                return response.tpl("/common/html/error",title="无权访问",content="抱歉...，您当前没有此页面访问权限，请联系管理员",imgsrc=config.domain['kcwebsimg']+"/icon/suo.png",status="401 error")
            else:
                return errorjson(msg="您没有以下接口访问权限，可联系管理员申请。\r\n"+ts,status="401")
def check_login():
    "检查是否登录"
    if not config.app['cli']:#终端运行时取消登录验证
        G.setadminlog=""
        account_token=request.args.get('account_token')
        if account_token:
            G.userinfo=get_cache(account_token)
            if not G.userinfo:
                return errorjson(code=5,msg='account_token已失效，请重新获取')
        # elif request.args.get('logintype')=='sign':
        #     sign=request.args.get('sign')
        #     timestr=request.args.get('time')
        #     rands=request.args.get('rands')
        #     username=request.args.get('username')
        #     inifo=sqlite('admin',model_app_path).where([('username','eq',username),'or',('phone','eq',username)]).find()
        #     if not inifo:
        #         return errorjson(code=-2,msg='intapp用户名错误')
        #     code,msg=checksign(params={
        #         'sign':sign,'time':timestr,'rands':rands,'username':username,'loginpwd':inifo['password']
        #     })
        #     if code!=1:
        #         return errorjson(code=code,msg=msg)
        else:
            G.userinfo=get_session("userinfo")
            if not G.userinfo:
                if 'GET' == request.HEADER.Method():
                    return response.tpl('/common/html/login')
                else:
                    return errorjson(code=-2,msg='登录失效,请登录后操作')
        return check_role()
def before_request():
    """请求拦截,

    进行登录验证，权限验证
    """
    if request.HEADER.Method()=='OPTIONS':
        return successjson()
    else:
        return check_login()
def after_request(body,status,resheader):
    "响应拦截"
    if status=='200 ok':
        if G.userinfo: #记录操作日志
            method=request.HEADER.Method()
            if method!="GET":
                t=request.getroutecomponent()
                modular=t[1]
                plug=t[2]
                controller=t[3]
                function=t[4]
                routeparam=json_encode(list(t[5]))
                t1=request.HEADER.URL().split("?")
                if len(t1)>1:
                    getparam="?"+t1[1:][0]
                else:
                    getparam=""
                dataparam=request.get_data()
                if dataparam:
                    sqlite("admin_log",model_app_path).insert({
                        "user_id":G.userinfo['id'],
                        "title":G.setadminlog,
                        "method":method,
                        "modular":modular,
                        "plug":plug,
                        "controller":controller,
                        "function":function,
                        "routeparam":routeparam,
                        "getparam":getparam,
                        "dataparam":dataparam,
                        "remote_addr":request.HEADER.Physical_IP(),
                        "addtime":times()
                    })
                G.setadminlog=""
    G.userinfo=None
def return_list(lists,count,pagenow,pagesize):
    """返回分页列表

    lists 数据库列表数据

    count 数据库总数量

    pagenow 页码

    pagesize 每页数量
    """
    if count:
        pagecount=math.ceil(int(count)/int(pagesize))
    else:
        pagecount=0
    data={
        'count':int(count),
        'pagenow':int(pagenow),
        'pagesize':int(pagesize),
        'pagecount':pagecount,
        'lists':lists
    }
    return data
def successjson(data=[],code=0,msg="成功",status='200 ok',cache=False):
    """成功说在浏览器输出包装过的json

        参数 data 结果 默认[]

        参数 code body状态码 默认0

        参数 msg body状态描述 默认 成功

        参数 status http状态码 默认 200

        参数 cache 是否启用浏览器缓存（状态码304缓存）

        返回 json字符串结果集 
        """
    res={
        "code":code,
        "msg":msg,
        "time":int(time.time()),
        "data":data
    }
    return response.json(res,status,response_cache=cache,header={"Access-Control-Allow-Methods":"POT,POST,GET,DELETE,OPTIONS","Access-Control-Allow-Credentials":"true","Content-Type":"text/json; charset=utf-8","Access-Control-Allow-Origin":"*"})
def errorjson(data=[],code=1,msg="失败",status='400 error',cache=False):
    """错误时在浏览器输出包装过的json

    参数 data 结果 默认[]

    参数 code body状态码 默认0

    参数 msg body状态描述 默认 成功

    参数 status http状态码 默认 200

    参数 cache 是否启用浏览器缓存（状态码304缓存）

    返回 json字符串结果集 
    """
    return successjson(data=data,code=code,msg=msg,status=status,cache=cache)
def randoms(lens=6,types=1):
    """生成随机字符串
    
    lens 长度

    types 1数字 2字母 3字母加数字
    """
    strs="0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM,!@#$%^&*()_+=-;',./:<>?"
    if types==1:
        strs="0123456789"
    elif types==2:
        strs="qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    elif types==3:
        strs="0123456789qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    k=''
    i=0
    while i < lens:
        k+=random.choice(strs)
        i+=1
    return k
def set_session(name,value,expire=None):
    "设置session"
    return session.set("app"+str(name),value,expire)
def get_session(name):
    "获取session"
    return session.get("app"+str(name))
def del_session(name):
    "删除session"
    return session.rm("app"+str(name))
def file_get_content(filename,encoding=False):
    """获取文件内容
    
    filename 完整文件名

    encoding 是否返回文件编码  默认否
    """
    fileData=''
    cur_encoding="utf-8"
    if os.path.isfile(filename):
        with open(filename, 'rb') as f:
            cur_encoding = chardet.detect(f.read())['encoding']
        #用获取的编码读取该文件而不是python3默认的utf-8读取。
        with open(filename,encoding=cur_encoding) as file:
            fileData = file.read()
    if encoding:
        return fileData,cur_encoding
    else:
        return fileData
def file_set_content(k,data,encoding="utf-8"):
    f=open(k,'w',encoding=encoding)
    f.write(data)
    f.close()
    return True
class system_start:
    "系统启动项"
    def lists(pagenow=1,pagesize=20,where=None):
        "启动项列表"
        lists=kcwsqlite.sqlite.connect(model_app_path).table("start").where(where).order("id asc").page(pagenow,pagesize).select()
        count=kcwsqlite.sqlite.connect(model_app_path).table("start").where(where).count()
        return lists,count
    def count(where=None):
        "启动项数量"
        return kcwsqlite.sqlite.connect(model_app_path).table("start").where(where).count()
    def insert_Boot_up(cmd,name="系统添加",types="shell",icon="",admin_id=0):
        "添加开机启动命令"
        if types not in ['shell','kcwebps']:
            return False
        if 'Linux' in get_sysinfo()['uname'][0]:
            if kcwsqlite.sqlite.connect(model_app_path).table("start").where("value",cmd).count():
                return False
            if types=='shell':
                insert_system_up(cmd=cmd)
            kcwsqlite.sqlite.connect(model_app_path).table("start").insert({"name":name,"types":types,"value":cmd,"icon":icon,"admin_id":admin_id,"addtime":times(),"updtime":times()})
            return True
        else:
            return False
    def del_Boot_up(cmd,vague=False,id=False):
        """删除开机启动命令
        
        vague 是否模糊匹配 
        """
        if id:
            where=[("id","eq",id)]
        if 'Linux' in get_sysinfo()['uname'][0]:
            del_system_up(cmd=cmd,vague=vague)
            if vague:
                if not id:
                    where=[("value","like","%"+str(cmd)+"%")]
            else:
                if not id:
                    where=[("value","eq",cmd)]
            kcwsqlite.sqlite.connect(model_app_path).table("start").where(where).delete()
            return True
        else:
            return False
g_local_ip=''
def get_local_ip():
    "获取内网ip"
    global g_local_ip
    if g_local_ip:
        return g_local_ip
    try:
        socket_objs = [socket.socket(socket.AF_INET, socket.SOCK_DGRAM)]
        ip_from_ip_port = [(s.connect(("8.8.8.8", 53)), s.getsockname()[0], s.close()) for s in socket_objs][0][1]
        ip_from_host_name = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")][:1]
        g_local_ip = [l for l in (ip_from_ip_port, ip_from_host_name) if l][0]
    except (Exception) as e:
        print("get_local_ip found exception : %s" % e)
    return g_local_ip if("" != g_local_ip and None != g_local_ip) else socket.gethostbyname(socket.gethostname())

def sysisphone():
    "判断是不是手机端访问"
    HTTP_USER_AGENT=request.HEADER.GET()['HTTP_USER_AGENT']
    if "Android" in HTTP_USER_AGENT or 'iPhone' in HTTP_USER_AGENT:
        return True
    else:
        return False

if os.path.isfile("app/common/file/config.conf"):
    kcwebsapidata=json_decode(file_get_content("app/common/file/config.conf"))
    if is_index(kcwebsapidata,'kcwebsapi'):
        if is_index(kcwebsapidata['kcwebsapi'],"host") and  kcwebsapidata['kcwebsapi']['host']:
            config.domain['kcwebsapi']=kcwebsapidata['kcwebsapi']['host']
        if is_index(kcwebsapidata['kcwebsapi'],"filehost") and kcwebsapidata['kcwebsapi']['filehost']:
            config.domain['kcwebsfile']=kcwebsapidata['kcwebsapi']['filehost']
    if is_index(kcwebsapidata['system'],'staticurl') and kcwebsapidata['system']['staticurl']:
        config.domain['kcwebsstatic']=kcwebsapidata['system']['staticurl']
        if config.domain['kcwebsstatic'][-1:]=='/':
            config.domain['kcwebsstatic']=config.domain['kcwebsstatic'][:-1]

def get_kcwebps_folder():
    '获取kcwebps框架目录'
    return (os.path.split(os.path.realpath(__file__))[0][:-7]).replace('\\','/')