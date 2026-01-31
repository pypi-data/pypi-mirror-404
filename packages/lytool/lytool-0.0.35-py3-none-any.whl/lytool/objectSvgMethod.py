import os

def addXml(dirPath):
    '''
    uizard导出的svg有问题，方法可修复svg
    :param dirPath: 存放svg的文件夹路径
    :return:
    '''
    xml = '<?xml version="1.0" standalone="no"?><!DOCTYPE svg PUBLIC "-//W3C//DTD SVG 1.1//EN" "http://www.w3.org/Graphics/SVG/1.1/DTD/svg11.dtd"> <svg t="1691282199858" class="icon" version="1.1" xmlns="http://www.w3.org/2000/svg" p-id="940" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="200"'
    for i in os.listdir(dirPath):
        with open(dirPath + f'/{i}', 'r', encoding='utf8') as fr:
            svg = fr.read()
            if '<?xml' not in svg:
                svg = svg.replace('<svg', xml)
        with open(dirPath + f'/{i}', 'w', encoding='utf8') as fw:
            fw.write(svg)

if __name__ == '__main__':
    dirPath = './svg_raw'
    addXml(dirPath)