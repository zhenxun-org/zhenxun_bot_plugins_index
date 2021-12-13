import sqlite3
from typing import List
from nonebot.log import logger
def Init():
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select count(*) from sqlite_master where type="table" and name = "anchor_list"')
    if CUR.fetchall()[0][0]==0:
        CUR.execute('create table anchor_list (id TEXT,name TEXT,dynamic_id TEXT,live_exist INTEGER,live_status INTEGER)')
        DB.commit()
    CUR.close()
    DB.close()
def AddNewAnchor(Mid:str,anchor:str,live_exist:int):#创建主播对应的表
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    Name='_'+Mid
    CUR.execute('select count(*) from sqlite_master where type="table" and name = "{}"'.format(Name))
    if CUR.fetchall()[0][0]==0:
        CUR.execute("create table {} (id TEXT,is_group INTEGER,dynamic INTEGER,live INTEGER,at INTEGER)".format(Name))
        CUR.execute('insert into anchor_list values("{}","{}","",{},0)'.format(Mid,anchor,live_exist))
        DB.commit()
    else:
        logger.warning("主播记录已存在！")
    CUR.close()
    DB.close()
def AddCard(Mid:str,ID:str,group:int,Live:int=1)->int: #添加主播信息 返回类型 记录是否已存在(int)1：存在
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    Name='_'+Mid
    CUR.execute('select count(*) from {} where id="{}" and is_group={}'.format(Name,ID,group))
    if CUR.fetchall()[0][0] !=0:
        logger.warning('当前群组/私聊记录已存在！')
        return 1
    CUR.execute('insert into {} values("{}",{},{},{},{})'.format(Name,ID,str(group),str(1),str(Live),str(0)))
    DB.commit()
    CUR.close()
    DB.close()
    return 0
def DeleteCard(Mid:str,ID:str,group:int):#删除主播信息 返回类型 删除是否成功(int)1:失败 ：成功
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    Name='_'+Mid
    CUR.execute('select count(*) from {} where id="{}" and is_group={}'.format(Name,ID,group))
    if CUR.fetchall()[0][0]==0:
        logger.error('记录不存在！删除失败！')
        return 1
    CUR.execute('delete from {} where id="{}" and is_group={}'.format(Name,ID,group))
    CUR.execute('select count(*) from {}'.format(Name))
    if CUR.fetchall()[0][0]==0:
        CUR.execute('drop table {}'.format(Name))
        CUR.execute('delete from anchor_list where id="{}"'.format(Mid))
    DB.commit()
    CUR.close()
    DB.close()
    return 0
def DeleteGroupCard(ID:str):#删除群聊全部关注列表
    anchors=GetAnchorList()
    for anchor in anchors:
        DeleteCard(anchor[0],ID,1)
def GetCard(Mid:str,ID:str,group:int):#获取主播信息
    res=[]
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select * from {} where id="{}" and is_group={}'.format(Name,ID,group))
    data=CUR.fetchall()
    if len(data)==0:
        CUR.close()
        DB.close()
        return res
    else:
        res=data[0]
        CUR.close()
        DB.close()
        return res
def GetALLCard(Mid:str):#获取全部信息
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select * from {}'.format(Name))
    data=CUR.fetchall()
    CUR.close()
    DB.close()
    return data
def DynamicON(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set dynamic=1 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def DynamicOFF(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set dynamic=0 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def LiveON(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set live=1 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def LiveOFF(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set live=0 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def AtON(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set at=1 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def AtOFF(Mid:str,ID:str,group:int):
    Name='_'+Mid
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update {} set at=0 where id="{}" and is_group={}'.format(Name,ID,group))
    DB.commit()
    CUR.close()
    DB.close()
def GetAnchorList()->List:
    res=[]
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select * from anchor_list')
    data=CUR.fetchall()
    if len(data)==0:
        CUR.close()
        DB.close()
        return res
    for index in data:
        res.append(index)
    CUR.close()
    DB.close()
    return res
def GetAnchorInfo(mid:str)->List:
    res=[]
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select * from anchor_list where id="{}"'.format(mid))
    data=CUR.fetchall()
    if len(data)!=0:
        res=data[0]
    CUR.close()
    DB.close()
    return res
def UpdateLive(mid:str,status:int):
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update anchor_list set live_status={} where id="{}"'.format(status,mid))
    DB.commit()
    CUR.close()
    DB.close()
def UpdateDynamic(mid:str,dynamicid:str):
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('update anchor_list set dynamic_id="{}" where id="{}"'.format(dynamicid,mid))
    DB.commit()
    CUR.close()
    DB.close()
def Empty()->bool:#全局主播列表为空
    DB=sqlite3.connect('bilibili.db')
    CUR=DB.cursor()
    CUR.execute('select count(*) from anchor_list')
    if CUR.fetchall()[0][0]==0:
        CUR.close()
        DB.close()
        return True
    else:
        CUR.close()
        DB.close()
        return False
    