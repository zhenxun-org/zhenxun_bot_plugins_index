from typing import List, Text
import httpx
import asyncio
from nonebot.adapters.cqhttp.message import MessageSegment
from os import link, stat
from nonebot.log import logger
null=""
head={"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36 Edg/92.0.902.78"}
async def UserInfo(mid:str):#返回格式为状态码(int),用户名(str)，直播间存在(int)
    param={'mid':mid,'jsonp':'jsonp'}
    url="https://api.bilibili.com/x/space/acc/info"
    async with httpx.AsyncClient() as client:
        try:
            re=await client.get(url=url,headers=head,params=param)
        except:
            logger.error('获取用户信息失败')
            return -1,'',0
        data=re.json()
    status=data['code']
    if(status!=0):
        return status,'',0
    Name = data['data']['name']
    LiveRoom=data['data']['live_room']
    RoomStatus=LiveRoom['roomStatus']#1为直播间存在
    return status,Name,RoomStatus
async def LiveRoomInfo(mid:str):#返回格式为状态码(int),直播状态码(int)，推送内容
    param={'mid':mid,'jsonp':'jsonp'}
    url="https://api.bilibili.com/x/space/acc/info"
    async with httpx.AsyncClient() as client:
        try:
            re=await client.get(url=url,headers=head,params=param)
        except:
            logger.error('更新直播间信息失败')
            return -1,0,''
        data=re.json()
    status=data['code']
    if(status!=0):
        return status,0,''
    LiveRoom=data['data']['live_room']
    Name = data['data']['name']
    LiveStatus=LiveRoom['liveStatus']#1为直播中
    LiveURL=LiveRoom['url']
    LiveTitle=LiveRoom['title']
    LiveCover=LiveRoom['cover']
    text=str(LiveStatus).replace('1','开播').replace('0','下播')
    return status,LiveStatus,'您关注的 {} {}了！\n'.format(Name,text)+'直播间标题：\n'+LiveTitle+'\n'+MessageSegment.image(LiveCover)+'\n'+'直播间链接：\n'+LiveURL
async def DynamicInfo(DynamicID:str) ->str:
    param={'dynamic_id':DynamicID}
    url='http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/get_dynamic_detail'
    async with httpx.AsyncClient() as client:
        try:
            re=await client.get(url=url,headers=head,params=param)
        except:
            logger.error('原始动态获取失败')
            return '原始动态获取失败'
        data=re.json()
    status=data['code']
    if(status!=0):
        return '原始动态获取失败'
    Dynamic=data['data']['card']
    Name=Dynamic['desc']['user_profile']['info']['uname']
    DynamicType=Dynamic['desc']['type']
    if DynamicType==8:#视频动态
        Details=eval(Dynamic['card'])
        BV=Dynamic['desc']['bvid']
        Dynamic=Details['dynamic'].replace('\\n','\n').replace('\/','/')
        VideoTitle=Details['title'].replace('\/','/')
        VideoCover=MessageSegment.image(Details['pic'].replace('\/','/'))
        VideoIntroduction=Details['desc'].replace('\\n','\n').replace('\/','/')
        VideoURL='https://b23.tv/'+BV
        return "原动态：\n{} 投稿了视频：\n{}\n{}\n{}\n{}\n视频链接：\n{}".format(Name,Dynamic,VideoTitle,VideoIntroduction,VideoCover,VideoURL)
    elif DynamicType==2:#图片动态
        Details=eval(Dynamic['card'])
        Dynamic=Details['item']['description'].replace('\\n','\n').replace('\/','/')
        Pictures=Details['item']['pictures'] #[0]['img_src']
        Text=''
        for index in Pictures:
            Text+=MessageSegment.image(index['img_src'].replace('\/','/'))+'\n'
        return "原动态：\n{} 发表了动态：\n{}\n{}".format(Name,Dynamic,Text)
    elif DynamicType==4:#文字动态
        Details=eval(Dynamic['card'])
        Dynamic=Details['item']['content'].replace('\\n','\n').replace('\/','/')
        return "原动态：\n{} 发表了动态：\n{}".format(Name,Dynamic)
    else:
        return "原动态：\n{} 发表了动态：\n不支持的动态类型".format(Name)
async def LatestDynamicInfo(mid:str):#状态码，动态ID，动态内容
    param={'host_uid':mid,'offset_dynamic_id':'0'}
    url='http://api.vc.bilibili.com/dynamic_svr/v1/dynamic_svr/space_history'
    async with httpx.AsyncClient() as client:
        try:
            re=await client.get(url=url,headers=head,params=param)
        except:
            logger.error('更新动态信息失败')
            return -1,'',''
        data=re.json()
    status=data['code']#0为成功，其它均为失败
    if(status!=0):
        return status,'',''
    LatestDynamic=data['data']['cards'][0]
    LatestDynamicID=LatestDynamic['desc']['dynamic_id_str']
    Name=LatestDynamic['desc']['user_profile']['info']['uname']
    LatestDynamicURLMobile='https://m.bilibili.com/dynamic/'+LatestDynamicID
    DynamicType=LatestDynamic['desc']['type'] 
    if DynamicType==8:#视频动态
        Details=eval(LatestDynamic['card'])
        BV=LatestDynamic['desc']['bvid']
        Dynamic=Details['dynamic'].replace('\\n','\n').replace('\/','/')
        VideoTitle=Details['title'].replace('\/','/')
        VideoCover=MessageSegment.image(Details['pic'].replace('\/','/'))
        VideoIntroduction=Details['desc'].replace('\\n','\n').replace('\/','/')
        VideoURL='https://b23.tv/'+BV
        return status,LatestDynamicID,'您关注的 {} 投稿了新视频：\n'.format(Name)+Dynamic+'\n'+VideoTitle+'\n'+VideoIntroduction+'\n'+VideoCover+'\n'+'视频链接：\n'+VideoURL
    elif DynamicType==2:#图片动态
        Details=eval(LatestDynamic['card'])
        Dynamic=Details['item']['description'].replace('\\n','\n').replace('\/','/')
        Pictures=Details['item']['pictures'] #[0]['img_src']
        Text=''
        for index in Pictures:
            Text+=MessageSegment.image(index['img_src'].replace('\/','/'))+'\n'
        return status,LatestDynamicID,'您关注的 {} 发布了新动态：\n'.format(Name)+Dynamic+'\n'+Text+'动态链接：\n'+LatestDynamicURLMobile
    elif DynamicType==4:#文字动态
        Details=eval(LatestDynamic['card'])
        Dynamic=Details['item']['content'].replace('\\n','\n').replace('\/','/')
        return status,LatestDynamicID,'您关注的 {} 发布了新动态：\n'.format(Name)+Dynamic+'\n'+'动态链接：\n'+LatestDynamicURLMobile
    elif DynamicType==1:#转发动态
        Details=eval(LatestDynamic['card'])
        OringinalDynamic=LatestDynamic['desc']['orig_dy_id_str']
        Dynamic=Details['item']['content'].replace('\\n','\n').replace('\/','/')
        origin=await DynamicInfo(OringinalDynamic)
        return status,LatestDynamicID,'您关注的 {} 发布了新动态：\n'.format(Name)+Dynamic+'\n'+origin+'\n'+'动态链接：\n'+LatestDynamicURLMobile
    else:#其它
        return status,LatestDynamicID,'您关注的 {} 发布了新动态：\n不支持的动态类型\n'.format(Name)+'动态链接：\n'+LatestDynamicURLMobile
#[CQ:image,file={}]
