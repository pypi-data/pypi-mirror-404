
# 打包上传 python setup.py sdist upload
# 打包并安装 python setup.py sdist install
# twine upload --repository-url https://test.pypi.org/legacy/ dist/* #上传到测试
# pip install --index-url https://pypi.org/simple/ kcwebs   #安装测试服务上的kcwebs pip3 install kcwebs==4.12.4 -i https://pypi.org/simple/
# 安装 python setup.py install
#############################################  pip3.8 install kcwebs==6.4.15 -i https://pypi.org/simple
import os,sys
from setuptools import setup
from kcwebs import kcwebsinfo
confkcws={}
confkcws['name']=kcwebsinfo['name']                             #项目的名称 
confkcws['version']=kcwebsinfo['version']							#项目版本
confkcws['description']=kcwebsinfo['description']       #项目的简单描述
confkcws['long_description']=kcwebsinfo['long_description']     #项目详细描述
confkcws['license']=kcwebsinfo['license']                    #开源协议   mit开源
confkcws['url']=kcwebsinfo['url']
confkcws['author']=kcwebsinfo['author']  					 #名字
confkcws['author_email']=kcwebsinfo['author_email'] 	     #邮件地址
confkcws['maintainer']=kcwebsinfo['maintainer'] 						 #维护人员的名字
confkcws['maintainer_email']=kcwebsinfo['maintainer_email']    #维护人员的邮件地址
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
    b=get_file("kcwebs",['kcwebs'])
    setup(
        name = confkcws["name"],
        version = confkcws["version"],
        keywords = "kcwebs"+confkcws['version'],
        description = confkcws["description"],
        long_description = confkcws["long_description"],
        license = confkcws["license"],
        author = confkcws["author"],
        author_email = confkcws["author_email"],
        maintainer = confkcws["maintainer"],
        maintainer_email = confkcws["maintainer_email"],
        url=confkcws['url'],
        packages =  b,

        
        install_requires = ['kcws>='+kcwebsinfo['version'],'kcwmysql>='+kcwebsinfo['version'],'kcwsqlite>='+kcwebsinfo['version'],'kcwhttp>='+kcwebsinfo['version'],'python-dateutil==2.9.0',
                            'pymongo==3.10.0','Mako==1.3.6','six>=1.12.0',
                            # 'websockets==10.4',
                            'curl_cffi==0.9.0',
                            'websockets==8.1',
                            ], #第三方包
        package_data = {
            '': ['*.html', '*.js','*.css','*.jpg','*.png','*.gif'],
        },
        entry_points = {
            'console_scripts':[
                'kcwebs = kcwebs.kcwebs:cill_start'
            ]
        }
    )
start()