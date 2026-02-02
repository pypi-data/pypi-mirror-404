from .common import *
dqpath=os.path.split(os.path.realpath(__file__))[0]
system_start.insert_Boot_up(cmd='nohup kcwebps /index/index/index/inspection --cli > app/runtime/log/inspection.log 2>&1 &',name='智能巡检',types='kcwebps',icon='https://img.kwebapp.cn/icon/kcwebs.png')

class index:
    def inspection():
        from .setup import setup
        mytimess=0
        systembaseconfig=getbaseconfig() #获取配置信息
        config.email['sender']=systembaseconfig['email']['sender'] #发件人邮箱账号
        config.email['pwd']=systembaseconfig['email']['pwd'] #发件人邮箱密码(如申请的smtp给的口令)
        if config.email['sender'] and config.email['pwd'] and systembaseconfig['email']['recuser']:
            while True:
                if times()-mytimess>1800:
                    mytimess=times()
                    html=''
                    sendstatus=False
                    pythonrunhtml="<h1 style='text-align:center'>"+systembaseconfig['system']['name']+"</h1>"
                    pythonrunhtml+="<h1>cli项目管理器告警</h1>"
                    pythonrunhtml+="<table border='1' width='100%'>"
                    pythonrunhtml+="<tr><td>项目名称</td><td>项目描述</td><td>状态</td></tr>"
                    data=setup.pythonrulistsss(pagesize=10000)
                    for k in data['lists']:
                        if k['status']!=1:
                            sendstatus=True
                            pythonrunhtml+="<tr><td>"+k['title']+"</td><td>"+k['descs']+"</td><td style='color:red'>已停止</td></tr>"
                    pythonrunhtml+="</table>"
                    if sendstatus:
                        html+=pythonrunhtml
                    
                    
                    config.email['sendNick']='智能巡检' #发件人昵称
                    if html:
                        send_mail(systembaseconfig['email']['recuser'],text=html,theme='智能巡检')
                else:
                    time.sleep(4)
    def getuser():
        "获取用户信息"
        return successjson(G.userinfo)
    def my_get_process_id(val):
        "根据名称获取进程id"
        return successjson(get_process_id(val))
    def index():
        if os.path.isfile("app/common/file/config.conf"):
            data=json_decode(file_get_content("app/common/file/config.conf"))
        else:
            data={
                'system':{
                    "logo":"","name":""
                }
            }
        response.userinfo=G.userinfo
        response.fileconfig=data
        return response.tpl(dqpath+'/tpl/index/index.html',absolutelypath=True)
    def kcwebpsconfig():
        return successjson(config.kcwebps)
    def home():
        # print(config.kcwebps)
        try:
            response.kcwebps=config.kcwebps
        except:
            response.kcwebps=''
        response.ppath=os.getcwd().replace('\\','/')
        response.kcwebpspath=kcwebpspath
        return response.tpl(dqpath+'/tpl/index/home.html',absolutelypath=True)
    def menu():
        admin_id=G.userinfo['id']
        header=sqlite("menu",model_app_path).order("sort desc").where("types='header' and (admin_id=0 or admin_id="+str(admin_id)+")").select()
        leftlist=sqlite("menu",model_app_path).order("sort desc").where("types='left' and (admin_id=0 or admin_id="+str(admin_id)+")").select()
        for k in leftlist:
            k['icon']=k['icon'].replace("https://img.kwebapp.cn",config.domain['kcwebsimg'])
            k['url']=k['url'].replace('/intapp/index/','/index/index/')
        data={
            'header':list_to_tree(data=header,child="level"),
            'leftlist':list_to_tree(data=leftlist,child="level")
        }
        return successjson(data)
    def ip_Place(client_ip):
        """ip归属地查询，目前只支持中国地区解析

        client_ip 客户端ip地址

        return (国家,省,市,县,区,运营商,网络类型)
        """
        data=get_cache("intappindexindexip_Place"+client_ip)
        if not data:
            http=Http()
            # if proxip:
            #     http.set_proxies={'http': 'http://'+proxip,'https': 'http://'+proxip}
            http.set_encoding="gb2312"
            http.set_session=False
            http.set_header['Host']='www.ip138.com'
            http.set_header['User-Agent']='Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 SE 2.X MetaSr 1.0'
            http.openurl("https://www.ip138.com/iplookup.asp?ip=%s&action=2" % client_ip,allow_redirects=False)
            strs=http.get_text
            file_set_content("aa.log",strs)
            strs=strs.split('var ip_result = ')[1]
            strs=strs.split(";")[0]
            strs=re.sub(", }","}",strs)
            ar=json_decode(strs)
            file_set_content("aa.log",strs)
            # print(strs)
            # print(ar)
            data={
                "country":"","province":"","city":"","county":"","area":"","operators":"","net":""
            }
            if ar and len(ar['ip_c_list']):
                jsar=ar['ip_c_list'][0]
                if jsar['city']=='':
                    try:
                        jsar['city']=(ar['参考数据2'].split("省")[1]).split(" ")[0]
                    except:pass
                jsar['prov']=re.sub("[省,市]","",jsar['prov'])
                jsar['city']=re.sub("[省,市]","",jsar['city'])
                lists=[jsar['ct'],jsar['prov'],jsar['city'],jsar['area'],jsar['idc'],jsar['yunyin'],jsar['net']]
                data={
                    "country":jsar['ct'],"province":jsar['prov'],"city":jsar['city'],"county":jsar['area'],"area":jsar['idc'],"operators":jsar['yunyin'],"net":jsar['net']
                }
            set_cache("intappindexindexip_Place"+client_ip,data,86400)
        return successjson(data)

    def homes():
        sysinfo=get_sysinfo()
        rundate=times()-int(sysinfo['start_time'])
        sysrundate=times()-int(psutil.boot_time())
        sysinfo['rundate']=returndate(rundate)
        sysinfo['sysrundate']=returndate(sysrundate)
        return successjson(sysinfo)
    def disk():#磁盘分区和使用情况
        partition=[]
        disk_usage=psutil.disk_usage('/')
        if "Linux" in get_sysinfo()['platform']:
            partition.append({
                'name':'/','type':'','count':disk_usage[0],'used':disk_usage[1],'free':disk_usage[2],'userate':disk_usage[3]
            })
        partitions=psutil.disk_partitions()
        for v in partitions:
            if v[2]:
                disk_usage=psutil.disk_usage(v[0])
                if disk_usage[0]:
                    partition.append({
                        'name':v[0],'type':v[2],'count':disk_usage[0],'used':disk_usage[1],'free':disk_usage[2],'userate':disk_usage[3]
                    })
        return successjson({
            'partitions':partition, #磁盘分区和使用情况
            'io':psutil.disk_io_counters()
        })
    def cpume():#cpu和内存以及网络信息
        # time.sleep(59)
        info={}
        info['cpu']={
            'count':psutil.cpu_count(),
            'time':psutil.cpu_times().user,
            'use':psutil.cpu_percent() #cpu使用率
        }
        physics=psutil.virtual_memory() #物理内存
        swap=psutil.swap_memory()  #交换内存
        info['memory']={
            'physics':{               #物理内存
                'count':physics.total,   #'内存大小'
                'available':physics.available,#可用
                'used':physics.used,   #已用
                'userate':physics.percent   #使用率
            },
            'swap':{
                'count':swap.total,
                'available':swap.free,
                'used':swap.used,   #已用
                'userate':swap.percent
            },
        }
        net=psutil.net_io_counters()
        info['net']={
            'bytes_sent':net.bytes_sent,
            'bytes_recv':net.bytes_recv,
            'packets_sent':net.packets_sent,
            'packets_recv':net.packets_recv
        }
        return successjson(info)
    def process():
        "进程列表"
        lists=[]
        for proc in psutil.process_iter():
            try:
                pinfo = proc.as_dict(attrs=['pid', 'name'])
            except psutil.NoSuchProcess:
                pass
            else:
                lists.append(pinfo)
        return successjson(lists)


    def shell():
        shellstr=request.args.get("shellstr")
        if shellstr:
            G.setadminlog="执行命令："+shellstr
            os.system(shellstr)
        else:
            data=request.get_json()
            G.setadminlog="执行命令："+data['shell']
            os.system(data['shell'])
        return successjson()
    def reboot(types='app'):
        "重启"
        if types=='app':
            G.setadminlog="重启应用"
            kill_all_kcwebs_pid('all')
            if 'Linux' in get_sysinfo()['platform']:
                shellstr="bash server.sh"
            elif 'Windows' in get_sysinfo()['platform']:
                shellstr="server.bat"
            else:
                return errorjson(msg='暂不支持重启应用'+get_sysinfo()['platform'])
        else:
            G.setadminlog="重启服务器"
            if 'Linux' in get_sysinfo()['platform']:
                shellstr="reboot"
            else:
                return errorjson(msg='仅linux支持重启服务器')
        os.system(shellstr)
        return successjson()