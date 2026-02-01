from .common import *
kcwebsuserinfopath=os.path.split(os.path.realpath(__file__))[0]+"/common/file/"
dqpath=os.path.split(os.path.realpath(__file__))[0]
class modular:
    def index():
        return response.tpl(dqpath+'/tpl/modular/index.html',absolutelypath=True)
    if not os.path.exists(kcwebsuserinfopath):
        os.makedirs(kcwebsuserinfopath)
    def kcwebssebduser():
        data=request.get_json()
        http=Http()
        http.openurl(config.domain['kcwebsapi']+"/pub/sebduser","POST",data)
        res=json_decode(http.get_text)
        return response.json(res)
    def kcwebsreg():
        data=request.get_json()
        http=Http()
        http.openurl(config.domain['kcwebsapi']+"/pub/reg","POST",data)
        res=json_decode(http.get_text)
        return response.json(res)
    def banduser():
        data=request.get_json()
        http=Http()
        timestamp=times()
        sign=md5(str(data['username'])+str(timestamp)+md5(md5(data['password'])))
        http.set_header['username']=data['username']
        http.set_header['timestamp']=str(timestamp)
        http.set_header['sign']=sign
        http.openurl(config.domain['kcwebsapi']+"/user/userinfo")
        res=json_decode(http.get_text)
        if(res['code']==0):
            kcwebsuserinfo=res['data']
            kcwebsuserinfo['username']=data['username']
            kcwebsuserinfo['password']=data['password']
            file_set_content(kcwebsuserinfopath+str(G.userinfo['id']),json_encode(kcwebsuserinfo))
            return successjson()
        else:
            return errorjson(msg=res['msg'])
        
    def modular_list(kw='',pagenow=1):
        http=Http()
        http.openurl(config.domain['kcwebsapi']+"/pub/modular_list","get",params={
            "kw":kw,"pagenow":pagenow
        })
        res=json_decode(http.get_text)
        lists=res['data']['lists']
        for k in lists:
            k['status']=0 #0未安装  1已安装  2安装中 3卸载中 4不可以安装
            if os.path.exists("app/"+str(k['name'])):
                k['status']=1
        if os.path.isfile(kcwebsuserinfopath+str(G.userinfo['id'])):
            kcwebsuserinfo=file_get_content(kcwebsuserinfopath+str(G.userinfo['id']))
        else:
            kcwebsuserinfo=''
        if kcwebsuserinfo:
            res['kcwebsuserinfo']=json_decode(kcwebsuserinfo)
        else:
            res['kcwebsuserinfo']=''
        return response.json(res)

    def uploadmodular():
        "打包模块上传"
        G.setadminlog="打包模块上传模块"
        kcwebsuserinfo=file_get_content(kcwebsuserinfopath+str(G.userinfo['id']))
        if kcwebsuserinfo:
            kcwebsuserinfo=json_decode(kcwebsuserinfo)
            data=request.get_json()
            server=create("app",data['name'])
            data=server.packmodular()
            if data[0]:
                data=server.uploadmodular(kcwebsuserinfo['username'],kcwebsuserinfo['password'])
                if data[0]:
                    return successjson()
                else:
                    return errorjson(msg=data[1])
            return errorjson(msg=data[1])
        else:
            return errorjson("请先配置kcwebs账号")
    def installmodular():
        "安装模块"
        G.setadminlog="安装模块"
        arr=request.get_json()
        server=create("app",arr['name'])
        data=server.installmodular(arr['token'])
        time.sleep(1)
        if data[0]:
            # model_intapp_menu.add(title=arr['title'],icon=arr['icon'],url="/"+arr['name'])
            return successjson()
        else:
            return errorjson(msg=data[1])
    def uninstallmodular():
        "卸载模块"
        G.setadminlog="卸载模块"
        arr=request.get_json()
        server=create("app",arr['name'])
        data=server.uninstallmodular()
        time.sleep(1)
        if data[0]:
            model_intapp_menu.delete(title=arr['title'])
            return successjson()
        else:
            return errorjson(msg=data[1])

