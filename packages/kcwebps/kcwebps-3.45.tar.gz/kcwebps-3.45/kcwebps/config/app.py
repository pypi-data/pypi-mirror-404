# -*- coding: utf-8 -*-
from .database import *
app['app_debug']=True  #是否开启调试模式
app['tpl_folder']='./app'  #设置模板文件目录名 注意：所有的配置目录都是以您的运行文件所在目录开始
app['before_request']='before_request'  #设置请求前要执行的函数名
app['after_request']='after_request'    #设置请求后要执行的函数名
app['staticpath']='app/static'          #静态主要目录
app['appmode']='develop'  #produc 生产环境  develop 开发环境
app['save_cli_pid']=True #是否开启cli运行时保存pid

# session配置
session['type']='File' #session 存储类型  支持 File,Redis,Python
session['path']='./app/runtime/session/temp' #session缓存目录
session['expire']=86400*30 #session默认有效期 该时间是指session在服务的保留时间，通常情况下浏览器上会保留该值的10倍
session['prefix']="kcws" # SESSION 前缀
session['host']=redis['host'] #Redis服务器地址
session['port']=redis['port'] #Redis 端口
session['password']=redis['password'] #Redis登录密码
session['db']=1 #Redis数据库    注：Redis用1或2或3等表示

#缓存配置
cache['type']='File' #驱动方式 支持 File,Redis,Python 
cache['path']='./app/runtime/cachepath' #缓存保存目录 
cache['expire']=120 #缓存有效期 0表示永久缓存
cache['host']=redis['host'] #Redis服务器地址
cache['port']=redis['port'] #Redis 端口
cache['password']=redis['password'] #Redis登录密码
cache['db']=2 #Redis数据库    注：Redis用1或2或3等表示

#email配置
email['sender']='' #发件人邮箱账号
email['pwd']='' #发件人邮箱密码(如申请的smtp给的口令)
email['sendNick']='' #发件人昵称
email['theme']='' #默认主题
email['recNick']='' #默认收件人昵称

#路由配置
route['default']=True #是否开启默认路由  默认路由开启后面不影响以下配置的路由，模块名/版本名/控制器文件名/方法名 作为路由地址   如：http://www.kcws.com/modular/plug/index/index/
route['modular']=[{"kcwebsapi":"official"},{"docs":"official"},{"bank":"fund"}] #指定访问配置固定模块 （如果匹配了该值，将无法通过改变url访问不同模块）
route['plug']=[{"kcwebsapi":"kcwebapi"},{"docs":"docs"},{"bank":"bank"}] #指定访问固定插件 （如果匹配了该值，将无法通过改变url访问不同插件）
route['defmodular']='index' #默认模块 当url不包括模块名时
route['defplug']='index' #默认插件 当url不包括插件名时
route['files']='index' #默认路由文件（控制器） 当url不包括控制器名时
route['funct']='index'  #默认路由函数 (操作方法) 当url不包括操作方法名时
route['methods']=['POST','GET','DELETE','PUT','OPTIONS'] #默认请求方式
route['children']=[
    {'title':'公共js','path':'/public/h5.js','component':'intapp/index/pub/script','methods':['GET']},
]



