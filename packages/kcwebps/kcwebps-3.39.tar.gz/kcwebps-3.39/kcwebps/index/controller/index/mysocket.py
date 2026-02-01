from .common import *
system_start.insert_Boot_up(cmd='nohup kcwebps /index/index/mysocket/servers --cli > app/runtime/log/mysocket.log 2>&1 &',name='通知服务自启',types='kcwebps',icon='https://img.kwebapp.cn/icon/kcwebs.png')
class sockets(kcwebssocket):
    user={}
    def __successjson(self,data=[],code=0,msg="成功"):
        res={
            "code":code,
            "msg":msg,
            "time":int(times()),
            "data":data
        }
        return json_encode(res)
    def __errorjson(self,data=[],code=1,msg="失败",status='400 error'):
        return self.__successjson(data=data,code=code,msg=msg)
    def __setuser(self,clientid,user):
        "设置用户"
        self.user[clientid]=user
    def __deluser(self,clientid):
        "删除用户"
        try:
            del self.user[clientid]
        except:pass
    def getuser(self,clientid):
        "获取用户"
        return self.user[clientid]
    async def onConnect(self,clientid,params):
        "#当客户端发来连接时触发的回调函数"
        uid=params['uid']
        userinfo=get_cache(uid)
        if not userinfo:
            await self.CloseSocket(clientid)
            return False
        
        authkey=get_cache("websocket")
        # del_cache(uid)
        # del_cache("websocket")
        if params['authkey']=='send_authkey_frdsgedsgvdsgvgdfsdgtdrfdsfdgvffdsfdsvfgd352esdgfs': #发布者
            userinfo['types']='send'
            self.__setuser(clientid,userinfo)
            await self.send_client(clientid,self.__successjson("发布者连接成功"))
            return True
        elif params['authkey']==authkey:#订阅者
            userinfo['types']='subto'
            self.__setuser(clientid,userinfo)
            await self.send_client(clientid,self.__successjson({
                'types':'Groupname',
                'data':self.getGroupname()
            }))
            return True
        else:
            await self.CloseSocket(clientid)
            return False
    async def onMessage(self,clientid,recv_text):
        "当客户端发来数据时触发的回调函数"
        try:
            data=json_decode(recv_text)
        except:
            await self.send_client(clientid,self.__errorjson(msg="必须是标准json字符串格式"))
        else:
            if self.getuser(clientid)['types']=='send':
                if is_index(data,'types') and data['types']=='ungroup':#解散分组
                    self.ungroup('group'+data['group_id'])
                elif is_index(data,'types') and data['types']=='joinGroup':#加入组
                    self.joinGroup(clientid,'group'+data['group_id']) #加入组
                else:
                    # print(data)
                    await self.sendToGroup('group'+data['group_id'],self.__successjson(data)) #向某个分组的所有在线clientid发送数据
            else:
                if data['types']=='getGroupname':#获取组名称
                    await self.send_client(clientid,self.__successjson({
                        'types':'Groupname',
                        'data':self.getGroupname()
                    }))
                elif data['types']=='joinGroup':#加入组
                    self.joinGroup(clientid,data['group']) #加入组
                    await self.send_client(clientid,self.__successjson({
                        'types':'res',
                        'data':'success'
                    }))
                elif data['types']=='leaveGroup':#退出组
                    self.leaveGroup(clientid,data['group']) #退出组
                    await self.send_client(clientid,self.__successjson({
                        'types':'res',
                        'data':'success'
                    }))
                else:
                    await self.send_client(clientid,self.__errorjson(msg="您的信息未发送，只有发布者拥有广播权限"))
    async def onClose(self,clientid):
        "客户端与websocket的连接断开时触发"
        await self.CloseSocket(clientid)
        self.__deluser(clientid)
class mysocket:
    def mysend():
        " 测试发送 "
        socket_clients=getfunction("app.intapp.controller.index.mysocket").socket_client()
        socket_clients.send('123')
        return successjson()
    def servers():
        #kcwebps /index/index/mysocket/servers
        if config.app['cli']: #cli模式下运行
            kcwebpsdomain.banddomain(proxyitem={'notes':'首页通知服务代理','types':'websocket','rule':'/index/index/ws','url':'http://127.0.0.1:39030'}) #绑定代理域名
            socket=sockets()
            socket.start(ip='0.0.0.0',port='39030')
    def restart():
        "重启通讯服务"
        G.setadminlog="重启通讯服务"
        if 'Linux' in get_sysinfo()['platform']:
            kill_route_cli("/index/index/mysocket/servers")
            cmd="nohup kcwebps /index/index/mysocket/servers --cli > app/runtime/log/mysocket.log 2>&1 &"
            os.system(cmd)
        else:
            return errorjson(msg="不支持该系统")
        return successjson()
    def getseradd():
        authkey=md5(randoms())
        set_cache("websocket",authkey,10)
        set_cache(str(G.userinfo['id']),G.userinfo,10)
        set_cache("socket_server_ip",request.HEADER.HTTP_HOST().split(":")[0],0)
        # return successjson("ws://"+request.HEADER.HTTP_HOST().split(":")[0]+":39030?authkey="+authkey+"&uid="+str(G.userinfo['id']))
        if len(request.HEADER.HTTP_HOST().split(":"))>1:
            return successjson("//"+request.HEADER.HTTP_HOST().split(":")[0]+":39030?authkey="+authkey+"&uid="+str(G.userinfo['id']))
        else:
            return successjson("//"+request.HEADER.HTTP_HOST()+"/index/index/ws?authkey="+authkey+"&uid="+str(G.userinfo['id']))
socket_client_ws=None
socket_client_connectiontime=0
class socket_client():
    #websocket客户端
    group_id=''
    socket_server_ip=''
    def __init(self):
        global socket_client_ws
        global socket_client_connectiontime
        if not self.socket_server_ip:
            self.socket_server_ip=get_cache('socket_server_ip')
            if not self.socket_server_ip:
                print("未初始，可打通讯日志页面进行初始化")
                return False
        if times()-socket_client_connectiontime>3600:
            if socket_client_ws:
                try:
                    socket_client_ws.close()
                except:pass
            socket_client_ws=None
        if not socket_client_ws:
            import websocket #websocket客户端
            try:
                self.group_id=''
                userinfo=sqlite("admin",model_app_path).order("id asc").find()
                set_cache(str(userinfo['id']),userinfo,60)
                url="ws://"+self.socket_server_ip+":39030?authkey=send_authkey_frdsgedsgvdsgvgdfsdgtdrfdsfdgvffdsfdsvfgd352esdgfs&uid="+str(userinfo['id'])
                socket_client_ws = websocket.create_connection(url)
                socket_client_connectiontime=times()
            except Exception as e:
                print("无法连接:",url,e)
                print("可打通讯日志页面进行初始化后重试，或检查当前地址是否可以访问")
                return False
        return True
    def send(self,content,group_id=1):
        "客户端发送消息"
        global socket_client_ws
        group_id=str(group_id)
        types='broadcast'
        if not self.__init():
            print(timestampToDate(times()),"连接失败")
            return False
        try:
            try:
                if group_id!=self.group_id:
                    self.group_id=group_id
                    socket_client_ws.send(json_encode({
                        'group_id':group_id,'types':'joinGroup','content':''
                    }))
                    time.sleep(0.1)
                socket_client_ws.send(json_encode({
                    'group_id':group_id,'types':str(types),'content':content
                }))
                return True
            except Exception as e:
                try:
                    socket_client_ws.close()
                except:pass
                else:
                    socket_client_ws=None
                if '你的主机中的软件中止了一个已建立的连接' in str(e) or '远程主机强迫关闭了一个现有的连接' in str(e):
                    if not self.__init():
                        print(timestampToDate(times()),"连接失败")
                        return False
                    try:
                        if group_id!=self.group_id:
                            self.group_id=group_id
                            socket_client_ws.send(json_encode({
                                'group_id':group_id,'types':'joinGroup','content':''
                            }))
                            time.sleep(0.1)
                        socket_client_ws.send(json_encode({
                            'group_id':group_id,'types':str(types),'content':content
                        }))
                        return True
                    except Exception as e:
                        return False
                else:
                    return False
        except:
            return False

