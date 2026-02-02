from .common import *
dqpath=os.path.split(os.path.realpath(__file__))[0]
# def customizeProcess(data):
#     pid=os.getpid()
#     set_cache(md5(data['paths']+data['other']),pid,0)
#     os.system("cd "+data['paths']+" && "+data['other'])
from .run_script import getinterpreter,run_script_delpid,run_script_getpid
def getinterpreter(paths,types,filename,other):
    from .run_script import getinterpreter
    return getinterpreter(paths,types,filename,other)


class setup:
    def index():
        return response.tpl(dqpath+'/tpl/setup/index.html',absolutelypath=True)
    def basepage():
        "基本配置"
        return response.tpl(dqpath+'/tpl/setup/basepage.html',absolutelypath=True)
    def startpage():
        "开机启动项"
        return response.tpl(dqpath+'/tpl/setup/startpage.html',absolutelypath=True)
    def bacrecpage():
        "备份恢复页面"
        return response.tpl(dqpath+'/tpl/setup/bacrecpage.html',absolutelypath=True)
    def pythonrun():
        "项目管理器"
        response.yunpath=os.getcwd()
        return response.tpl(dqpath+'/tpl/setup/pythonrun.html',absolutelypath=True)
    def getbanddomain():
        G.setadminlog="获取绑定域名"
        status,webitem=kcwebpsdomain.getbanddomain()
        if status:
            return successjson(webitem)
        else:
            return errorjson(msg=webitem)
    def banddomainall():
        G.setadminlog="绑定域名"
        domain=request.get_json()['domain']
        proxy_pass=request.get_json()['proxy_pass']
        client_max_body_size=request.get_json()['client_max_body_size']
        read_timeout=request.get_json()['read_timeout']
        status,msg=kcwebpsdomain.banddomainall(domain=domain,proxy_pass=proxy_pass,read_timeout=read_timeout)
        if status:
            return successjson()
        else:
            return errorjson(msg=msg)
    def delbanddomain():
        G.setadminlog="删除绑定域名"
        status,msg=kcwebpsdomain.delbnddomain()
        if status:
            return successjson()
        else:
            return errorjson(msg=msg)
    def restart(types='stop'):
        "启动/停止项目管理"
        G.setadminlog="启动/停止项目管理"
        data=request.get_json()
        if types=='start':
            os.system(data['cmd'])
            for ds in range(60):
                time.sleep(0.5)
                pid=run_script_getpid(data['id'])
                if get_pid_info(pid):
                    break
            return successjson()
        elif types=='stop':
            pid=run_script_getpid(data['id'])
            if not kill_pid(pid):
                return errorjson('停止失败')
            run_script_delpid(data['id'])
        return successjson()
        
    def get_cli_info():
        data=request.get_json()
        if data['types']=='kcwebps':
            # return successjson(get_pid_info(run_script_getpid(data['id']),types='info'))
            pid=get_kcws_cli_pid(data['other'])
            if pid:
                pid=int(pid)
                p = psutil.Process(pid)
                memory = psutil.virtual_memory()
                info={
                    'pid':pid,
                    'name':p.name(),
                    'cli':p.cmdline(),
                    'cpu':p.cpu_percent(1),
                    'memory':p.memory_info().rss,
                    'allmemory':memory.total
                }
                info['usememorys']=int(info['memory']/info['allmemory']*100)
            else:
                info={}
            # return successjson(get_kcws_cli_info(data['other'],types='info'))
            return successjson(info)
        else:
            info={}
            interpreter=data['interpreter']
            memory = psutil.virtual_memory()
            for proc in psutil.process_iter(['name']):
                try:
                    if interpreter in proc.info['name']:
                        info={
                            'pid':proc.pid,'name':proc.name(),'cpu':proc.cpu_percent(),'memory':proc.memory_info().rss,'allmemory':memory.total
                        }
                        info['usememorys']=int(info['memory']/info['allmemory']*100)
                        break
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    pass
            return successjson(info)
            # return successjson(get_pid_info(run_script_getpid(data['id']),types='info'))
    def setpythonrun():
        "设置/添加项目管理"
        G.setadminlog="设置/添加项目管理"
        data=request.get_json()
        try:del data['interpreter']
        except:pass
        try:del data['info']
        except:pass
        try:del data['cmd']
        except:pass
        try:del data['process']
        except:pass
        try:del data['status']
        except:pass
        
        if data['types']=='kcwebps':
            if 'Linux' in get_sysinfo()['platform'] or 'Windows' in get_sysinfo()['platform']:
                pass
            else:
                return errorjson(msg="不支持该系统")
            paths=os.getcwd().replace('\\','/')
            if not data['other']:
                return errorjson(msg='kcwebps项目路由地址不能为空')
            data['other']=data['other'].replace(' ','')
            if data['other'][0:6]=='server':
                return errorjson(msg='不支持该路由参数')
            if data['id']:
                if sqlite("pythonrun").where("id!='"+str(data['id'])+"' and types='"+data['types']+"' and other='"+data['other']+"'").count():
                    return errorjson(msg='该路由地址已存在')
            else:
                if sqlite("pythonrun").where("types='"+data['types']+"' and other='"+data['other']+"'").count():
                    return errorjson(msg='该路由地址已存在')
            if not  os.path.exists(paths+"/app/runtime/log/"):
                os.makedirs(paths+"/app/runtime/log/", exist_ok=True)
            if data['id']:
                data.update(updtime=times(),addtime=times())
             
                sqlite("pythonrun").where("id",data['id']).update(data)
            else:
                del data['id']
                data.update(updtime=times(),addtime=times())
                sqlite("pythonrun").insert(data)
            return successjson()
        elif data['types']=='customize':
            if not data['paths']:
                return errorjson(msg='请选择运行目录')
            if not data['other']:
                return errorjson(msg='请输入命令')
            if data['id']:
                data.update(updtime=times(),addtime=times())
         
                sqlite("pythonrun").where("id",data['id']).update(data)
            else:
                del data['id']
                data.update(updtime=times(),addtime=times())
                sqlite("pythonrun").insert(data)
            return successjson()
        elif 'Linux' in get_sysinfo()['platform']:
            ttt,interpreter=getinterpreter(data['paths'],data['types'],data['filename'],data['other']) #解释器
            if not ttt:
                return errorjson(msg=interpreter)
      
            if data['id']:
                arr=sqlite("pythonrun").where("id",data['id']).find()
                ttt,interpreterj=getinterpreter(arr['paths'],arr['types'],arr['filename'],arr['other']) #解释器
                if interpreterj!=interpreter:#删除之前的
                    pid=run_script_getpid(data['id'])
                    kill_pid(pid)
                    run_script_delpid(data['id'])
                    try:
                        os.remove("/usr/bin/"+interpreterj)
                    except:pass
           
                data.update(updtime=times(),addtime=times())
                
                sqlite("pythonrun").where("id",data['id']).update(data)
                return successjson()
            else:
                del data['id']
                data.update(updtime=times(),addtime=times())
                sqlite("pythonrun").insert(data)
                return successjson()
        else:
            return errorjson(msg="不支持该系统，当前只支持linux")
    def logpythonrun(id):
        "项目管理日志"
        G.setadminlog="项目管理日志"
        data=sqlite("pythonrun").where('id',id).find()
        paths=os.getcwd().replace('\\','/')
        logpath=paths+"/app/runtime/log/"
        logname=logpath+md5(data['other'])+'.log'
        if data['types'] not in ['customize','kcwebps']:
            logpath=data['paths']+"/app/runtime/log/"
            ttt,interpreter=getinterpreter(data['paths'],data['types'],data['filename'],data['other'])
            logname=logpath+md5(interpreter+data['other'])+'.log'

        f=open(logname)
        data=f.read()
        f.close()
        return successjson(data)
    def delpythonrun(id=''):
        "删除项目管理"
        G.setadminlog="删除项目管理"
        if id:
            id=[id]
        else:
            id=request.get_json()
        arr=sqlite("pythonrun").where('id','in',id).field("id,paths,types,filename,other,descs").select()
        for k in arr:
            descs=k['descs']
            daemon=''
            if descs=='daemon':
                daemon='1'
            if k['types']=='kcwebps':
                pid=run_script_getpid(k['id'])
                kill_pid(pid)
                run_script_delpid(k['id'])
            elif k['types']=='customize':
                pid=run_script_getpid(k['id'])
                kill_pid(pid)
                run_script_delpid(k['id'])
            else:
                ttt,interpreter=getinterpreter(k['paths'],k['types'],k['filename'],k['other']) #解释器
                os.system("pkill -9 "+interpreter[:12])
                if os.path.isfile("/usr/bin/"+interpreter):
                    os.remove("/usr/bin/"+interpreter)
                pid=run_script_getpid(k['id'])
                kill_pid(pid)
                run_script_delpid(k['id'])
        sqlite("pythonrun").where('id','in',id).delete()
   
        return successjson()
    def pythonrulistsss(kw='',pagenow=1,pagesize=20):
        where=None
        if kw:
            where=[("title","like","%"+str(kw)+"%"),'or',("descs","like","%"+str(kw)+"%")]
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        paths=os.getcwd().replace('\\','/')
        logpath=paths+"/app/runtime/log/"
        
        
        lists=sqlite("pythonrun").where(where).page(pagenow,pagesize).select()
        current_script=os.path.dirname(os.path.abspath(__file__))+"/run_script.py"
        for k in lists:
            descs=k['descs']
            daemon='0'
            if descs=='daemon':
                daemon='1'
            logname=logpath+md5(k['other'])+'.log'
            if k['types'] not in ['customize','kcwebps']:
                logpath=k['paths']+"/app/runtime/log/"
                ttt,interpreter=getinterpreter(k['paths'],k['types'],k['filename'],k['other'])
                logname=logpath+md5(interpreter+k['other'])+'.log'
            if not os.path.exists(logpath):
                os.makedirs(logpath, exist_ok=True)
            if 'Linux' in get_sysinfo()['platform']:
                k['cmd']='nohup python3.8 '+current_script+' '+str(k['id'])+' '+paths+' '+daemon+'  > '+logname+' 2>&1 &'
            elif 'Windows' in get_sysinfo()['platform']:
                k['cmd']='start /b  python '+current_script+' '+str(k['id'])+' '+paths+' '+daemon
            else:
                return errorjson(msg="不支持该系统")
            pid=run_script_getpid(k['id'])
            if get_pid_info(pid):
                k['status']=1 #运行中
            else:
                k['status']=0 #已停止
                run_script_delpid(k['id'])
            if k['types']=='kcwebps':
                k['interpreter']='kcwebps'
            elif k['types']=='customize':
                k['interpreter']=''
            else:
                ttt,interpreter=getinterpreter(k['paths'],k['types'],k['filename'],k['other']) #解释器
                k['interpreter']=interpreter
        count=sqlite("pythonrun").where(where).count()
        data=return_list(lists,count,pagenow,pagesize)
        return data
    def pythonrulists(id=''):
        "项目管理列表"
        if id:
            return successjson(sqlite("pythonrun").find(id))
        kw=request.args.get('kw')
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        data=setup.pythonrulistsss(kw=kw,pagenow=pagenow,pagesize=pagesize)
        return successjson(data)
    def setbaseconfig(types='get'):
        "保存配置信息"
        if types=='get':
            return successjson(getbaseconfig())
        else:
            G.setadminlog="保存配置信息"
            getbaseconfig(types=types,config=request.get_json())
            return successjson(msg="保存成功")

    def addstart():
        "添加启动项"
        G.setadminlog="添加启动项"
        data=request.get_json()
        if kcwsqlite.sqlite.connect(model_app_path).table("start").where("value",data['value']).count():
            return errorjson(msg="禁止重复添加")
        try:
            icon=data['icon']
        except:
            icon=''
        if system_start.insert_Boot_up(cmd=data['value'],name=data['name'],types=data['types'],admin_id=G.userinfo['id'],icon=icon):
            return successjson()
        else:
            return errorjson(msg="添加失败，该系统支不支持")
    def delstart():
        G.setadminlog="删除启动项"
        data=request.get_json()
        if system_start.del_Boot_up(cmd=data['value'],id=data['id']):
            return successjson()
        else:
            return errorjson()
    def startlist():
        "启动项列表"
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=100
        else:
            pagesize=int(pagesize)
        yz=system_start.lists(pagenow,pagesize)
        lists=yz[0]
        count=yz[1]
        data=return_list(lists,count,pagenow,pagesize)
        
        return successjson(data)

    def aliyunosslist(types='app'):
        import oss2
        if not os.path.isfile("app/common/file/config.conf"):
            return errorjson(msg="请先配置阿里云oss配置信息")
        data=json_decode(file_get_content("app/common/file/config.conf"))
        prefix=request.args.get("prefix")
        if not prefix:
            if types=='app':
                prefix="backups/"+data['aliyun']['backpath']+"/app/"
            else:
                prefix="backups/"+data['aliyun']['backpath']+"/backup/mysql/"
        data=[]
        try:
            fileconfig=json_decode(file_get_content("app/common/file/config.conf"))
            auth = oss2.Auth(fileconfig['aliyun']['access_key'],fileconfig['aliyun']['access_key_secret'])
            bucket = oss2.Bucket(auth,fileconfig['aliyun']['address'],fileconfig['aliyun']['bucket'])
            # 列举fun文件夹下的文件与子文件夹名称，不列举子文件夹下的文件。
            
            for obj in oss2.ObjectIterator(bucket, prefix = prefix, delimiter = '/'):
                # 通过is_prefix方法判断obj是否为文件夹。
                if obj.is_prefix():  # 文件夹
                    data.insert(0,{"name":obj.key.split("/")[-2],"path":obj.key,"type":"folder"})
                else:                # 文件
                    data.insert(0,{"name":obj.key.split("/")[-1],"path":obj.key,"type":"file"})
        except:pass
        # data1=[]
        # i=len(data)
        # while True:
        #     i+=1
        #     if i<0:
        #         break
        #     else:
        #         data1.append(data[i])
        return successjson(data)
    def aliyunossdownload(types=""):
        "从阿里云备份点恢复"
        import oss2
        if not os.path.isfile("app/common/file/config.conf"):
            return errorjson(msg="请先配置阿里云oss配置信息")
        fileconfig=json_decode(file_get_content("app/common/file/config.conf"))
        auth = oss2.Auth(fileconfig['aliyun']['access_key'],fileconfig['aliyun']['access_key_secret'])
        bucket = oss2.Bucket(auth,fileconfig['aliyun']['address'],fileconfig['aliyun']['bucket'])
        filepath=request.args.get("filepath")
        if types=='mysql': #恢复mysql
            pass
        else: #恢复文稿
            bucket.get_object_to_file(filepath, "backup.zip")
            kcwebszip.unzip_file("backup.zip","backup/app")
            os.remove("backup.zip")
            if os.path.exists("backup/app"):
                filelist=get_file("backup/app")
                for k in filelist:
                    if k['type']=='folder' and '__pycache__' not in k['path']:
                        if 'common/file' == k['path'][-11:]:
                            path=re.sub("backup/","",k['path'])
                            if os.path.exists(path):
                                shutil.rmtree(path)
                            shutil.copytree(k['path'],path)
        return successjson()
    def backup(types=''):
        "备份全部"
        import oss2
        G.setadminlog="备份全部"
        paths=request.args.get("paths")
        if paths: #备份目录  app/common/file
            shutil.copytree(paths,"backup/"+paths)
        else: #备份全部
            filelist=get_file("app")
            if os.path.exists("backup"):
                shutil.rmtree("backup")
            for k in filelist:
                if k['type']=='folder' and '__pycache__' not in k['path']:
                    if 'common/file' == k['path'][-11:]:
                        shutil.copytree(k['path'],"backup/"+k['path'])
                        # print(k['path'],"backup/"+k['path'])
        if types=='aliyun':#备份文件上传到阿里云oss
            if not os.path.isfile("app/common/file/config.conf"):
                print("您没有保存阿里云oss修改配置信息而无法上传")
            else:
                fileconfig=json_decode(file_get_content("app/common/file/config.conf"))
                backpath=fileconfig['aliyun']['backpath']
                if backpath:
                    if backpath[:1]=='/':
                        backpath=backpath[1:]
                    if backpath[-1]=='/':
                        backpath=backpath[:-1]
                else:
                    backpath="kcwebs"
                auth = oss2.Auth(fileconfig['aliyun']['access_key'],fileconfig['aliyun']['access_key_secret'])
                bucket = oss2.Bucket(auth,fileconfig['aliyun']['address'],fileconfig['aliyun']['bucket'])
                kcwebszip.packzip("backup/app","backup/app.zip")
                oss2.resumable_upload(bucket,"backups/"+backpath+"/app/"+time.strftime("%Y%m%d-%H:%M:%S",time.localtime(times()))+".zip","backup/app.zip")
                filelist=[]
                for obj in oss2.ObjectIterator(bucket, prefix="backups/"+backpath+"/app/"):
                    filelist.append(obj.key)
                i=0
                while True:
                    if len(filelist)-i <= 30: #在阿里云保留30个备份文件
                        break
                    bucket.delete_object(filelist[i])
                    i+=1
                os.remove("backup/app.zip")
                print("上传到阿里云oss成功")
        if not config.app['cli']:
            return successjson(msg="所有文稿备份成功")
    def recovery():
        "恢复文稿"
        G.setadminlog="恢复文稿"
        paths=request.args.get("paths")
        if paths: #恢复指定目录 app/common/file
            shutil.copytree("backup/"+paths,paths)
        elif os.path.exists("backup/app"): #恢复全部文稿
            filelist=get_file("backup/app")
            for k in filelist:
                if k['type']=='folder' and '__pycache__' not in k['path']:
                    if 'common/file' == k['path'][-11:]:
                        path=re.sub("backup/","",k['path'])
                        if os.path.exists(path):
                            shutil.rmtree(path)
                        shutil.copytree(k['path'],path)
                        print(k['path'],path)
            return successjson(msg="所有文稿恢复成功")
        else:
            return errorjson(msg="备份目录不存在")
    def download(name=""):
        "下载备份文件"
        G.setadminlog="下载备份文件"
        if os.path.exists("backup"):
            kcwebszip.packzip("backup","backup.zip")
            f=open("backup.zip","rb")
            body=f.read()
            f.close()
            os.remove("backup.zip")
            return body,"200 ok",{"Content-Type":"application/zip","Accept-Ranges":"bytes"}
        else:
            return "没有备份文件，请备份文件后再下载"
    def postsup():
        "上传备份文件"
        G.setadminlog="上传备份文件"
        if request.binary.save('file',"backup."+request.binary.filesuffix('file')):
            kcwebszip.unzip_file("backup.zip","backup")
            os.remove("backup.zip")
            return successjson()
        else:
            return errorjson(msg="上传失败")
    def dowfile(name=''):
        "下载指定文件"
        G.setadminlog="下载指定文件"
        pathname=request.args.get("pathname")
        return response.download(pathname)
    def uploadfile():
        "上传文件导指定目录"
        G.setadminlog="上传文件导指定目录"
        pathname=request.args.get("pathname")
        if request.binary.save('file',pathname):
            return successjson()
        else:
            return errorjson(msg="上传失败")
    def backxz(name=''):
        "压缩指定文件夹并下载"
        G.setadminlog="压缩指定文件夹并下载"
        paths=request.args.get("paths")
        kcwebszip.packzip(paths,"backxz.zip")
        f=open("backxz.zip","rb")
        body=f.read()
        f.close()
        os.remove("backxz.zip")
        return body,"200 ok",{"Content-Type":"application/zip","Accept-Ranges":"bytes"}
    def upunback():
        "上传zip压缩包并解压指定文件夹"
        G.setadminlog="上传zip压缩包并解压指定文件夹"
        paths=request.args.get("paths")
        if request.binary.save('file',"backxz."+request.binary.filesuffix('file')):
            try:
                kcwebszip.unzip_file("backxz.zip",paths)
                os.remove("backxz.zip")
            except:
                return errorjson(msg="文件格式错误")
            return successjson()
        else:
            return errorjson(msg="上传失败")
        return successjson()
