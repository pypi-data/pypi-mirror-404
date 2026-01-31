from lxml import etree
import re
def analysis_file_to_tree(file_path):
    # 读取本地html，返回tree，便于外部使用xpath
    with open(file_path, 'r', encoding='utf8') as f:
        html = f.read()
    tree = etree.HTML(html, etree.HTMLParser())  # 创建xpath操作树
    return tree

def analysis_html_to_truee(html):
    # 读取页面html，返回tree，便于外部使用xpath
    tree = etree.HTML(html, etree.HTMLParser())  # 创建xpath操作树
    return tree

def analysis_file_by_re_to_text(file_path, pattern):
    # 读取本地html，传入正则，返回匹配的文本
    with open(file_path, 'r', encoding='utf8') as f:
        html = f.read()
    obj = re.compile(pattern)
    text = obj.search(html).group(1)
    return text

def analysis_html_by_re_to_text(html, pattern):
    obj = re.compile(pattern)
    text = obj.search(html).group(1)
    return text