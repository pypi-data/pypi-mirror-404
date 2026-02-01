from .common import *
dqpath=os.path.split(os.path.realpath(__file__))[0]
class menu:
    def index():
        return response.tpl(dqpath+'/tpl/menu/index.html',absolutelypath=True)
    def menulist(pid=0):
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        admin_id=G.userinfo['id']
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        if int(pid) > 0:
            lists=sqlite("menu",model_app_path).where("pid",pid).page(pagenow,pagesize).order("sort desc,types asc").select()
            count=sqlite("menu",model_app_path).where("pid",pid).count()
        else:
            lists=sqlite("menu",model_app_path).where("admin_id=0 or admin_id="+str(admin_id)).page(pagenow,pagesize).order("sort desc,types asc").select()
            count=sqlite("menu",model_app_path).where("admin_id=0 or admin_id="+str(admin_id)).count()
        data=return_list(lists,count,pagenow,pagesize)
        return successjson(data)
    def menuupdate(id=0):
        "更新内容"
        G.setadminlog="修改菜单"
        data=request.get_json()
        if not id:
            id=data['id']
            sqlite("menu",model_app_path).where("id",id).update(data)
            return successjson()
        else:
            return errorjson(msg="参数不全")
    def menudelete():
        "批量删除"
        G.setadminlog="删除菜单"
        id=request.get_json()
        idstr="0"
        for k in id:
            idstr+=","+str(k)
        sqlite("menu",model_app_path).where("id in ("+idstr+")").delete()
        return successjson()
    def menuinsert():
        G.setadminlog="添加菜单"
        data=request.get_json()
        if is_index(data,'id'):
            del data['id']
        data['admin_id']=G.userinfo['id']
        sqlite("menu",model_app_path).insert(data)
        return successjson()
