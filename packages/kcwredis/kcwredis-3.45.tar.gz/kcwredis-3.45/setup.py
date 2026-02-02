
# 打包上传 python setup.py sdist upload
# 打包并安装 python setup.py sdist install
# twine upload --repository-url https://test.pypi.org/legacy/ dist/* #上传到测试
# pip install --index-url https://pypi.org/simple/ kcwebs   #安装测试服务上的kcwebs pip3 install kcwebs==4.12.4 -i https://pypi.org/simple/
# 安装 python setup.py install
#############################################  pip3.8 install kcwebs==6.4.15 -i https://pypi.org/simple
import os,sys
from kcwredis import __version__
from setuptools import setup
confkcws={}
confkcws['name']='kcwredis'
confkcws['version']=__version__
confkcws['description']='kcwcache'
confkcws['long_description']=''
confkcws['license']='MIT License'
confkcws['url']=''
confkcws['author']='百里'
confkcws['author_email']='kcwebs@kwebapp.cn'
confkcws['maintainer']='坤坤'
confkcws['maintainer_email']='fk1402936534@qq.com'
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
    b=get_file("kcwredis",['kcwredis'])
    setup(
        name = confkcws["name"],
        version = confkcws["version"],
        keywords = "kcwredis"+confkcws['version'],
        description = confkcws["description"],
        long_description = confkcws["long_description"],
        license = confkcws["license"],
        author = confkcws["author"],
        author_email = confkcws["author_email"],
        maintainer = confkcws["maintainer"],
        maintainer_email = confkcws["maintainer_email"],
        url=confkcws['url'],
        packages =  b,

        
        install_requires = ['redis==3.3.8'], #第三方包
        package_data = {
            '': ['*.html', '*.js','*.css','*.jpg','*.png','*.gif'],
        }
    )
start()