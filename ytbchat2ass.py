# -*- coding:utf-8 -*-
from chat_downloader import ChatDownloader
import sys
import math
import urllib.request
import re
import argparse

# 目前仅支持开启了chat的回放，看不懂chat-downloader的源代码，甚至不想把直播安排进todo


def sec2hms(sec):  # 时间转换
    hms = str(int(sec//3600)).zfill(2)+':' + str(int((sec % 3600)//60)).zfill(2)+':'+str(round(sec % 60, 2))
    return hms


def chat2ass(code, name, delay):
    url = "https://www.youtube.com/watch?v="+code
    html = urllib.request.urlopen(url).read().decode('utf-8')
    names = [name]
    title = re.findall("<title>(.+?)</title>", html)[0].replace(' - YouTube', '')
    names += re.findall('itemprop="name" content="(.+?)">', html)
    chat = ChatDownloader().get_chat(url, message_groups=['messages', 'superchat'])  # 默认普通评论和sc
    count = 0
    limitLineAmount = 12  # 屏上弹幕行数限制
    danmakuPassageway = []  # 塞弹幕用，记录每行上一条弹幕的消失时间
    for i in range(limitLineAmount):
        danmakuPassageway.append(0)
    fontName = 'Source Han Sans JP'  # 字体自己换
    videoWidth = 1280  # 视频宽度，按720P处理了后面的内容，不建议改
    videoHeight = 720  # 视频高度
    OfficeBgHeight = 72
    OfficeSize = 36
    fontSize = 58
    head = '[Script Info]\n\
; Script generated by Aegisub 3.2.2\n\
; http://www.aegisub.org/\n\
ScriptType: v4.00+\n\
PlayResX: 1280\n\
PlayResY: 720\n\
\n\
[V4+ Styles]\n\
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, marginL, marginR, marginV, Encoding\n\
Style: Default,微软雅黑,54,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,0,0,0,0\n\
Style: Alternate,微软雅黑,36,&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,0,0,0,0\n\
Style: Office,'+fontName+','+str(OfficeSize)+',&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,1.5,0,2,0,0,10,0\n\
Style: Danmaku,'+fontName+','+str(fontSize)+',&H00FFFFFF,&H00FFFFFF,&H00000000,&H00000000,-1,0,0,0,100,100,2,0,1,1.5,0,2,0,0,10,0\n\n\
[Events]\n\
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n\
Comment: 0,00:00:00.0,00:00:00.0,Danmaku,标题,0,0,0,,'+title+'\n'

    f = open(code+'.ass', 'w', encoding='utf-8-sig')
    f.write(head)
    for message in chat:
        vpos = message['time_in_seconds'] - int(delay)
        if vpos > 0:
            vpos_end = vpos+8  # 普通弹幕的时长，默认8秒
        else:
            continue
        if 'name' not in message['author'].keys():
            continue
        if 'money' in message.keys():
            text = '('+str(message['money']['amount']) + message['money']['currency']+')'  # 打钱的标上数额
            if 'message' in message.keys():
                if message['message']:
                    text += message['message']  # 打钱有留言的加上
            vpos_end += 2  # 打钱的多给2秒
        else:
            # 没打钱的直接记录弹幕，设置了的号加上账号名字
            text = message['author']['name']+'： ' + message['message'] if message['author']['name'] in name else message['message']
        if 'emotes' in message.keys():
            for i in message['emotes']:
                if i['is_custom_emoji']:
                    text = text.replace(i['name'], '')
                else:
                    text = text.replace(i['name'], i['id'])
        if text:
            if len(text) == 0:
                continue
        else:
            continue
        if message['author']['name'] in name:  # 特定账号的弹幕放上面并加上背景
            f.write('Dialogue: 4,'+sec2hms(vpos)+','+sec2hms(vpos_end)+',Office,,0,0,0,,{\\an5\\p1\\pos('+str(videoWidth/2)+','+str(math.floor(OfficeBgHeight/2))+')\\bord0\\1c&H000000&\\1a&H78&}'+'m 0 0 l '+str(videoWidth)+' 0 l '+str(videoWidth) + ' '+str(OfficeBgHeight)+' l 0 '+str(OfficeBgHeight)+'\n')
            f.write('Dialogue: 5,'+sec2hms(vpos)+','+sec2hms(vpos_end)+',Office,,0,0,0,,{\\an5\\pos('+str(videoWidth/2)+','+str(math.floor(OfficeBgHeight/2))+')\\bord0\\fsp0}'+text+'\n')
            count += 1
        else:  # 其他人的弹幕放滚动
            vpos_next_min = float('inf')
            vpos_next = vpos+1280/(len(text)*60+1280) * 8
            for i in range(limitLineAmount):
                if vpos_next >= danmakuPassageway[i]:
                    passageway_index = i
                    danmakuPassageway[i] = vpos+8
                    break
                elif danmakuPassageway[i] < vpos_next_min:
                    vpos_next_min = danmakuPassageway[i]
                    Passageway_min = i
                if i == limitLineAmount-1 and vpos_next < vpos_next_min:
                    passageway_index = Passageway_min
                    danmakuPassageway[Passageway_min] = vpos+8
            # 计算弹幕位置
            sx = videoWidth
            sy = fontSize*(passageway_index)
            ex = 0
            for i in text:
                if re.search("[A-Za-z 0-9',.]", i):
                    ex = ex-30
                else:
                    ex = ex-60
            ey = fontSize*(passageway_index)
            f.write('Dialogue: 0,'+sec2hms(vpos)+',' + sec2hms(vpos_end) + ',Danmaku,'+message['author']['name'].replace(',', '')+',0,0,0,,{\\an7\\move('+str(sx)+','+str(sy)+','+str(ex)+','+str(ey)+')}'+text+'\n')
            count += 1
    f.close()
    print(title+'的弹幕已经存为'+sys.argv[1]+'.ass,共'+str(count)+'条')


def main():
    if len(sys.argv) == 1:
        sys.argv.append('--help')
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', metavar='str', help='除主播外，需将弹幕显示在上方的账号')
    parser.add_argument('-d', '--delay', metavar='str', help='弹幕延迟，一般适用于首播')
    parser.add_argument('code', metavar='str', help='该视频的编号，如youtu.be/tWXPP1tvuIU或www.youtube.com/watch?v=tWXPP1tvuIU中的tWXPP1tvuIU')
    args = parser.parse_args()
    if args.code:
        if not args.name:
            args.name = ''
        if not args.delay:
            args.delay = 0
        chat2ass(args.code, args.name, args.delay)


if __name__ == '__main__':
    main()
