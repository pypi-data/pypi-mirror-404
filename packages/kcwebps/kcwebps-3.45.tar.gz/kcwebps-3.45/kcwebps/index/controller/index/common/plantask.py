# -*- coding: utf-8 -*-
from .model import *
if not os.path.exists(config.cache['path']+"/plan/"):
    os.makedirs(config.cache['path']+"/plan/")
import pytz,multiprocessing,threading
class PLANTASK():
    def log(iden):
        "获取任务日志"
        if os.path.isfile(config.cache['path']+"/plan/"+str(iden)):
            f=open(config.cache['path']+"/plan/"+str(iden),"r",encoding='utf-8')
            k=f.read()
            f.close()
            return k
        else:
            return ''
    def shells(shell,iden):
        shell=shell+" >> "+config.cache['path']+"/plan/"+iden+" 2>&1 &"
        f=open(config.cache['path']+"/plan/"+str(iden),"w+",encoding='utf-8')
        # f=open(config.cache['path']+"/plan/"+str(iden),"a",encoding='utf-8') #追加
        f.write("---------"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"--OPEN shell SUCCESS---------\n"+shell+"\n")
        f.close()
        subprocess.Popen(shell,shell=True, stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        # ars=pi.stdout.read().decode()
    def openurls(url,iden):
        http=Http()
        http.openurl(url)
        f=open(config.cache['path']+"/plan/"+str(iden),"w+",encoding='utf-8')
        f.write("---------"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())+"--OPEN URL SUCCESS---------\n"+http.get_text+"\n---------OPEN URL END---------\n\n\n")
        f.close()
    def plantaskdsfsdfsafdsafsd(BlockingSchedulers,func,targger="cron",args=None,year=None,month=None,week="*",day_of_week='*',day=None,hour=None,minute=None,second='0',iden=False):
        """添加定时器任务、计划任务

        func 函数名

        args 函数参数  例：(1,)

        year 年

        month 月

        day 日

        hour 几点

        minute 几分

        second 几秒
        """
        # BlockingSchedulers = BlockingScheduler()
        if not iden:
            iden=randoms()
        if targger=='cron':
            BlockingSchedulers.add_job(func,targger,args=args,year=year,month=month,week=week,day_of_week=day_of_week,day=day,hour=hour, minute=minute,second=second)
        elif targger=='interval':
            if day:
                BlockingSchedulers.add_job(func,targger,args=args,days=int(day))
            elif hour:
                BlockingSchedulers.add_job(func,targger,args=args,hours=int(hour))
            elif minute:
                BlockingSchedulers.add_job(func,targger,args=args,minutes=int(minute))
            elif second:
                BlockingSchedulers.add_job(func,targger,args=args,seconds=int(second))
        try:
            BlockingSchedulers.start()
        except:
            BlockingSchedulers.shutdown()
    # def delete(data):
    #     "删除计划任务,"
    #     if PLANTASK.BlockingSchedulers:
    #         PLANTASK.BlockingSchedulers.remove_job(data['iden'])
    #         return True
    #     else:
    #         return False
    BlockingSchedulers=None
    def plantask(data):
        "添加计划任务"
        iden=data['iden']
        if data['types']=='shell':
            func=PLANTASK.shells
            args=(data['value'],iden)
        elif data['types']=='openurl':
            func=PLANTASK.openurls
            args=(data['value'],iden)
        elif data['types']=='restart-php-fpm': #重启php
            func=PLANTASK.shells
            phpname=data['value'].replace(".", "")
            args=("pkill -9 "+phpname+"-fpm && "+phpname+"-fpm"+" -c /usr/local/php/"+data['value']+"/bin/php.ini -R",iden)
        else:
            func=PLANTASK.shells
            args=(data['value'],iden)
        targger="cron"
        year=None
        month=None
        day=None
        week="*"
        day_of_week="*"
        hour=None
        minute=None
        second='0'
        if data['cycle']=='minute':
            second=data['second']
        elif data['cycle']=='hour':
            second=data['second']
            minute=data['minute']
        elif data['cycle']=='day_of_week':
            second=data['second']
            minute=data['minute']
            day_of_week=data['day_of_week']
        elif data['cycle']=='day':
            second=data['second']
            minute=data['minute']
            hour=data['hour']
        elif data['cycle']=='month':
            second=data['second']
            minute=data['minute']
            hour=data['hour']
            day=data['day']
        elif data['cycle']=='year':
            second=data['second']
            minute=data['minute']
            hour=data['hour']
            day=data['day']
            month=data['month']
        elif data['cycle']=='fixed':
            second=data['second']
            minute=data['minute']
            hour=data['hour']
            day=data['day']
            month=data['month']
            year=data['year']
        elif data['cycle']=='NS':
            targger="interval"
            second=data['second']
        elif data['cycle']=='NM':
            targger="interval"
            minute=data['minute']
        elif data['cycle']=='NH':
            targger="interval"
            hour=data['hour']
        elif data['cycle']=='NH':
            targger="interval"
            day=data['day']
        try:
            if not PLANTASK.BlockingSchedulers:
                from apscheduler.schedulers.blocking import BlockingScheduler
                PLANTASK.BlockingSchedulers = BlockingScheduler(timezone=pytz.timezone("Asia/Shanghai"))
            if 'Linux' in get_sysinfo()['platform']:
                mu=multiprocessing.Process(target=PLANTASK.plantaskdsfsdfsafdsafsd,args=(PLANTASK.BlockingSchedulers,func,targger,args,year,month,week,day_of_week,day,hour,minute,second,iden))
                mu.start()
                # f=open(config.cache['path']+"/plantaskstart.log","a")
                # f.write("启动计划日志,"+data['value']+","+str(times())+"\n")
                # f.close()
            elif 'Windows' in get_sysinfo()['platform']:
                t=threading.Thread(target=PLANTASK.plantaskdsfsdfsafdsafsd,args=(PLANTASK.BlockingSchedulers,func,targger,args,year,month,week,day_of_week,day,hour,minute,second,iden))
                t.daemon=True
                t.start()
        except:
            return False
        else:
            return True