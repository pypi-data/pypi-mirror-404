from .common import *
kcwebsuserinfopath=os.path.split(os.path.realpath(__file__))[0]+"/common/file/"
dqpath=os.path.split(os.path.realpath(__file__))[0]
class plug:
    def index(modular="intapp",kw=''):
        lefttext=request.args.get('lefttext')
        if not lefttext:
            lefttext='应用'
        lefturl=request.args.get('lefturl')
        if not lefturl:
            lefturl='myapp'
        lefttype=request.args.get('lefttype')
        if not lefttype:
            lefttype=''
        response.platform=get_sysinfo()['platform']
        response.modular=modular
        response.kw=kw
        return response.tpl(dqpath+'/tpl/plug/index.html',absolutelypath=True)
    def getpluglist(modular="intapp"):
        "本地插件列表"
        path="app/"+modular+"/controller/"
        lis=os.listdir(path)
        lists=[]
        for k in lis:
            if not os.path.isfile(path+k) and '__' not in k:
                lists.append(k)
        data=sqlite('plug',model_app_path).select()
        i=0
        for k in data:
            if k['name'] not in lists:
                del data[i]
            i+=1
        return successjson(data)
    def plug_list(modular="intapp",pagenow=1,group=''):
        "云插件列表"
        kw=request.args.get("kw")
        if not kw:
            kw=''
        plug=sqlite('plug',model_app_path).select()
        http=Http()
        http.openurl(config.domain['kcwebsapi']+"/pub/plug_list?modular="+modular+"&pagenow="+pagenow+"&group="+group+"&kw="+kw)
        res=json_decode(http.get_text)
        del http
        lists=res['data']['lists']
        for k in lists:
            k['status']=0 #0未安装  1已安装  2安装中 3卸载中 4不可以安装 5可更新
            # if os.path.exists("app/intapp/controller/"+str(k['name'])):
            #     k['status']=1
            if not os.path.exists("app/"+k['modular']):
                k['status']=4
            else:
                for kk in plug:
                    if k['name']==kk['name'] and k['modular']==kk['modular']:
                        k['status']=1
                        kk['status']=1
                        if k['edition'] and float(k['edition'][0]) > float(kk['edition']):
                            k['status']=5
                            kk['status']=5
        if os.path.isfile(kcwebsuserinfopath+str(G.userinfo['id'])):
            kcwebsuserinfo=file_get_content(kcwebsuserinfopath+str(G.userinfo['id']))
        else:
            kcwebsuserinfo={}
        if kcwebsuserinfo:
            res['kcwebsuserinfo']=json_decode(kcwebsuserinfo)
        else:
            res['kcwebsuserinfo']=''
        for k in plug:
            k['icon']=k['icon'].replace("https://img.kwebapp.cn",config.domain['kcwebsimg'])
        res['plug']=plug
        return response.json(res)

    def uploadplug():
        "打包插件上传"
        G.setadminlog="打包插件上传"
        kcwebsuserinfo=file_get_content(kcwebsuserinfopath+str(G.userinfo['id']))
        if kcwebsuserinfo:
            kcwebsuserinfo=json_decode(kcwebsuserinfo)
            data=request.get_json()
            if data['name']=='index' and data['modular']=='intapp':
                tpaths=os.path.split(os.path.realpath(__file__))[0]+"/common/file"
                lis=os.listdir(os.path.split(os.path.realpath(__file__))[0]+"/common/file")
                for files in lis:
                    if os.path.isfile(tpaths+"/"+files):
                        os.remove(tpaths+"/"+files)
            server=create("app",data['modular'])
            data1=server.packplug(data['name'])
            if data1[0]:
                data1=server.uploadplug(data['name'],kcwebsuserinfo['username'],kcwebsuserinfo['password'])
                if data1[0]:
                    return successjson()
                else:
                    return errorjson(msg=data1[1])
            return errorjson(msg=data1[1])
        else:
            return errorjson(msg="请先配置kcwebs账号")
    #临时增加
    t=sqlite('plug',model_app_path).find()
    if t and not is_index(t,'menu'): #添加字段
        sqlite('plug',model_app_path).execute("ALTER TABLE 'plug' ADD  'menu' INT(11) NOT NULL DEFAULT 1")
    def installplug():
        "安装或更新插件"
        G.setadminlog="安装或更新插件"
        arr=request.get_json()
        # print('arr',arr)
        #备份插件文稿数据
        dirname="app/"+arr['modular']+"/controller/"+arr['name']+"/common/file"
        if os.path.exists(dirname):
            if not os.path.exists("backup/"+dirname):
                os.makedirs("backup/"+dirname)
            kcwebszip.packzip(dirname,"backup/"+dirname+"/backup.zip")
            file_set_content("backup/"+dirname+"/time",str(times()))
            
        
        server=create("app",arr['modular'])
        keys=md5(arr['modular']+arr['name'])
        token=''
        t=sqlite('recorddata',model_intapp_index_path).where('keys',keys).find()
        if t and t['text']:
            token=t['text']
        if arr['token']:
            token=arr['token']
        # print('token',token)
        data=server.installplug(arr['name'],arr['edition'],token,mandatory=True)
        if data[0]:
            sqlite('plug',model_app_path).where("name='"+arr['name']+"' and modular='"+arr['modular']+"'").delete()
            role=[]
            if os.path.isfile("app/"+arr['modular']+"/controller/"+arr['name']+"/role.txt"):
                f=open("app/"+arr['modular']+"/controller/"+arr['name']+"/role.txt",encoding="utf-8")
                while True:
                    line = f.readline()
                    if not line:
                        break
                    elif len(line) > 3 and ',' in line and '/' in line:
                        line=line.split(",")
                        role.append({"name":line[0],"value":re.sub("\t","",re.sub("\r","",re.sub("\n","",line[1])))})
                f.close()
            # status=False
            # for k in role:
            #     if k['value']==arr['modular']+"/"+arr['name']:
            #         status=True
            # if not status:
            #     role.append({"name":arr['title'],"value":arr['modular']+"/"+arr['name']})
            if not role:
                role.append({"name":arr['title'],"value":arr['modular']+"/"+arr['name']})
            sqlite('plug',model_app_path).insert({
                "name":arr['name'],
                "title":arr['title'],
                "describes":arr['describes'],
                "edition":arr['edition'],
                "modular":arr['modular'],
                "icon":arr['icon'],
                "role":json_encode(role),
                'menu':arr['menu'],
                "addtime":times()
            })
            #恢复文稿数据
            if os.path.isfile("backup/"+dirname+"/backup.zip"):
                kcwebszip.unzip_file("backup/"+dirname+"/backup.zip",dirname)
            if not t:
                sqlite('recorddata',model_intapp_index_path).insert({'types':2,'keys':keys,'text':token,'addtime':times()})
            return successjson()
        else:
            if '授权码错误' in data[1]:
                if t:
                    sqlite('recorddata',model_intapp_index_path).where('keys',keys).delete()
                return successjson(code=1,msg='授权码错误')
            else:
                return errorjson(msg=data[1],data=data)

    def uninstallplug():
        "卸载插件"
        G.setadminlog="卸载插件"
        arr=request.get_json()
        #备份插件文稿数据
        dirname="app/"+arr['modular']+"/controller/"+arr['name']+"/common/file"
        if not os.path.exists("backup/"+dirname):
            os.makedirs("backup/"+dirname)
        kcwebszip.packzip(dirname,"backup/"+dirname+"/backup.zip")
        file_set_content("backup/"+dirname+"/time",str(times()))
            
        sqlite("menu",model_app_path).where("url='/"+arr['modular']+'/'+arr['name']+"'").delete()
        sqlite('plug',model_app_path).where("name='"+arr['name']+"' and modular='"+arr['modular']+"'").delete()
        server=create("app",arr['modular'])
        data=server.uninstallplug(arr['name'])
        if data[0]:
            return successjson()
        else:
            return errorjson(msg=data[1])