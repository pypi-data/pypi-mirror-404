
# 打包上传 python setup.py sdist upload
# 打包并安装 python setup.py sdist install
# twine upload --repository-url https://test.pypi.org/legacy/ dist/* #上传到测试
# pip install --index-url https://pypi.org/simple/ kcwebs   #安装测试服务上的kcwebs pip3 install kcwebs==4.12.4 -i https://pypi.org/simple/
# 安装 python setup.py install 
#############################################
import os,sys
from setuptools import setup
from kcws import kcwsinfo
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
    b=get_file("kcws",['kcws'])
    setup(
        name = kcwsinfo["name"],
        version = kcwsinfo["version"],
        keywords = "kcws"+kcwsinfo['version'],
        description = kcwsinfo["description"],
        long_description = kcwsinfo["long_description"],
        license = kcwsinfo["license"],
        author = kcwsinfo["author"],
        author_email = kcwsinfo["author_email"],
        maintainer = kcwsinfo["maintainer"],
        maintainer_email = kcwsinfo["maintainer_email"],
        url=kcwsinfo['url'],
        packages =  b,
        install_requires = ['gunicorn==20.0.4','watchdog==4.0.0','filetype==1.2.0','psutil==5.8.0','requests==2.32.4'], #第三方包
        package_data = {
            '': ['*.html', '*.js','*.css','*.jpg','*.png','*.gif'],
        },
        entry_points = {
            'console_scripts':[
                'kcws = kcws.kcws:cill_start'
            ]
        }
    )
start()