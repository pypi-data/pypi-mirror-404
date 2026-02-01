from kcwebps.index.common import *
import subprocess
response.platform=get_sysinfo()['platform']
def get_process_id(name):
    try:
        child = subprocess.Popen(['pgrep', '-f', name],stdout=subprocess.PIPE, shell=False)
        response = child.communicate()[0]
        return [int(pid) for pid in response.split()]
    except:
        return []
def get_pid_info(pid,types='pid'):
    """通过pid获取进程信息
    
    pid 路由地址

    types info表示获取进程信息 否则判断进程号是否存在
    """
    if not pid:
        return False
    pid=int(pid)
    try:
        if types=='info':
            p = psutil.Process(pid)
            data={
                'pid':pid,
                'name':p.name(),
                'cli':p.cmdline(),
                'cpu':p.cpu_percent(1),
                'memory':p.memory_info().rss
            }
            return data
        else:
            if psutil.pid_exists(pid):
                return pid
            else:
                return False
    except:
        return False
def getbaseconfig(types='get',config={}):
    "获取配置信息"
    if types=='get':
        if os.path.isfile("app/common/file/config.conf"):
            data=json_decode(file_get_content("app/common/file/config.conf"))
            if not data['aliyun']['backpath']:
                data['aliyun']['backpath']="kcwebs"
            if not is_index(data,'kcwebsapi'):
                data['kcwebsapi']={'host':'','filehost':''}
            if not is_index(data,'email'):
                data['email']={'sender':'','pwd':'','recuser':''}
            if not is_index(data['system'],"id"):
                data['system']['id']=''
            
        else:
            data={}
        return data
    else:
        file_set_content("app/common/file/config.conf",json_encode(config))
        return True
def returndate(rundate):
    if rundate < 60:
        rundate=str(rundate)+"秒"
    elif rundate < 60*60:
        rundate=str(int(rundate/60))+"分钟"+str(int(rundate%60))+"秒"
    elif rundate < 60*60*24:
        m=int(rundate%(60*60))
        if m < 60:
            rundate=str(int(rundate/(60*60)))+"小时"+str(m)+"秒"
        elif m <60*60:
            rundate=str(int(rundate/(60*60)))+"小时"+str(int(m/60))+"分"+str(int(m%60))+"秒"
    else:
        m=int(rundate%(60*60*24))
        if m < 60:
            rundate=str(int(rundate/(60*60*24)))+"天"+str(m)+"秒"
        elif m < 60*60:
            rundate=str(int(rundate/(60*60*24)))+"天"+str(int(m/60))+"分"+str(int(m%60))+"秒"
        elif m < 60*60*24:
            xs=int(m/3600)
            mm=int(m%3600)
            if mm < 60:
                rundate=str(int(rundate/(60*60*24)))+"天"+str(xs)+"小时"+str(mm)+"秒"
            else:
                rundate=str(int(rundate/(60*60*24)))+"天"+str(xs)+"小时"+str(int(mm/60))+"分"+str(int(mm%60))+"秒"
    return rundate