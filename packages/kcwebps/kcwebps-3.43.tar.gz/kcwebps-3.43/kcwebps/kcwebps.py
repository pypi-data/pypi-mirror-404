try:
    from .common import *
except Exception as e:
    if 'unable to open database file' in str(e):
        print('该命令仅支持运行kcwebps项目',e)
        exit()
    else:
        print('e',e)
from kcwebs import kcwebs
def cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr='kcwebps'):
        "脚本入口"
        cmd_par=kcwebs.kcws.get_cmd_par(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
        if cmd_par and not cmd_par['project']:
            cmd_par['project']='kcwebps'
        if cmd_par and cmd_par['server'] and not cmd_par['help']:#启动web服务
            try:
                Queues.delwhere("code in (2,3)")
            except:pass
            #执行kcwebps自启项
            try:
                import kcwsqlite
                startdata=kcwsqlite.sqlite.connect(model_app_path).where("types='kcwebps'").table("start").order("id asc").select()
            except Exception as e:
                print("需要在kcwebps项目中执行",e)
                exit()
            for teml in startdata:
                os.system(teml['value'])
            if get_sysinfo()['uname'][0]=='Linux':
                system_start.insert_Boot_up(cmd='cd /kcwebps && bash server.sh',name='kcwebps自启',icon='https://img.kwebapp.cn/icon/kcwebs.png')
                os.system('nohup kcwebps index/index/pub/clistartplan --cli > app/runtime/log/server.log 2>&1 &')
        if cmd_par and cmd_par['install'] and not cmd_par['help']:#插入 应用、模块、插件
            if cmd_par['appname']:
                remppath=os.path.split(os.path.realpath(__file__))[0]
                if not os.path.exists(cmd_par['project']+'/'+cmd_par['appname']) and not os.path.exists(cmd_par['appname']):
                    shutil.copytree(remppath+'/tempfile/kcwebps',cmd_par['project'])
                    if get_sysinfo()['uname'][0]=='Linux':
                        try:
                            os.remove(cmd_par['project']+"/server.bat")
                        except:pass
                    elif get_sysinfo()['uname'][0]=='Windows':
                        try:
                            os.remove(cmd_par['project']+"/server.sh")
                        except:pass
                    print('kcwebps项目创建成功')
                else:
                    t=kcwebs.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
            else:
                t=kcwebs.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)
        elif cmd_par:
            t=kcwebs.cill_start(fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr=fdgrsgrsegsrsgrsbsdbftbrsbfdrtrtbdfsrsgr)