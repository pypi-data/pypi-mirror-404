
import re
def error(e,data):
    try:
        plug=str(e).split("has no attribute")[1]
        plug=re.sub("[' ]","",plug)
    except:
        plug=''
    header={"Content-Type":"application/json; charset=utf-8","Access-Control-Allow-Origin":"*"}
    header['Location']="/index/index/plug/index/intapp/"+plug
    return '{"code":1,"msg":"您访问的地址不存在","data":"'+str(e)+'"}','302 Found',header 
from . import index