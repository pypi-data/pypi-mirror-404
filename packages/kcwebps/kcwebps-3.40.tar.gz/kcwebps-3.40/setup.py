
# 打包上传 python setup.py sdist upload
# 打包并安装 python setup.py sdist install
############################################# pip3.8 install kcwebps==3.1.62 -i https://pypi.org/simple
import os,sys
from setuptools import setup
from kcwebps import kcwebpsinfo
confkcws={}
confkcws['name']=kcwebpsinfo['name']                             #项目的名称 
confkcws['version']=kcwebpsinfo['version']							#项目版本
confkcws['description']=kcwebpsinfo['description']       #项目的简单描述
confkcws['long_description']=kcwebpsinfo['long_description']     #项目详细描述
confkcws['license']=kcwebpsinfo['license']                    #开源协议   mit开源
confkcws['url']=kcwebpsinfo['url']
confkcws['author']=kcwebpsinfo['author']  					 #名字
confkcws['author_email']=kcwebpsinfo['author_email'] 	     #邮件地址
confkcws['maintainer']=kcwebpsinfo['maintainer'] 						 #维护人员的名字
confkcws['maintainer_email']=kcwebpsinfo['maintainer_email']    #维护人员的邮件地址
def get_file(folder='./',lists=[]):
    lis=os.listdir(folder)
    for files in lis:
        if not os.path.isfile(folder+"/"+files):
            if files=='__pycache__' or files=='.git':
                pass
            else:
                lists.append(folder+"/"+files)
                get_file(folder+"/"+files,lists)
        else:
            pass
    return lists
def start():
    b=get_file("kcwebps",['kcwebps'])
    setup(
        name = confkcws["name"],
        version = confkcws["version"],
        keywords = "kcwebps"+confkcws['version'],
        description = confkcws["description"],
        long_description = confkcws["long_description"],
        license = confkcws["license"],
        author = confkcws["author"],
        author_email = confkcws["author_email"],
        maintainer = confkcws["maintainer"],
        maintainer_email = confkcws["maintainer_email"],
        url=confkcws['url'],
        packages =  b,
        install_requires = ['kcwebs>='+kcwebpsinfo['version'],'pyOpenSSL==23.2.0','cryptography==41.0.7','chardet==4.0.0','apscheduler==3.6.3','oss2>=2.12.1','websocket-client==1.8.0'], #第三方包 'pyOpenSSL==23.2.0','cryptography==41.0.7'
        package_data = {
            '': ['*.html', '*.js','*.css','*.jpg','*.png','*.gif','server.bat','*.sh','*.md','*sqlite/app','*sqlite/index_index','*.config','*file/config.conf'],
        },
        entry_points = {
            'console_scripts':[
                'kcwebps = kcwebps.kcwebps:cill_start'
            ]
        }
    )
start()