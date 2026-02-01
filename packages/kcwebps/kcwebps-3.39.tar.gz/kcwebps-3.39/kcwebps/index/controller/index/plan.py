
# -*- coding: utf-8 -*-
from .common import *
indexconfigpath=os.path.split(os.path.realpath(__file__))[0]+"/common/file/sqlite/"
dqpath=os.path.split(os.path.realpath(__file__))[0]
class plan:
    def index():
        return response.tpl(dqpath+'/tpl/plan/index.html',absolutelypath=True)
    def get(id=0):
        "获取列表"
        if id:
            return successjson(sqlite("interval").find(id))
        where=None
        pagenow=request.args.get('pagenow')
        pagesize=request.args.get('pagesize')
        if not pagenow:
            pagenow=1
        else:
            pagenow=int(pagenow)
        if not pagesize:
            pagesize=10
        else:
            pagesize=int(pagesize)
        lists=sqlite("interval").page(pagenow,pagesize).select()
        count=sqlite("interval").where(where).count()
        data=return_list(lists,count,pagenow,pagesize)
        data['strconfig']=json_decode(file_get_content(indexconfigpath+"strconfig"))
        return successjson(data)
    def add():
        G.setadminlog="添加计划任务"
        "添加任务"
        if sqlite("interval").count() >=100:
            return errorjson(code=1,msg="您已超过系统预设最大限制")
        data=request.get_json()
        if data['types']=='backupmysql':
            if sqlite("interval").where("types","backupmysql").count():
                return errorjson(code=1,msg="该计划已添加，不可重复提交")
        data['addtime']=times()
        data['updtime']=times()
        if data['oss']==True:
            data['oss']=1
        else:
            data['oss']=0
        data['iden']=md5(str(times()))
        if data['types'] != 'backupmysql' and (not data['name'] or not data['value']):
            return errorjson(code=1,msg="参数不全")
        # PLANTASK.plantask(data)
        # Queues.insert(target=PLANTASK.plantask,args=(data,),title="添加任务任务:"+data['name'])
        sqlite("interval").insert(data)
        return successjson(msg="添加成功，重启后生效")
    def delpl():
        "删除计划"
        G.setadminlog="删除计划任务"
        id=request.get_json()
        sqlite("interval").where('id','in',id).delete()
        return successjson(msg="任务已删除，重启后生效")
    def log(iden):
        "任务日志"
        return successjson(PLANTASK.log(iden))

    def setconfig(types='set',paths='strconfig'):
        if types=='set':
            G.setadminlog="保存配置"
            data=request.get_json()
            file_set_content(indexconfigpath+paths,json_encode(data))
            return successjson(data)
        elif types=='get':
            data=json_decode(file_get_content(indexconfigpath+paths))
            return successjson(data)