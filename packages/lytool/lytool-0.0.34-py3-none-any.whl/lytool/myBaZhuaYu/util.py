import requests

def request_t_post(host, path, tokenStr, bodyData=''):
	return requests.post(host + path, headers={'Authorization': 'bearer ' + tokenStr}, data=bodyData).json()

def request_t_get(host, path, tokenStr):
	return requests.get(host + path, headers={'Authorization': 'bearer ' + tokenStr}).json()

def show_task_data(dataResult):
	if 'error' in dataResult:
		if dataResult['error'] == 'success' and 'dataList' in dataResult['data']:
			dataDict = dataResult['data']['dataList'][0]
			for k, v in dataDict.items():
				print("%s\t%s"%(k, v))
		else:
			print(dataResult['error_Description'])
	else:
		print(response)

'''
[{'白色': 'https://cbu01.alicdn.com/img/ibank/O1CN017TJucW2HrU4p6Bb0C_!!969419204-0-cib.jpg'}, {'黑色': 'https://cbu01.alicdn.com/img/ibank/O1CN016IK77e2HrU4tClNkW_!!969419204-0-cib.jpg'}, {'奶金色': 'https://cbu01.alicdn.com/img/ibank/O1CN01PZEONx2HrU4uvClb3_!!969419204-0-cib.jpg'}, {'樱粉色': 'https://cbu01.alicdn.com/img/ibank/O1CN01j19Api2HrU4l0vn69_!!969419204-0-cib.jpg'}]
'''