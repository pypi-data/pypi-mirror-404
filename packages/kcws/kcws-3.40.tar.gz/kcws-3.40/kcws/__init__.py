# -*- coding: utf-8 -*-
__version__ = '3.40'
try:
    from .app import web
except:
    print('警告：from .app import web导入失败')
# from . import config
kcwsinfo={}
kcwsinfo['name']='kcws'                             #项目的名称
kcwsinfo['version']=__version__							#项目版本
kcwsinfo['description']='kcwebs作为web开发而设计的高性能框架'       #项目的简单描述
kcwsinfo['long_description']='kcwebs作为web开发而设计的高性能框架，采用全新的架构思想，注重易用性。遵循MIT开源许可协议发布，意味着个人和企业可以免费使用kcwebs，甚至允许把你基于kcwebs开发的应用开源或商业产品发布或销售。完整文档请访问：https://docs.kwebapp.cn/index/index/2'     #项目详细描述
kcwsinfo['license']='MIT License'                    #开源协议   mit开源
kcwsinfo['url']='https://docs.kwebapp.cn/index/index/2'
kcwsinfo['author']='百里-坤坤'  					 #名字
kcwsinfo['author_email']='kcwebs@kwebapp.cn' 	     #邮件地址
kcwsinfo['maintainer']='坤坤' 						 #维护人员的名字
kcwsinfo['maintainer_email']='fk1402936534@qq.com'    #维护人员的邮件地址