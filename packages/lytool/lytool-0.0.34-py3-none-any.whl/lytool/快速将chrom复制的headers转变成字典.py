# 快速将chrom格式的headers，清洗成字典
#   ctrl+r
#       勾选Regex
#       搜索栏：(.*): (.*)\n
#       替换栏：'$1': '$2',\n
#       点击REPLACE ALL

'''
content-encoding: gzip
content-type: text/html;charset=UTF-8
date: Wed, 25 Aug 2021 10:00:31 GMT
server: Tengine
set-cookie: PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; Version=1; Domain=58.com; Path=/
set-cookie: param8616=1; Domain=58.com; Expires=Thu, 25-Aug-2022 10:00:31 GMT; Path=/
set-cookie: param8716kop=1; Domain=58.com; Expires=Thu, 25-Aug-2022 10:00:31 GMT; Path=/
set-cookie: PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; Version=1; Domain=58.com; Path=/
set-cookie: JSESSIONID=44F8C4BE1E2E476B382975FF545F5101; Path=/; Secure; HttpOnly
set-cookie: f=n
vary: Accept-Encoding
:authority: sz.58.com
:method: GET
:path: /searchjob/?pts=1629884554040
:scheme: https
accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9
accept-encoding: gzip, deflate, br
accept-language: zh-CN,zh;q=0.9
cache-control: no-cache
cookie: f=n; commontopbar_new_city_info=4%7C%E6%B7%B1%E5%9C%B3%7Csz; commontopbar_ipcity=cd%7C%E6%88%90%E9%83%BD%7C0; id58=c5/nfGDN5UKqV32/D90GAg==; 58tj_uuid=a1a2bf2f-3d75-443c-994c-d677eafb21e7; wmda_new_uuid=1; wmda_uuid=cecda8c5ce9a26451d9ac5651bd5a481; als=0; xxzl_deviceid=RyCl8M%2B4QIQXAiykN2KncbMlnyA44w9AE2baPedrnYJ2MHq1lq2ZfhNhNESysz8Z; gr_user_id=787e9426-e683-41b0-8b7a-fce6b251a7ea; bj58_new_uv=1; bj58_id58s="ZDcxX0gwSSt0VHRRMTk5OQ=="; ppStore_fingerprint=undefined%EF%BC%BF1624106711982; sessid=B0DD2179-A275-41EC-A5F4-3B2EB6ECE2B4; aQQ_ajkguid=6AA48222-78B2-4FC9-8A3E-E00FD775607A; ctid=102; param8616=1; param8716kop=1; wmda_visited_projects=%3B11187958619315%3B1731918550401%3B2385390625025%3B1731916484865%3B10104579731767; isSmartSortTipShowed=true; xxzl_smartid=6b5197f651ff5293983f2a061374790b; sessionid=6c5b2a4f-8ed9-4b07-a99e-cbdf4d07bfdf; wmda_session_id_10104579731767=1629884555339-9271fd0d-9f2c-5375; PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; www58com="UserID=43471937920532&UserName=hizqj8"; 58cooper="userid=43471937920532&username=hizqj8"; 58uname=hizqj8; passportAccount="atype=0&bstate=0"; JSESSIONID=17F9AD262A9D243CF818E68CF6442CC3; new_session=1; new_uv=6; utm_source=; spm=; init_refer=https%253A%252F%252Fpassport.58.com%252F; Hm_lvt_a3013634de7e7a5d307653e15a0584cf=1629884587; Hm_lpvt_a3013634de7e7a5d307653e15a0584cf=1629884587; wmda_session_id_1731916484865=1629884587014-7a2f5859-d38e-da15; f=n; xxzl_cid=1523c158c1404ba78729766eaa9dde56; xzuid=964172aa-8642-44f8-8d08-c94743a8e9fd; jl_list_left_banner=101
pragma: no-cache
referer: https://passport.58.com/
sec-ch-ua: "Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"
sec-ch-ua-mobile: ?0
sec-fetch-dest: document
sec-fetch-mode: navigate
sec-fetch-site: same-site
sec-fetch-user: ?1
upgrade-insecure-requests: 1
user-agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36
'''

{
    'content-encoding': 'gzip',
    'content-type': 'text/html;charset=UTF-8',
    'date': 'Wed, 25 Aug 2021 10:00:31 GMT',
    'server': 'Tengine',
    'set-cookie': 'PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; Version=1; Domain=58.com; Path=/',
    'set-cookie': 'param8616=1; Domain=58.com; Expires=Thu, 25-Aug-2022 10:00:31 GMT; Path=/',
    'set-cookie': 'param8716kop=1; Domain=58.com; Expires=Thu, 25-Aug-2022 10:00:31 GMT; Path=/',
    'set-cookie': 'PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; Version=1; Domain=58.com; Path=/',
    'set-cookie': 'JSESSIONID=44F8C4BE1E2E476B382975FF545F5101; Path=/; Secure; HttpOnly',
    'set-cookie': 'f=n',
    'vary': 'Accept-Encoding',
    ':authority': 'sz.58.com',
    ':method': 'GET',
    ':path': '/searchjob/?pts=1629884554040',
    ':scheme': 'https',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'no-cache',
    'cookie': 'f=n; commontopbar_new_city_info=4%7C%E6%B7%B1%E5%9C%B3%7Csz; commontopbar_ipcity=cd%7C%E6%88%90%E9%83%BD%7C0; id58=c5/nfGDN5UKqV32/D90GAg==; 58tj_uuid=a1a2bf2f-3d75-443c-994c-d677eafb21e7; wmda_new_uuid=1; wmda_uuid=cecda8c5ce9a26451d9ac5651bd5a481; als=0; xxzl_deviceid=RyCl8M%2B4QIQXAiykN2KncbMlnyA44w9AE2baPedrnYJ2MHq1lq2ZfhNhNESysz8Z; gr_user_id=787e9426-e683-41b0-8b7a-fce6b251a7ea; bj58_new_uv=1; bj58_id58s="ZDcxX0gwSSt0VHRRMTk5OQ=="; ppStore_fingerprint=undefined%EF%BC%BF1624106711982; sessid=B0DD2179-A275-41EC-A5F4-3B2EB6ECE2B4; aQQ_ajkguid=6AA48222-78B2-4FC9-8A3E-E00FD775607A; ctid=102; param8616=1; param8716kop=1; wmda_visited_projects=%3B11187958619315%3B1731918550401%3B2385390625025%3B1731916484865%3B10104579731767; isSmartSortTipShowed=true; xxzl_smartid=6b5197f651ff5293983f2a061374790b; sessionid=6c5b2a4f-8ed9-4b07-a99e-cbdf4d07bfdf; wmda_session_id_10104579731767=1629884555339-9271fd0d-9f2c-5375; PPU="UID=43471937920532&UN=hizqj8&TT=ab6e1455572ee7851a6bcc7228331943&PBODY=ELR4Xsb-riU9yKdHz10lVlJv6zwbDCmJUYhg91S4HynwQZNkVTyXSjNcuhAL6lf9jCdJUc5RtnhXYN0gSSSKvXiIgpYGtOVDlW8kVf6BRwmYLL5cfPiEs_ARMbz7aMqOC_oggh95NiPGp3GxKf9Toe_mDkMQpx2B-JPaXakNMCc&VER=1&CUID=W5rVOguglIoaXeAFalQIrQ"; www58com="UserID=43471937920532&UserName=hizqj8"; 58cooper="userid=43471937920532&username=hizqj8"; 58uname=hizqj8; passportAccount="atype=0&bstate=0"; JSESSIONID=17F9AD262A9D243CF818E68CF6442CC3; new_session=1; new_uv=6; utm_source=; spm=; init_refer=https%253A%252F%252Fpassport.58.com%252F; Hm_lvt_a3013634de7e7a5d307653e15a0584cf=1629884587; Hm_lpvt_a3013634de7e7a5d307653e15a0584cf=1629884587; wmda_session_id_1731916484865=1629884587014-7a2f5859-d38e-da15; f=n; xxzl_cid=1523c158c1404ba78729766eaa9dde56; xzuid=964172aa-8642-44f8-8d08-c94743a8e9fd; jl_list_left_banner=101',
    'pragma': 'no-cache',
    'referer': 'https://passport.58.com/',
    'sec-ch-ua': '"Chromium";v="92", " Not A;Brand";v="99", "Google Chrome";v="92"',
    'sec-ch-ua-mobile': '?0',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-site',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
}