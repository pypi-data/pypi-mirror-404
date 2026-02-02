from .common import *
dqpath=os.path.split(os.path.realpath(__file__))[0]
kcwebps_default_role={
    'id':0,
    'name':'index',
    'title':'kcwebps',
    'describes':'kcwebps默认',
    'edition':'1',
    'modular':'https://img.kwebapp.cn/icon/folder.png',
    'role':[
        {"name": "首页", "value": "/index/index/index/home"},
        {"name": "获取当前登录用户信息", "value": "/index/index/index/getuser"},
        {"name": "导航列表", "value": "/index/index/index/menu"},
        {"name": "系统信息", "value": "/index/index/index/homes"},
        {"name": "磁盘分区", "value": "/index/index/index/disk"},
        {"name": "cpu和内存以及网络", "value": "/index/index/index/cpume"},
        {"name": "进程列表", "value": "/index/index/index/process"},
        {"name": "shell执行能力", "value": "/index/index/index/shell"},
        {"name": "重启", "value": "/index/index/index/reboot"},
        {"name": "管理员入口", "value": "/index/index/admin/index"},
        {"name": "管理员页面", "value": "/index/index/admin/admin"},
        {"name": "权限页面", "value": "/index/index/admin/role"},
        {"name": "操作日志页面", "value": "/index/index/admin/adminlog"},
        {"name": "日志列表", "value": "/index/index/admin/loglist"},
        {"name": "日志明细", "value": "/index/index/admin/logdeta"},
        {"name": "清空日志", "value": "/index/index/admin/deletelogs"},
        {"name": "删除30天前的日志", "value": "/index/index/admin/deletelog30"},
        {"name": "路由列表", "value": "/index/index/admin/getpluglist"},
        {"name": "当前用户拥有的权限", "value": "/index/index/admin/getmypluglist"},
        {"name": "管理员列表", "value": "/index/index/admin/getlist"},
        {"name": "添加管理员", "value": "/index/index/admin/insert"},
        {"name": "删除管理员", "value": "/index/index/admin/delete"},
        {"name": "编辑管理员", "value": "/index/index/admin/update"},
        {"name": "设置管理员密码", "value": "/index/index/admin/setpwd"},
        {"name": "设置自己的密码", "value": "/index/index/admin/setmypwd"},
        {"name": "角色列表", "value": "/index/index/admin/getrolelist"},
        {"name": "添加角色", "value": "/index/index/admin/insertrole"},
        {"name": "更新角色", "value": "/index/index/admin/updaterole"},
        {"name": "删除角色", "value": "/index/index/admin/deleterole"},
        {"name": "退出所有会话", "value": "/index/index/admin/dellogin"},
        {"name": "导航页面", "value": "/index/index/menu/index"},
        {"name": "导航列表", "value": "/index/index/menu/menulist"},
        {"name": "编辑导航", "value": "/index/index/menu/menuupdate"},
        {"name": "删除导航", "value": "/index/index/menu/menudelete"},
        {"name": "添加导航", "value": "/index/index/menu/menuinsert"},
        {"name": "模块页面", "value": "/index/index/modular/index"},
        {"name": "模块列表", "value": "/index/index/modular/modular_list"},
        {"name": "安装模块", "value": "/index/index/modular/installmodular"},
        {"name": "卸载模块", "value": "/index/index/modular/uninstallmodular"},
        {"name": "插件页面", "value": "/index/index/plug/index"},
        {"name": "插件列表", "value": "/index/index/plug/getpluglist"},
        {"name": "云插件列表", "value": "/index/index/plug/plug_list"},
        {"name": "安装更新插件", "value": "/index/index/plug/installplug"},
        {"name": "卸载插件", "value": "/index/index/plug/uninstallplug"},
        {"name": "计划页面", "value": "/index/index/plan/index"},
        {"name": "列出计划", "value": "/index/index/plan/get"},
        {"name": "添加计划", "value": "/index/index/plan/add"},
        {"name": "删除计划", "value": "/index/index/plan/delpl"},
        {"name": "计划日志", "value": "/index/index/plan/log"},
        {"name": "任务页面", "value": "/index/index/task/index"},
        {"name": "任务列表", "value": "/index/index/task/task"},
        {"name": "任务状态", "value": "/index/index/task/taskstatus"},
        {"name": "设置", "value": "/index/index/setup/index"},
        {"name": "基本配置", "value": "/index/index/setup/basepage"},
        {"name": "开机启动项", "value": "/index/index/setup/startpage"},
        {"name": "备份恢复", "value": "/index/index/setup/bacrecpage"},
        {"name": "项目管理器", "value": "/index/index/setup/pythonrun"},
        {"name": "启动/停止项目管理", "value": "/index/index/setup/restart"},
        {"name": "设置/添加项目管理", "value": "/index/index/setup/setpythonrun"},
        {"name": "删除项目管理", "value": "/index/index/setup/delpythonrun"},
        {"name": "项目管理列表", "value": "/index/index/setup/pythonrulists"},
        {"name": "项目管理日志", "value": "/index/index/setup/logpythonrun"},
        {"name": "获取/保存配置信息", "value": "/index/index/setup/setbaseconfig"},
        {"name": "添加启动项", "value": "/index/index/setup/addstart"},
        {"name": "删除启动项", "value": "/index/index/setup/delstart"},
        {"name": "获取启动项", "value": "/index/index/setup/startlist"},
        {"name": "阿里云备份列表", "value": "/index/index/setup/aliyunosslist"},
        {"name": "阿里云备点恢复", "value": "/index/index/setup/aliyunossdownload"},
        {"name": "备份全部文稿", "value": "/index/index/setup/backup"},
        {"name": "恢复全部文稿", "value": "/index/index/setup/recovery"},
        {"name": "下载备份文件", "value": "/index/index/setup/download"},
        {"name": "上传备份文件", "value": "/index/index/setup/postsup"}
    ]
}
class admin:
    def setadminpwd():
        "设置初始化用户 登录码和密码"
        username='kcws'
        password="111111"
        try:
            sqlite("admin",model_app_path).where("id",1).update({'username':username,'password':md5("kcws"+password)})
        except:
            return errorjson(msg="设置失败")
        else:
            return successjson({"username":username,"password":password})
    def index():
        G.setadminlog="管理员入口"
        return response.tpl(dqpath+'/tpl/admin/index.html',absolutelypath=True)
    def admin():
        G.setadminlog="管理员页面"
        return response.tpl(dqpath+'/tpl/admin/admin.html',absolutelypath=True)
    def role():
        G.setadminlog="白名单角色页面"
        return response.tpl(dqpath+'/tpl/admin/role.html',absolutelypath=True)
    def blacklistrole():
        G.setadminlog="黑名单角色页面"
        return response.tpl(dqpath+'/tpl/admin/blacklistrole.html',absolutelypath=True)
    def adminlog():
        return response.tpl(dqpath+'/tpl/admin/adminlog.html',absolutelypath=True)
    def logdeta(id):
        G.setadminlog="日志明细"
        data=sqlite("admin_log t1",model_app_path).field("t1.*,t2.icon,t2.name,t2.phone").join("admin t2","t1.user_id=t2.id","LEFT").where("t1.id",id).find()
        data['routeparamarr']=json_decode(data['routeparam'])
        data['dataparamarr']=json_decode(data['dataparam'])
        return successjson(data)
    def loglist():
        G.setadminlog="日志列表"
        where="1=1"
        kw=request.args.get('kw')
        types=request.args.get('types')
        method=request.args.get('method')
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        if kw:
            if types=='title' or types=='dataparam' or types=='getparam' or types=='routeparam':
                where+=" and "+types+" like '%"+kw+"%'"
            else:
                where+=" and t2."+types+" like '%"+kw+"%'"
        if method:
            where+=" and method='"+method+"'"
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        lists=sqlite("admin_log t1",model_app_path).order("t1.id desc").field("t1.*,t2.icon,t2.name,t2.phone").join("admin t2","t1.user_id=t2.id","LEFT").where(where).page(pagenow,pagesize).select()
        count=sqlite("admin_log t1",model_app_path).join("admin t2","t1.user_id=t2.id","LEFT").where(where).count()
        data=return_list(lists,count,pagenow,pagesize)
        return successjson(data)
    def deletelogs(id=0):
        G.setadminlog="清空日志"
        if id:
            sqlite("admin_log",model_app_path).where('id',id).delete()
            return successjson()
        else:
            try:
                sqlite("admin_log",model_app_path).where("1=1").delete()
            except:
                return errorjson(msg="失败")
            else:
                return successjson()
    def deletelog30(id=0):
        G.setadminlog="删除30天前的日志"
        try:
            id=request.get_json()
            if not id:
                id=json_decode(request.froms.get("id"))
            sqlite("admin_log",model_app_path).where('addtime','<',times()-86400*30).delete()
        except:
            return errorjson(msg="失败")
        else:
            return successjson()
    def getpluglist(modular="intapp"):
        G.setadminlog="本地插件列表"
        path="app/"+modular+"/controller/"
        lis=os.listdir(path)
        lists=[]
        for k in lis:
            if not os.path.isfile(path+k) and '__' not in k:
                lists.append(k)
        data=sqlite('plug',model_app_path).select()
        # print(data)
        i=0
        for k in data:
            # k['value']=k['modular']+"/"+k['name']
            data[i]['role']=json_decode(k['role'])
            # if k['name'] not in lists:
            #     # print(k['name'],lists)
            #     del data[i]
            i+=1
        return successjson(data)
    def getmypluglist(modular="intapp"):
        "本地插件列表,当前用户拥有的权限"
        path="app/"+modular+"/controller/"
        lis=os.listdir(path)
        lists=[]
        for k in lis:
            if not os.path.isfile(path+k) and '__' not in k:
                lists.append(k)
        modular=request.args.get('modular')
        plug=request.args.get('plug')
        sqlite('plug',model_app_path).where("modular='intapp' and name='index'").delete() #版本过渡
        if modular and plug:
            data=sqlite('plug',model_app_path).where("modular='"+modular+"' and name='"+plug+"'").select()
        elif modular:
            data=sqlite('plug',model_app_path).where("modular='"+modular+"'").select()
        elif plug:
            data=sqlite('plug',model_app_path).where("name='"+plug+"'").select()
        else:
            data=sqlite('plug',model_app_path).select()
        data.insert(0,kcwebps_default_role)
        i=0
        for k in data:
            k['role']=json_decode(k['role'])
            if G.userinfo['role']['id']==1:
                role=k['role']
            else:
                role=[]
                for ii in k['role']:
                    if ii['value'] in G.userinfo['role']['roleroute']:
                        role.append(ii)
            
            if G.userinfo['blacklistrole']:#过滤权限黑名单
                data[i]['role']=[]
                for j in role:
                    if j['value'] in G.userinfo['blacklistrole']['roleroute']:
                        pass
                    else:
                        data[i]['role'].append(j)
                i+=1
        
        
        return successjson(data)
    def dellogin():
        G.setadminlog="退出所有会话"
        shutil.rmtree(config.session['path'])
        shutil.rmtree(config.cache['path'])
        return successjson()
    def getlist(id=0):
        "获取列表"
        if id:
            return successjson(sqlite("admin",model_app_path).field('id,icon,username,phone,nickname,name,logintime,addtime').find(id))
        where=None
        kw=request.args.get('kw')
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        if kw:
            where=[("username","like","%"+str(kw)+"%"),'or',("name","like","%"+str(kw)+"%"),'or',("nickname","like","%"+str(kw)+"%"),'or',("phone","like","%"+str(kw)+"%")]
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        lists=sqlite("admin",model_app_path).field("t1.*,t2.title,t2.describes,t3.title as t3title,t3.describes as t3describes").alias('t1').join("role t2","t1.role=t2.id","LEFT").join("blacklistrole t3","t1.blacklistrole=t3.id","LEFT").where(where).page(pagenow,pagesize).select()
        count=sqlite("admin",model_app_path).where(where).count()
        if G.userinfo['id']!=1:
            i=0
            for k in lists:
                if k['id']==1:
                    del lists[i]
                    count=count-1
                i+=1
        data=return_list(lists,count,pagenow,pagesize)
        return successjson(data)
    def insert():
        G.setadminlog="添加管理员"
        try:
            data=request.get_json()
            if not data:
                data=json_decode(request.froms.get("data"))
            if sqlite("admin",model_app_path).where("phone",data['phone']).count():
                return errorjson(msg="该手机已添加")
            if sqlite("admin",model_app_path).where("username",data['username']).count():
                return errorjson(msg="该用户名已添加")
            if not data['username'] or not data['password']:
                return errorjson(msg="请输入用户名或密码")
            data.update(logintime=times(),addtime=times())
            sqlite("admin",model_app_path).insert(data)
        except:
            return errorjson(msg="失败")
        else:
            return successjson()
    def delete(id=0):
        "批量删除"
        G.setadminlog="删除管理员"
        if id:
            sqlite("admin",model_app_path).where('id',id).delete()
            return successjson()
        else:
            try:
                id=request.get_json()
                if not id:
                    id=json_decode(request.froms.get("id"))
                if 1 in id:
                    id.remove(1)
                sqlite("admin",model_app_path).where('id','in',id).delete()
            except:
                return errorjson(msg="失败")
            else:
                return successjson()
    def update(id=0):
        "更新内容"
        G.setadminlog="修改管理员"
        data=request.get_json()
        if not data:
            data=json_decode(request.froms.get("data"))
        if not id:
            id=data['id']
        try:
            del data['title']
        except:pass
        try:
            del data['describes']
        except:pass
        try:
            del data['t3title']
        except:pass
        try:
            del data['t3describes']
        except:pass
        try:
            del data['logintime']
        except:pass
        try:
            del data['addtime']
        except:pass
        try:
            del data['password']
        except:pass
        if G.userinfo['role']['id']!=1:
            try:
                del data['phone']
            except:pass
            try:
                del data['username']
            except:pass
            try:
                del data['nickname']
            except:pass
            try:
                del data['name']
            except:pass
            try:
                del data['icon']
            except:pass
        if int(id)==1:
            # try:
            #     del data['phone']
            # except:pass
            # try:
            #     del data['username']
            # except:pass
            try:
                del data['role']
            except:pass
            try:
                del data['blacklistrole']
            except:pass
        if G.userinfo['role']['id']==1:
            sqlite("admin",model_app_path).where("id",id).update(data)
        else:
            if int(id)==1:
                return errorjson(msg="您没有权限修改此账号")
            if data['role']==G.userinfo['role']['id'] or sqlite("role",model_app_path).where("admin_id="+str(G.userinfo['id'])+" and id="+str(data['role'])).count():
                sqlite("admin",model_app_path).where("id",id).update(data)
            else:
                return errorjson(msg="您没有其他角色的权限")
        return successjson()
    def setpwd():
        "设置管理员登录密码"
        G.setadminlog="设置管理员登录密码"
        data=request.get_json()
        if not data:
            data=json_decode(request.froms.get("data"))
        try:
            sqlite("admin",model_app_path).where("id",data['id']).update({'password':data['password']})
        except:
            return errorjson(msg="设置失败")
        else:
            return successjson()
    def setmypwd():
        """设置自己的登录密码"""
        G.setadminlog="设置自己的登录密码"
        data=request.get_json()
        if not data:
            data=json_decode(request.froms.get("data"))
        try:
            sqlite("admin",model_app_path).where("id",G.userinfo['id']).update({'password':data['password']})
        except:
            return errorjson(msg="设置失败")
        else:
            return successjson()
    def getrolelist(id=0,roleroute=1,tab='role'):
        "获取角色"
        id=int(id)
        roleroute=int(roleroute)
        modular=request.args.get('modular')
        plug=request.args.get('plug')
        if id:
            return successjson(sqlite(tab,model_app_path).find(id))
        if G.userinfo['role']['id']==1:
            where='1=1'
        else:
            where="t1.id="+str(G.userinfo['role']['id'])+" or t1.admin_id="+str(G.userinfo['id'])
        kw=request.args.get('kw')
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        if kw:
            # where=[("title","like","%"+str(kw)+"%"),'and',('admin_id','eq',G.userinfo['id'])]
            where+=" and t1.title like '%"+str(kw)+"%'"
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        if roleroute:
            lists=sqlite(tab+" t1",model_app_path).join("admin t2","t1.admin_id=t2.id","left").field("t1.*,t2.name").where(where).page(pagenow,pagesize).select()
        else:
            lists=sqlite(tab+" t1",model_app_path).join("admin t2","t1.admin_id=t2.id","left").field("t1.id,t1.admin_id,t1.icon,t1.title,t1.describes,t1.types,t1.updtime,t1.addtime,t2.name").where(where).select()
        if roleroute:
            for k in lists:
                roleroutelist=json_decode(k['roleroute'])
                if modular or plug:#获取指定模块下插件的接口权限
                    roleroutelists=[]
                    for kk in roleroutelist:
                        if (modular+'/'+plug) in kk:
                            roleroutelists.append(kk)
                    k['roleroute']=roleroutelists
                else:
                    k['roleroute']=roleroutelist
        count=sqlite(tab+" t1",model_app_path).where(where).count()
        data=return_list(lists,count,pagenow,pagesize)
        return successjson(data)
    def insertrole(tab='role'):
        G.setadminlog="添加角色"
        try:
            data=request.get_json()
            if not data:
                data=json_decode(request.froms.get("data"))
            data['admin_id']=G.userinfo['id']
            data.update(updtime=times(),addtime=times())
            data['roleroute']=list(set(data['roleroute']))
            data['roleroute']=json_encode(data['roleroute'])
            sqlite(tab,model_app_path).insert(data)
        except:
            print(traceback.print_exc())
            return errorjson(msg="失败")
        else:
            return successjson()
    # def aa():
    #     a=[1,2,3,4]
    #     i=0
    #     for k in a:
    #         if k==3:
    #             del a[i]
    #         i+=1
    #     print(a)
    def updaterole(id=0,tab="role"):
        "更新内容"
        G.setadminlog="修改角色权限"
        data=request.get_json()
        if not data:
            data=json_decode(request.froms.get("data"))
        del data['name']
        del data['admin_id']
        modular=request.args.get('modular')
        plug=request.args.get('plug')
        data['roleroute']=list(set(data['roleroute']))
        plugarr=sqlite('plug',model_app_path).select()
        plugarr.insert(0,kcwebps_default_role)
        i=0
        for d in data['roleroute']:
            t=False
            for k in plugarr:
                role=json_decode(k['role'])
                for kk in role:
                    if d==kk['value']:
                        t=True
            if not t:
                del data['roleroute'][i]
            i+=1


        if not id:
            id=data['id']
        id=int(id)
        if tab=="role" and id==1:
            return errorjson(msg="该角色不允许修改")
        try:
            data.pop('updtime')
            data.pop('addtime')
            # dataroleroute=data['roleroute']
        except:pass
        else:
            if G.userinfo['role']['id']==1:
                if modular or plug:#更新指定模块下插件的接口权限
                    t=sqlite(tab,model_app_path).where("id",id).find()
                    tarrroleroute=json_decode(t['roleroute'])
                    tarrroleroutes=[]
                    for k in tarrroleroute:
                        if (modular+'/'+plug) not in k:
                            tarrroleroutes.append(k)
                    for k in data['roleroute']:
                        tarrroleroutes.append(k)
                    data['roleroute']=json_encode(tarrroleroutes)
                    sqlite(tab,model_app_path).where("id",id).update(data)
                else:
                    data['roleroute']=json_encode(data['roleroute'])
                    sqlite(tab,model_app_path).where("id",id).update(data)
            else:
                if modular or plug:#更新指定模块下插件的接口权限
                    t=sqlite(tab,model_app_path).where("id="+str(id)+" and admin_id="+str(G.userinfo['id'])).find()
                    if t:
                        tarrroleroute=json_decode(t['roleroute'])
                        tarrroleroutes=[]
                        for k in tarrroleroute:
                            if (modular+'/'+plug) not in k:
                                tarrroleroutes.append(k)
                        for k in data['roleroute']:
                            tarrroleroutes.append(k)
                        data['roleroute']=json_encode(tarrroleroutes)
                        sqlite(tab,model_app_path).where("id",id).update(data)
                    else:
                        return errorjson(msg="该记录权限不足")
                else:
                    data['roleroute']=json_encode(data['roleroute'])
                    if sqlite(tab,model_app_path).where("id="+str(id)+" and admin_id="+str(G.userinfo['id'])).update(data):
                        return successjson()
                    else:
                        return errorjson(msg="该记录权限不足")
        return successjson()
    def deleterole(tab="role"):
        "批量删除"
        G.setadminlog="删除角色"
        try:
            id=request.get_json()
            if not id:
                id=json_decode(request.froms.get("id"))
            if tab=='role':
                try:
                    
                    id.remove(1)
                except:pass
            if G.userinfo['role']['id']==1:
                sqlite(tab,model_app_path).where('id','in',id).delete()
            else:
                ids='0'
                for k in id:
                    ids+=","+str(k)
                sqlite(tab,model_app_path).where("id in ("+ids+") and admin_id="+str(G.userinfo['id'])).delete()
        except:
            return errorjson(msg="失败")
        else:
            return successjson()