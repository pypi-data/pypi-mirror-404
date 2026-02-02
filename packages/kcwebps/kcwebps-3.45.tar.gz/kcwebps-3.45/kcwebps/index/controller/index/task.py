from .common import *
dqpath=os.path.split(os.path.realpath(__file__))[0]
class task:
    def index():
        G.setadminlog="任务队列页面"
        return response.tpl(dqpath+'/tpl/task/index.html',absolutelypath=True)
    def task():
        G.setadminlog="获取全部队列"
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
        yz=Queues.getall(pagenow,pagesize)
        data=return_list(yz[0],yz[1],pagenow,pagesize)
        return successjson(data)
    def taskstatus(taskid):
        G.setadminlog="获取任务状态"
        return successjson(Queues.status(taskid))
    def delhist():
        G.setadminlog="清除任务历史记录"
        return successjson(Queues.delhist())