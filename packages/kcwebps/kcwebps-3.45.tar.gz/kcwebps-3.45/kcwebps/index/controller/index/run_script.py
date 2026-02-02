import kcwsqlite,os,time,hashlib,sys,kcwcache,subprocess,traceback
def md5(strs):
    m = hashlib.md5()
    b = strs.encode(encoding='utf-8')
    m.update(b)
    return m.hexdigest()
def getinterpreter(paths,types,filename,other):
    interpreter=md5(paths+types+filename+other) #解释器
    if types=='python3.6':
        if os.path.isfile('/usr/local/python/python3.6/bin/python3'):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/python/python3.6/bin/python3 /usr/bin/"+interpreter)
        else:
            return False,'未安装python3.6'
    elif types=='python3.8':
        if os.path.isfile('/usr/local/python/python3.8/bin/python3'):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/python/python3.8/bin/python3 /usr/bin/"+interpreter)
        else:
            return False,'未安装python3.8'
    elif types=='python3.9':
        if os.path.isfile('/usr/local/python/python3.9/bin/python3'):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/python/python3.9/bin/python3 /usr/bin/"+interpreter)
        else:
            return False,'未安装python3.9'
    elif types=='npm':
        if os.path.isfile('/usr/local/nodejs/nodejs14.16/bin/npm'):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/nodejs/nodejs14.16/bin/npm /usr/bin/"+interpreter)
        else:
            return False,'未安装npm'
    elif types=='php7.2':
        if os.path.isfile("/usr/local/php/php7.2/bin/php"):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/php/php7.2/bin/php /usr/bin/"+interpreter)
        else:
            return False,'您必须使用本系统的软件插件安装php7.2后才能使用该功能'
    elif types=='php7.3':
        if os.path.isfile("/usr/local/php/php7.3/bin/php"):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/php/php7.3/bin/php /usr/bin/"+interpreter)
        else:
            return False,'您必须使用本系统的软件插件安装php7.3后才能使用该功能'
    elif types=='php7.4':
        if os.path.isfile("/usr/local/php/php7.4/bin/php"):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/php/php7.4/bin/php /usr/bin/"+interpreter)
        else:
            return False,'您必须使用本系统的软件插件安装php7.4后才能使用该功能'
    elif types=='php8.2':
        if os.path.isfile("/usr/local/php/php8.2/bin/php"):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/php/php8.2/bin/php /usr/bin/"+interpreter)
        else:
            return False,'您必须使用本系统的软件插件安装php8.2后才能使用该功能'
    elif types=='php8.3':
        if os.path.isfile("/usr/local/php/php8.3/bin/php"):
            if not os.path.isfile("/usr/bin/"+interpreter):
                os.system("ln -s /usr/local/php/php8.3/bin/php /usr/bin/"+interpreter)
        else:
            return False,'您必须使用本系统的软件插件安装php8.3后才能使用该功能'
    return True,interpreter
def is_index(params,index):
    try:
        params[index]
    except KeyError:
        return False
    except IndexError:
        return False
    else:
        return True
def run_script_savepid(id):
    pid=os.getpid()
    kcwcache.cache.set_cache(md5(str(id)),pid,0)
def run_script_getpid(id):
    return kcwcache.cache.get_cache(md5(str(id)))
def run_script_delpid(id):
    kcwcache.cache.del_cache(md5(str(id)))
if __name__ == "__main__":


    id=int(sys.argv[1])
    paths="/kcwebps"
    if is_index(sys.argv,2):
        paths=sys.argv[2]
    daemon=False
    if is_index(sys.argv,3) and sys.argv[3]=='1':
        daemon=True
    run_script_savepid(id)
    # print(os.path.dirname(os.path.abspath(__file__))+"/run_script.py")
    # exit()
    model_intapp_index_path=paths+"/app/common/file/sqlite/index_index"
    data=kcwsqlite.sqlite.connect(model_intapp_index_path).table("pythonrun").where("id",id).find()
    if not data:
        raise Exception('id错误')
    if data['types']=='customize':
        cmd="cd "+data['paths']+" && "+data['other']
        cmds=data['other'].split(' ')
    elif data['types']=='kcwebps':
        cmd="cd "+paths+" && kcwebps "+data['other']+" --cli"
        data['paths']='/kcwebps'
        cmds=("kcwebps "+data['other']+" --cli").split(' ')
    else:
        ttt,interpreter=getinterpreter(data['paths'],data['types'],data['filename'],data['other'])
        if data['other']: #带运行参数
            cmd="cd "+data['paths']+"&& "+interpreter+" "+data['filename']+" "+data['other']
            cmds=(interpreter+" "+data['filename']+" "+data['other']).split(' ')
        else:
            cmd="cd "+data['paths']+"&& "+interpreter+" "+data['filename']
            cmds=(interpreter+" "+data['filename']).split(' ')
    cmdarr=[]
    for k in cmds:
        if k:
            cmdarr.append(k)
    if daemon:
        while True:
            # os.system(cmd)
            process = subprocess.Popen(cmdarr,cwd=data['paths'],stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            while True:
                # 读取一行输出
                try:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break  # 如果没有更多输出了，并且进程已经结束，则退出循环
                    if output:
                        print(output.strip())  # 打印输出（去除行尾的换行符）
    
                    error = process.stderr.readline()
                    if error:
                        print(f"{error.strip()}", file=sys.stderr)  # 打印错误信息
                except UnicodeDecodeError as e:
                    error=str(traceback.format_exc())
                    arr=error.split('\n')
                    errarr=[]
                    for erk in arr:
                        if 'File "' in erk:
                            errarr.append(erk)
                    print("警告："+errarr[len(errarr)-1][2:])
                    print("原因："+str(e))
                except:
                    print('subprocess异常',str(traceback.format_exc()))
                    raise
            process.stdout.close()
            process.stderr.close()
            process.wait()
            time.sleep(5)
    else:
        # os.system(cmd)
        process = subprocess.Popen(cmdarr,cwd=data['paths'],stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        while True:
            # 读取一行输出
            try:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break  # 如果没有更多输出了，并且进程已经结束，则退出循环
                if output:
                    print(output.strip())  # 打印输出（去除行尾的换行符）
    
                error = process.stderr.readline()
                if error:
                    print(f"{error.strip()}", file=sys.stderr)  # 打印错误信息
            except UnicodeDecodeError as e:
                error=str(traceback.format_exc())
                arr=error.split('\n')
                errarr=[]
                for erk in arr:
                    if 'File "' in erk:
                        errarr.append(erk)
                print("警告："+errarr[len(errarr)-1][2:])
                print("原因："+str(e))
            except:
                print('subprocess异常',str(traceback.format_exc()))
                raise
        process.stdout.close()
        process.stderr.close()
        process.wait()
    run_script_delpid(id)