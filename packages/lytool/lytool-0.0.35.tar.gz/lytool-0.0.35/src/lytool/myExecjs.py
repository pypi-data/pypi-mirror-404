# 安装：pip install PyExecJS

import execjs
import json

def myExecjs(path, data):
    with open(path, 'r', encoding='utf8') as f:
        js = f.read()
    decrypt_data = execjs.compile(js).call('decrypy', data)
    json_data = json.loads(decrypt_data)
    return json_data

