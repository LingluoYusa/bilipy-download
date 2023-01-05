# bili视频解析程序
# edition 0.3
# creation_time 2022/04/24

import json
from typing import List
import requests
import time
import os

# 变量参数
filepath = 'Z:/bili下载'
sessdata = 'f0035cb8%2C1666429052%2C8224d*41'  # <-- SESSDATA参数填写到本行的引号里

# 公共参数
aid = 0
bid = ''
cid = 0
epcid = []
epurl = []
apd = False
bpd = 0  # 0-初始 1-BV视频 2-ep番剧
cpd = False
fpbv = 0  # 分P参数
drbv = False  # 联合投稿参数
drname = ''
rcid = {}  # cid返回值
bvname = ''
rurls = ''
cidXml = ''

# 调试模式开关
ts = False

print('BILIBILI视频解析程序')
print("{:-^90s}".format(""))
# 参数检查
lensessdata = len(sessdata)
if sessdata == '':
    print('× 警告！未填写SESSDATA参数，可能导致[1080P60FLV视频流]获取异常')
    pass
elif lensessdata != 32:
    print('× 警告！SESSDATA参数异常，请检查是否正确填写')
    pass
else:
    print('√ SESSDATA参数检查通过 如果下载的视频清晰度不对请注意该参数是否过期或填写错误')
    pass
if filepath == '':
    print('× 警告！未填写下载地址路径，将无法调用aria2下载')
    pass
elif os.path.isfile(filepath):
    print('× 警告！下载地址路径目标为一个文件,将无法调用aria2下载')
    pass
elif not os.path.isdir(filepath):
    print('× 警告！下载地址路径不存在，开始下载时将在此处创建文件夹')
    print('  ', filepath)
    pass
elif os.path.isdir(filepath):
    print('√ filepath参数检查通过 下载路径为>>', filepath)
    pass
else:
    print('× 系统未知错误')
print()

while True:
    srurl = input('请输入视频链接：')
    # 视频链接中提取bid并检查是否有分P
    httpbv = srurl.split('://')[-1].split('video/')[0]
    rfpbv = srurl.split('?p=')[-1]
    if httpbv.startswith('www.bilibili.com/'):
        # 检查是否为BV视频
        if srurl.find('BV') != -1:
            bv = (srurl.split('BV')[1])[0:10]
            bid = ('BV' + bv)
            print("{:-^90s}".format(""))
            print('√ [0]BV号提取成功：%s' % bid)

            # 检查是否有分P
            if srurl.find('?p=') != -1:
                fpbv = int(rfpbv) - 1
                print('   发现分P参数 执行下载%sP' % (fpbv + 1))
                pass
            elif srurl.find('?p=') == -1:
                print('   未发现分P参数 执行默认下载')
                pass

            time.sleep(0.5)
            bpd = 1
            break
            pass
        # 检查是否为ep番剧
        elif srurl.find('ss') != -1:
            ss = (srurl.split('ss')[1])[0:5]
            bid = ss
            print("{:-^90s}".format(""))
            print('■ 提示：进入B站番剧下载 SESSDATA填写错误会导致下载出错！')
            print('√ [0]EP号提取成功：%s' % bid)
            bpd = 2
            time.sleep(1)
            break
            pass
        else:
            print('× 未检查到视频/番剧编号，请重新输入')
            print()
            continue
            pass
    else:
        print('× 未检查到b站链接，请重新输入')
        print()
        continue
        pass
    pass

if bpd == 1:
    # 通过bid获取cid(bv)
    apicid = requests.get("https://api.bilibili.com/x/player/pagelist?bvid=%s" % bid)
    rcid = json.loads(apicid.content)
    if ts:
        # 调试显示cid返回值
        print()
        print("[ts]apicid %s" % apicid)
        print("[ts]获取cid返回", rcid)
        print()
        pass

    # 判断rcid的状态并显示
    if rcid['code'] == 0:
        cid = rcid['data'][fpbv]['cid']
        print("√ [1]CID获取成功: ", cid)
        cpd = True
        time.sleep(0.5)
        pass
    else:
        cidcode = rcid['code']
        cidmsg = rcid['message']
        print('× [1]警告！cid获取失败 错误码：%s 检查结果：%s' % (cidcode, cidmsg))
        pass
    pass

if bpd == 1 and cpd == True:
    # 通过bid和cid获取aid(bv)
    apiaid = requests.get("https://api.bilibili.com/x/web-interface/view?cid=%s&bvid=%s" % (cid, bid))
    raid = json.loads(apiaid.content)
    if ts:
        # 调试显示aid返回值
        print()
        print("[ts]apiaid %s" % apiaid)
        print("[ts]获取aid返回", raid)
        print()
        pass

    # 判断raid的状态并显示
    if raid['code'] == 0:
        aid = raid['data']['aid']
        print("√ [2]AID获取成功: ", aid)
        time.sleep(0.5)

        # 检查是否存在多个发布UP
        if 'staff' in raid['data']:
            drbv = True
            for i in raid['data']['staff']:
                # print(i['name'])
                drname = drname + i['name'] + ' '
                pass

        # 算法验证模块 算法网址：https://github.com/SocialSisterYi/bilibili-API-collect/blob/master/other/bvid_desc.md
        # 本算法仅能编码及解码aid<29460791296 ，无法验证aid>=29460791296 的正确性
        table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'  # 码表
        tr = {}  # 反查码表
        # 初始化反查码表
        for i in range(58):
            tr[table[i]] = i
        s = [11, 10, 3, 8, 4, 6]  # 位置编码表
        xor = 177451812  # 固定异或值
        add = 8728348608  # 固定加法值

        # aid转bid
        def av2bv(x):
            x = (x ^ xor) + add
            r: List[str] = list('BV1  4 1 7  ')
            for i in range(6):
                r[s[i]] = table[x // 58 ** i % 58]
            return ''.join(r)

        if av2bv(aid) == bid:
            print('√ [3]算法验证通过')
            time.sleep(1)
            print()
            print('□ 已定位视频')
            # 判断是否要显示分P
            if fpbv == 0:
                # 判断是否为联合投稿
                if drbv:
                    bvname = ("%s - %s" % (raid['data']['title'], drname))
                    print('□ 视频名称：', raid['data']['title'])
                    print('□ up主名称：', drname)
                    print('□ 视频封面：', raid['data']['pic'])
                    print('□ 视频简介：')
                    print(raid['data']['desc'])
                    pass
                elif not drbv:
                    bvname = ("%s - %s" % (raid['data']['title'], raid['data']['owner']['name']))
                    print('□ 视频名称：', raid['data']['title'])
                    print('□ up主名称：', raid['data']['owner']['name'])
                    print('□ 视频封面：', raid['data']['pic'])
                    print('□ 视频简介：')
                    print(raid['data']['desc'])
                    pass
                pass
            else:
                if drbv:
                    bvname = ("%s - %s" % (rcid['data'][fpbv]['part'], drname))
                    print('□ 视频名称：', rcid['data'][fpbv]['part'], ' 当前为%sP' % (fpbv + 1))
                    print('□ up主名称：', drname)
                    print('□ 视频封面：', raid['data']['pic'])
                    print('□ 视频简介：')
                    print(raid['data']['desc'])
                    pass
                elif not drbv:
                    bvname = ("%s - %s" % (rcid['data'][fpbv]['part'], raid['data']['owner']['name']))
                    print('□ 视频名称：', rcid['data'][fpbv]['part'], ' 当前为%sP' % (fpbv + 1))
                    print('□ up主名称：', raid['data']['owner']['name'])
                    print('□ 视频封面：', raid['data']['pic'])
                    print('□ 视频简介：')
                    print(raid['data']['desc'])
                    pass
                pass
            print("{:-^90s}".format(""))
            print()
            apd = True
            pass
        else:
            print('× [3]算法验证失败 强制退出程序')
            pass
        pass
    else:
        aidcode = raid['code']
        aidmsg = raid['message']
        print('× [2]警告！aid获取失败 错误码：%s 检查结果：%s' % (aidcode, aidmsg))
        pass
    pass

if bpd == 2:
    # 通过bid获取番剧信息(ep)
    getep = requests.get('http://api.bilibili.com/pgc/view/web/season?season_id=%s' % bid)
    rep = json.loads(getep.content)

    if ts:
        print()
        print('rep', rep)
        print('episodes', rep['result']['episodes'])
        print()
        pass

    # 判断rcid的状态并显示
    if rep['code'] == 0:
        if rep['result']['total'] > 0:
            print("{:-^90s}".format(""))
            bvname = rep['result']['season_title']
            print('番剧名称：', rep['result']['season_title'])
            print('剧集封面：', rep['result']['cover'])
            print('正片数量： 共计', rep['result']['total'], '话')
            print()
            for i in rep['result']['episodes']:
                print('第', i['title'], '话')
                print('单集封面：', i['cover'])
                print('单集名称：', i['share_copy'])
                # print('AID', i['aid'])
                # print('BID', i['bvid'])
                print('CID', i['cid'])
                epcid.append(i['cid'])
                print()
                pass
            time.sleep(3)
            pass
        else:
            print('× [1]警告！当前番剧列表为空')
            pass
    else:
        cidcode = rep['code']
        cidmsg = rep['message']
        print('× [1]警告！番剧数据获取失败 错误码：%s 检查结果：%s' % (cidcode, cidmsg))
        pass
    pass

# BV号视频解析
if bpd == 1 and apd == True and cpd == True:
    # 延迟3秒获取
    print('正在获取链接...')
    time.sleep(3)
    print()

    # 原始数据获取并进行第一次格式化
    headers = {'Cookie': 'SESSDATA=%s' % sessdata}
    resurl = ("https://api.bilibili.com/x/player/playurl?avid=%d&cid=%d&qn=116&fnval=0&fnver=0&fourk=1" % (aid, cid))

    resrun = requests.get("https://api.bilibili.com/x/player/playurl?avid=%d&cid=%d&qn=1&type=&otype=json&platform"
                          "=html5&high_quality=1 " % (aid, cid))  # 默认链接 视频格式1080P30MP4
    res = requests.get(resurl, headers=headers)  # 插值链接 视频格式1080P60FLV 下载需添加参数

    # 查询durl并进行第二次转换，同时获取url数量
    # resloke = res.content
    r = json.loads(res.content)
    s = json.loads(resrun.content)
    rdurl = r['data']['durl']
    sdurl = s['data']['durl']
    urllen = len(rdurl)  # 分P数量，1表示无分P
    print()
    if ts:
        # 调试显示cid返回值
        print()
        print("[ts]请求接口：", resurl, headers)
        print("[ts]视频流返回: %s" % r)
        print()
        print("[ts]durl处理:", rdurl)
        print()
        pass

    # 判断请求的视频是否有多个分P并解析视频流
    if urllen == 1:
        print('>> 视频流解析完成')
        print("{:-^90s}".format(""))
        rurls = rdurl[0]['url']
        suls = sdurl[0]['url']
        print('[1080P30MP4视频流]：')
        print(suls)
        print()
        print('[1080P60FLV视频流]：')
        print(rurls)
        print()
        # 通过cid解析弹幕xml文件
        cidXml = ("https://comment.bilibili.com/%d.xml" % cid)
        print('[XML弹幕文件解析完成]：')
        print(cidXml)
        print()
        print('提示：直接下载请复制[1080P30MP4视频流]至浏览器或任意下载工具即可')
        print('      如果需要下载[1080P60FLV视频流]请调用下面的下载程序')
        print('      XML弹幕文件可使用此目录下的转换工具转换成可被播放器理解的ASS文件')
        pass
    elif urllen > 1:
        print('多分P下载开发中...')
        pass
    print("{:-^90s}".format(""))
    time.sleep(1)

    # 询问是否调用aria2c下载
    if filepath == '' or os.path.isfile(filepath):
        print('× 警告！下载路径异常 aria2无法下载')
        pass
    else:
        while True:
            print('是否执行aria2进行下载？（需要提前安装并配置完成aria2，下载默认选择高画质）')
            judge = input('[yes/no]')
            if judge == 'yes' or judge == 'y' or judge == '':
                if not os.path.isdir(filepath):
                    print('■ 提示：未检查到下载路径 自动创建路径中...')
                    os.mkdir(filepath)
                    time.sleep(0.5)
                    if not os.path.isdir(filepath):
                        print('× 警告！下载路径创建失败 请手动创建后重新执行下载')
                        break
                        pass
                    else:
                        print('√ 路径创建成功')
                        pass
                    pass
                print()
                url = 'http://127.0.0.1:6800/jsonrpc'
                download_pvurl = rurls
                name_bv = bvname
                headers = {
                    'origin': 'https://www.bilibili.com',
                    'referer': srurl,
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                                  'Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50 '
                }
                download_xmlurl = cidXml
                print('开始调用aria2下载>> %s' % bvname)
                print('下载路径>> ', filepath)
                json_rpc = json.dumps({
                    'id': '',
                    'jsonrpc': '2.0',
                    'method': 'aria2.addUri',
                    'params': [[download_pvurl], {'referer': srurl, 'dir': filepath, 'out': [bvname]}]
                })
                if ts:
                    # 调试显示aria2输出值
                    print()
                    print("[ts]url %s" % url)
                    print("[ts]name_bv %s" % name_bv)
                    print("[ts]download_url %s" % download_pvurl)
                    print()
                    print("[ts]headers: ", headers)
                    pass
                response = requests.post(url=url, data=json_rpc)
                print('aria2响应>> ', response)
                break
                pass
            elif judge == 'no' or judge == 'n':
                print('取消aria2执行')
                break
                pass
            else:
                print('输入错误，请输入yes/y 或者 no/n，空默认为yes')
                print()
                continue
                pass
            pass
        pass
    pass

# EP号番剧解析
if bpd == 2 and epcid != []:
    print('正在获取数据...')
    print()
    # 原始数据获取并进行格式化
    for i in epcid:
        headers = {'Cookie': 'SESSDATA=%s' % sessdata}
        resurl = ("https://api.bilibili.com/pgc/player/web/playurl?cid=%d&qn=116&fnval=2&fnver=0&fourk=1" % i)
        res = requests.get(resurl, headers=headers)  # 插值链接 视频格式1080P60FLV 下载需添加参数
        s = json.loads(res.content)
        # sdurl = s['result']['durl']
        suls = s['result']['durl'][0]['url']
        epurl.append(suls)
        time.sleep(1)
        pass
    print('>> 视频流解析完成')
    print("{:-^90s}".format(""))
    print('[1080P60FLV视频流]：', epurl)
    print()
    print('[XML弹幕文件解析完成]：')
    # 通过cid顺序解析弹幕xml文件
    for i in epcid:
        cidXml = ("https://comment.bilibili.com/%d.xml" % i)
        print(cidXml)
        pass
    print()

    # 询问是否调用aria2c下载
    print("{:-^90s}".format(""))
    time.sleep(1)
    if filepath == '' or os.path.isfile(filepath):
        print('× 警告！下载路径异常 aria2无法下载')
        pass
    elif sessdata == '' or lensessdata != 32:
        print('× 警告！sessdata参数异常 阻止aria2下载')
        pass
    else:
        while True:
            print('是否执行aria2进行下载？（需要提前安装并配置完成aria2，下载默认选择高画质）')
            judge = input('[yes/no]')
            if judge == 'yes' or judge == 'y' or judge == '':
                if not os.path.isdir(filepath):
                    print('■ 提示：未检查到下载路径 自动创建路径中...')
                    os.mkdir(filepath)
                    time.sleep(0.5)
                    if not os.path.isdir(filepath):
                        print('× 警告！下载路径创建失败 请手动创建后重新执行下载')
                        break
                        pass
                    else:
                        print('√ 路径创建成功')
                        pass
                    pass
                print()
                url = 'http://127.0.0.1:6800/jsonrpc'
                download_pvurl = epurl
                name_bv = bvname
                headers = {
                    'origin': 'https://www.bilibili.com',
                    'referer': srurl,
                    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, '
                                  'like Gecko) Chrome/100.0.4896.127 Safari/537.36 Edg/100.0.1185.50 '
                }

                print('开始调用aria2下载>> %s' % bvname)
                print('下载路径>> ', filepath)
                for i in download_pvurl:
                    url = 'http://127.0.0.1:6800/jsonrpc'
                    json_rpc = json.dumps({
                        'id': '',
                        'jsonrpc': '2.0',
                        'method': 'aria2.addUri',
                        'params': [[i], {'referer': srurl, 'dir': filepath, 'out': [bvname]}]
                    })
                    response = requests.post(url=url, data=json_rpc)
                    print('aria2响应>> ', response)
                    time.sleep(0.5)
                    pass
                # json_rpc = json.dumps({
                #     'id': '',
                #     'jsonrpc': '2.0',
                #     'method': 'aria2.addUri',
                #     'params': [[download_pvurl], {'referer': srurl, 'dir': filepath, 'out': [bvname]}]
                # })
                # response = requests.post(url=url, data=json_rpc)
                # print('aria2响应>> ', response)

                if ts:
                    # 调试显示aria2输出值
                    print()
                    print("[ts]url %s" % url)
                    print("[ts]name_bv %s" % name_bv)
                    print("[ts]download_url %s" % download_pvurl)
                    print()
                    print("[ts]headers: ", headers)
                    pass
                break
                pass
            elif judge == 'no' or judge == 'n':
                print('取消aria2执行')
                break
                pass
            else:
                print('输入错误，请输入yes/y 或者 no/n，空默认为yes')
                print()
                continue
                pass
            pass
        pass
    pass


print()
print()
input('程序结束，按Enter键退出')
