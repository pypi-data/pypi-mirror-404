import re

# def decode16(string):
#     '''
#     ("b'xe5xb0x8fxe6xb5xb7xe7xbbxb5xf0x9fxa7xbd'")=>龙良雨
#     ("龙良雨")=>龙良雨
#     '''
#     try:
#         # 去掉最外层的""
#         hex_string = eval(string).decode('utf8')
#         # 使用正则表达式找到所有的十六进制编码
#         hex_values = re.findall(r'x[0-9a-fA-F]{2}', hex_string)
#         # 将十六进制编码转换为整数，然后使用bytes.fromhex将其转换为字节数据
#         byte_data = bytes.fromhex(''.join([hex_val[1:] for hex_val in hex_values]))
#         # 将字节数据解码为字符串
#         decoded_text = byte_data.decode('utf-8')
#         return decoded_text
#     except NameError:
#         return string

def decode16(string):
    '''
    通过检查字符串是否为字节类型来处理解码。
    ("b'xe5xb0x8fxe6xb5xb7xe7xbbxb5xf0x9fxa7xbd'") => 龙良雨
    ("龙良雨") => 龙良雨
    '''
    try:
        # 如果输入的是字节类型，直接解码
        if isinstance(string, bytes):
            decoded_text = string.decode('utf-8')
        elif isinstance(string, str) and string.startswith("b'") and string.endswith("'"):
            # 如果输入是类似字节字面量的字符串，去掉最外层的引号，并解码
            string = string[2:-1]  # 去掉 b' 和 '
            decoded_text = bytes.fromhex(string.replace('x', '')).decode('utf-8')
        else:
            # 否则直接返回原始字符串
            decoded_text = string
        return decoded_text
    except Exception as e:
        # print(f"解码出错: {e}")
        return string
