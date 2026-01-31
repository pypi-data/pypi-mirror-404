import execjs

class RunJs():
    def __init__(self, file_name):
        self.file_name = file_name

    def getJsCode(self, file_name):
        with open(file_name, 'r', encoding='UTF-8') as file:
            result = file.read()
        return result

    def placeAnOrder(self, commodity_id, name, province, city, area, street, address, phone):
        # 自动购物
        context1 = execjs.compile(self.getJsCode(self.file_name))
        result1 = context1.call('run', commodity_id, name, province, city, area, street, address, phone)
        print(result1)

if __name__ == '__main__':
    headless = False  # 无头模式
    commodity_id = '100010040739'
    name = '彭淑贤'
    province = '四川'
    city = '成都市'
    area = '武侯区'
    street = '金花桥街道'
    address = '金花桥路江安河新居2期'
    phone = '17311328850'

    runJs = RunJs(r'C:\Users\justin\Desktop\FrontierAcademy\college_be\automation\src\placeAnOrder.js')
    order_price = runJs.placeAnOrder(headless, commodity_id, name, province, city, area, street, address, phone)
    print(order_price) # {'order': '242769492845', 'price':'10.4元'}
