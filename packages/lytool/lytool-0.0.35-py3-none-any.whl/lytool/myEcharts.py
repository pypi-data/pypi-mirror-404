import matplotlib
matplotlib.use('TkAgg')
from matplotlib import pyplot as plt
from matplotlib import font_manager
import numpy as np
import pandas as pd


class DrawEcharts:
    def __init__(self, title, xTitle=None, yTitle=None, dpi=78, artboard='black', canvas='#100c2a',
                 fontPath=r'C:\Windows\Fonts\msyh.ttc'):
        '''
        :param title: 标题
        :param xTitle: x轴标题
        :param yTitle: y轴标题
        :param dpi: 精度
        :param artboard: 画板颜色
        :param canvas: 画布颜色
        :param fontPath: 字体路径
        '''
        self.title = title
        # 画板
        plt.figure(figsize=(10, 6.18), dpi=dpi, facecolor=artboard)
        # 画布
        plt.axes().set(facecolor=canvas)
        # 中文
        self.my_font = font_manager.FontProperties(
            fname=fontPath,
            size=12.36)

        # 主标题
        plt.title(title,
                  fontproperties=self.my_font,
                  color='white',
                  size=20,
                  fontweight=600,
                  horizontalalignment='center',
                  verticalalignment='bottom')

        # 轴标题
        plt.xlabel(xTitle, fontproperties=self.my_font, color='white')
        plt.ylabel(yTitle, fontproperties=self.my_font, color='white')

    def myColor(self):
        '''
        动态获取颜色列表
        :param num: 用于确定返回多少个颜色
        :return: 颜色列表
        '''
        colorList = ['#69abfc', '#97f8cc', '#e8d27a', '#f68d97', '#77eafc']
        # return colorList[:int(num / 2)]
        # colorList = ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de', '#3ba272', '#fc8452', '#9a60b4']
        return colorList

    def myTicks_df(self, data):
        '''
        动态设置标签
        :param data: 原始数据
        :param xLabelFormat: x轴刻度标签样式
        :param yLabelFormat: y轴标签样式
        :param xStep: x轴刻度值步长
        :param yStep: y轴刻度值步长
        :param fromZero: 坐标轴刻度是否从零开始显示
        :param echartsType: 统计图类型
        '''
        # 刻度线样式
        plt.tick_params(axis='both',
                        colors='white',
                        direction='out',
                        length=4,
                        width=0.5,
                        pad=5)

        # 获取x轴与y轴的所有值
        xList = []
        yList = []
        for i in range(len(data)):
            if i % 2 == 0:
                xList.extend(data[i])
            elif i % 2 != 0:
                yList.extend(data[i])

        plt.xticks(xList,
                   color='white',
                   labels=xList,
                   fontproperties=self.my_font,
                   size=7.63848,
                   rotation=45)

        # 设置y轴刻度
        plt.yticks(yList,
                   color='white',
                   labels=yList,
                   fontproperties=self.my_font,
                   size=7.63848,
                   rotation=45)

    def myTicks(self, data, xLabelFormat='{}', yLabelFormat='{}', xStep=1, yStep=1, echartsType=None):
        '''
        动态设置标签
        :param data: 原始数据
        :param xLabelFormat: x轴刻度标签样式
        :param yLabelFormat: y轴标签样式
        :param xStep: x轴刻度值步长
        :param yStep: y轴刻度值步长
        :param fromZero: 坐标轴刻度是否从零开始显示
        :param echartsType: 统计图类型
        '''
        # 刻度线样式
        plt.tick_params(axis='both',
                        colors='white',
                        direction='out',
                        length=4,
                        width=0.5,
                        pad=5)
        if echartsType == 'hist':
            return

        # 获取x轴与y轴的所有值
        xList = []
        yList = []
        for i in range(len(data)):
            if i % 2 == 0:
                xList.extend(data[i])
            elif i % 2 != 0:
                yList.extend(data[i])

        # x轴与y轴的刻度值
        if echartsType == 'bar':
            # self.width可控制x轴标签向右移动的距离
            xRange = [i + self.moveList.pop(0) for i in data[0]]
            yRange = range(0, int(max(yList)) + 1, yStep)
        elif echartsType == 'barh':
            # self.height可控制y轴标签向上移动的距离
            xRange = range(1, int(max(yList)) + 1, xStep)
            yRange = [i + self.moveList.pop(0) for i in data[0]]
        elif echartsType == 'bara':
            xRange = data[0]
            yArray = np.zeros(len(data[0]))
            for i in range(len(data)):
                if i % 2 != 0:
                    y = np.array(data[i])
                    yArray += y
            yRange = range(0, int(max(list(yArray))) + 1)
        else:
            xRange = range(int(min(xList)), int(max(xList)) + 1, xStep)
            yRange = range(int(min(yList)), int(max(yList)) + 1, yStep)

        # x轴的刻度标签
        if echartsType == 'bar':
            xLabel = [xLabelFormat.format(i) for i in self.myLabel]
            yLabel = [yLabelFormat.format(i) for i in yRange]
        elif echartsType == 'barh':
            xLabel = [xLabelFormat.format(i) for i in xRange]
            yLabel = [yLabelFormat.format(i) for i in self.myLabel]
        elif echartsType == 'bara':
            xLabel = [xLabelFormat.format(i) for i in self.myLabel]
            yLabel = [yLabelFormat.format(i) for i in yRange]
        else:
            xLabel = [xLabelFormat.format(i) for i in xRange]
            yLabel = [yLabelFormat.format(i) for i in yRange]

        # y轴的刻度标签
        # if echartsType == 'barh':
        #     yLabel = [yLabelFormat.format(i) for i in self.myLabel]
        # else:
        #     yLabel = [yLabelFormat.format(i) for i in yRange]
        # 设置x轴刻度
        plt.xticks(xRange,
                   color='white',
                   labels=xLabel,
                   fontproperties=self.my_font,
                   size=7.63848,
                   rotation=45)

        # 设置y轴刻度
        plt.yticks(yRange,
                   color='white',
                   labels=yLabel,
                   fontproperties=self.my_font,
                   size=7.63848,
                   rotation=45)

    def myPlot_df(self, data, xLabelFormat='{}', yLabelFormat='{}', myLabel=[]):
        '''
        动态生成折线
        :param data: 原始数据
        :param xLabelFormat: x轴刻度标签样式
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        '''
        # 折线数量
        num = len(data)
        # 颜色列表
        colorList = self.myColor()
        # 绘制刻度
        self.myTicks_df(data)
        # 绘制折线
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                y = data[i + 1]
                try:
                    plt.plot(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        linestyle='--',
                        linewidth=1.5,
                        marker='o',
                        markerfacecolor=colorList[int(i / 2)],
                        markersize='5',
                        markeredgecolor='white',
                        markeredgewidth=0.5,
                        label=myLabel[int(i / 2)]
                    )
                except IndexError:
                    # 不传图例名称时触发
                    plt.plot(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        linestyle='--',
                        linewidth=1.5,
                        marker='o',
                        markerfacecolor=colorList[int(i / 2)],
                        markersize='5',
                        markeredgecolor='white',
                        markeredgewidth=0.5
                    )

        if len(myLabel) != 0:
            self.myLegend()
        self.myGrid()
        # self.mySave()
        # 显示
        plt.show()

    def myPlot(self, data, xLabelFormat='{}', yLabelFormat='{}', myLabel=[]):
        '''
        动态生成折线
        :param data: 原始数据
        :param xLabelFormat: x轴刻度标签样式
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        '''
        # 折线数量
        num = len(data)
        # 颜色列表
        colorList = self.myColor()
        # 绘制刻度
        self.myTicks(data, xLabelFormat, yLabelFormat, yStep=2)
        # 绘制折线
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                y = data[i + 1]
                try:
                    plt.plot(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        linestyle='--',
                        linewidth=1.5,
                        marker='o',
                        markerfacecolor=colorList[int(i / 2)],
                        markersize='5',
                        markeredgecolor='white',
                        markeredgewidth=0.5,
                        label=myLabel[int(i / 2)]
                    )
                except IndexError:
                    # 不传图例名称时触发
                    plt.plot(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        linestyle='--',
                        linewidth=1.5,
                        marker='o',
                        markerfacecolor=colorList[int(i / 2)],
                        markersize='5',
                        markeredgecolor='white',
                        markeredgewidth=0.5
                    )

        if len(myLabel) != 0:
            self.myLegend()
        self.myGrid()
        self.mySave()
        # 显示
        plt.show()

    def myScatter(self, data, xLabelFormat='{}', yLabelFormat='{}', myLabel=[]):
        '''
        动态生成散点图
        :param data: 原始数据
        :param xLabelFormat: x轴刻度标签样式
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        '''
        # 散点组数量
        num = len(data)
        # 颜色列表
        colorList = self.myColor()
        # 绘制刻度
        self.myTicks(data, xLabelFormat, yLabelFormat, yStep=2)
        # 绘制折线
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                y = data[i + 1]
                try:
                    plt.scatter(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        marker='o',
                        label=myLabel[int(i / 2)]
                    )
                except IndexError:
                    # 不传图例名称时触发
                    plt.scatter(
                        x,
                        y,
                        color=colorList[int(i / 2)],
                        alpha=0.9,
                        marker='.',
                    )

        if len(myLabel) != 0:
            self.myLegend()
        self.myGrid()
        self.mySave()
        # 显示
        plt.show()

    def myBar(self, data, yLabelFormat='{}', yStep=1):
        '''
        动态生成柱状图
        :param data: 原始数据
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        :param fromZero: 坐标轴刻度是否从零开始显示
        :param yStep: y轴坐标轴刻度的递进步长，比如y:[0, 100],步长为50，y轴就会出现三个刻度：0 50 100
        '''
        # 拿标签
        self.myLabel = data[0]
        # 数据组数
        num = len(data)
        # 动态柱子宽度，柱子越多，宽度越窄
        self.width = num * 0.3 / num
        # 转化数据类型，将【字符串元素列表】转为【浮点数元素列表】
        for i in range(num):
            if i % 2 == 0:
                # 将x轴列表元素换成从1开头的数字
                data[i] = [i * num / 2 / 2 for i in range(1, len(data[i]) + 1)]
                # 将y轴列表元素换成浮点数
                data[i + 1] = [float(i) for i in data[i + 1]]

        # 颜色列表
        colorList = self.myColor()

        # 两组数据所有柱状图的中间值
        widthList = []
        # 绘制折线
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                # 其余的柱状图增加x轴的值
                # if i > 0:
                # self.width可控制柱子向右移动的距离
                x = [j + 0.01 * i + self.width * i / 2 for j in data[i]]

                y = data[i + 1]
                bars = plt.bar(
                    x,
                    y,
                    color=colorList,
                    alpha=0.9,
                    width=self.width
                )
                # 所有柱子的中间值
                midWidthList = []
                for bar in bars:
                    x = bar.get_x()
                    width = bar.get_width()
                    midX = x + width / 2
                    height = bar.get_height()
                    y = height + 0.8
                    plt.text(midX, y, yLabelFormat.format(height), horizontalalignment='center', color='white',
                             fontproperties=self.my_font, size=width * 30)
                    midWidthList.append(midX)
                groupNum = len(midWidthList)
                widthList.extend(midWidthList)

        # 计算x标签向右移动的距离
        num = 0
        self.moveList = []
        while num < groupNum:
            # if num == 5:
            #     break
            lis = []
            for i in range(len(widthList)):
                if i % groupNum == num:
                    lis.append(widthList[i])
            self.moveList.append((max(lis) - min(lis)) / 2)
            num += 1

        # 绘制刻度
        self.myTicks(data, yLabelFormat=yLabelFormat, yStep=yStep, echartsType='bar')
        self.myGrid()
        self.mySave()
        plt.show()

    def myBarH(self, data, xLabelFormat='{}'):
        '''
        动态生成柱状图
        :param data: 原始数据
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        :param fromZero: 坐标轴刻度是否从零开始显示
        '''
        # 拿标签
        self.myLabel = data[0]
        # 数据组数
        num = len(data)
        # 动态柱子宽度，柱子越多，宽度越窄
        self.height = num * 0.3 / num

        # 转化数据类型，将【字符串元素列表】转为【浮点数元素列表】
        for i in range(num):
            if i % 2 == 0:
                # 将x轴列表元素换成从1开头的数字
                data[i] = [i * num / 2 / 2 for i in range(1, len(data[i]) + 1)]
                # 将y轴列表元素换成浮点数
                data[i + 1] = [float(i) for i in data[i + 1]]

        # 颜色列表
        colorNum = len(data[0]) * 2
        colorList = self.myColor()

        # 两组数据所有柱状图的中间值
        heightList = []
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                # 每遍历一次柱子的高度按比例增加高度
                x = [j + 0.01 * i + self.height * i / 2 for j in data[i]]
                y = data[i + 1]
                bars = plt.barh(
                    x,
                    y,
                    color=colorList,
                    alpha=0.9,
                    height=self.height
                )
                # 获取所有柱子的中间值
                midHeightList = []
                for bar in bars:
                    y = bar.get_y()
                    height = bar.get_height()
                    midY = y + height / 2
                    width = bar.get_width()
                    x = width + 0.2
                    plt.text(x, midY, xLabelFormat.format(width), va='center', color='white',
                             fontproperties=self.my_font, size=height * 20)
                    midHeightList.append(midY)
                groupNum = len(midHeightList)
                heightList.extend(midHeightList)

        # 计算y标签向上移动的距离
        num = 0
        self.moveList = []
        while num < groupNum:
            if num == 5:
                break
            lis = []
            for i in range(len(heightList)):
                if i % groupNum == num:
                    lis.append(heightList[i])
            self.moveList.append((max(lis) - min(lis)) / 2)
            num += 1

        # 绘制刻度
        self.myTicks(data, xLabelFormat=xLabelFormat, yStep=1, echartsType='barh')

        self.myGrid()
        self.mySave()
        plt.show()

    def myBarA(self, data, yLabelFormat='{%.2f}'):
        '''
        堆积柱状图
        :param data: 原始数据
        :param yLabelFormat: y轴标签样式
        :param myLabel: 图例列表
        :param fromZero: 坐标轴刻度是否从零开始显示
        '''
        # 拿标签
        self.myLabel = data[0]
        # 数据组数
        num = len(data)
        # 动态柱子宽度，柱子越多，宽度越窄
        self.width = num * 0.3 / num
        # 转化数据类型，将【字符串元素列表】转为【浮点数元素列表】
        for i in range(num):
            if i % 2 == 0:
                # 将x轴列表元素换成从1开头的数字
                data[i] = [i for i in range(len(data[i]))]
                # 将y轴列表元素换成浮点数
                data[i + 1] = [float(i) for i in data[i + 1]]
        # 颜色列表
        colorNum = len(data) / 2
        colorList = self.myColor()
        # 两组数据所有柱状图的中间值
        widthList = []
        # 绘制折线
        # yAfter = [0 for i in range(len(data[0]))]
        yAfter = np.zeros(len(data[0]))
        for i in range(num):
            if i % 2 == 0:
                x = data[i]
                y = data[i + 1]
                bars = plt.bar(
                    x,
                    y,
                    color=colorList[int(i / 2)],
                    alpha=0.9,
                    width=self.width,
                    bottom=list(yAfter)
                )
                # 所有柱子的中间值
                midWidthList = []
                for index, bar in enumerate(bars):
                    x = bar.get_x()
                    width = bar.get_width()
                    midX = x + width / 2
                    height = bar.get_height()
                    y = height + yAfter[index] + 0.3
                    plt.text(midX, y, yLabelFormat.format(round(height, 2)), horizontalalignment='center',
                             color='white',
                             fontproperties=self.my_font, size=width * 40)
                    midWidthList.append(midX)
                # 记录上个柱子的高度
                yAfter += np.array(data[i + 1])
                groupNum = len(midWidthList)
                widthList.extend(midWidthList)

        # 计算x标签向右移动的距离
        num = 0
        self.moveList = []
        while num < groupNum:
            if num == 5:
                break
            lis = []
            for i in range(len(widthList)):
                if i % groupNum == num:
                    lis.append(widthList[i])
            self.moveList.append((max(lis) - min(lis)) / 2)
            num += 1

        # 绘制刻度
        self.myTicks(data, yLabelFormat=yLabelFormat, yStep=2, echartsType='bara')

        self.myGrid()
        self.mySave()
        plt.show()

    def myHist(self, data, bins, label=[]):
        '''
        直方图
        :param data: 原始数据
        :param distance: 数据距离
        '''
        colorList = self.myColor()

        try:
            # 多维数组
            test = data[0][0]
            num = len(data)
            bars = plt.hist(data, bins=bins, color=colorList[0:num], label=label)
            # for num in bars[0]:
            #     for i in range(len(num)):
            #         distance = int((max(data[1])-min(data[1]))/bins)
            #         plt.text(bars[1][i], num[i], str(int(num[i])), ha='center', color='white',
            #                  fontproperties=self.my_font, size=10)
            self.myLegend()
        except:
            # 一维数组
            bars = plt.hist(data, bins=bins, color=colorList[0])
            # 计算每组
            distance = int((max(data) - min(data)) / bins)
            for i in range(len(bars[0])):
                plt.text(bars[1][i] + distance / 2, bars[0][i] + 0.8, str(int(bars[0][i])), ha='left', color='white',
                         fontproperties=self.my_font, size=10)
        self.myTicks(data, echartsType='hist')
        plt.show()

    def myPie(self, data, labels):
        # 最大扇面分离
        explode = [0 for i in data]
        explode[data.index(max(data))] = 0.05

        colors = self.myColor()
        patches, outLabel, innerLabel = plt.pie(data, labels=labels, labeldistance=1.1, colors=colors, explode=explode, autopct='%1.1f%%', pctdistance=0.6, shadow=False, startangle=90)
        # 外标签设置中文
        for text in outLabel:
            text.set_color('white')
            text.set_fontproperties(self.my_font)
        # 内标签设置大小、颜色
        for text in innerLabel:
            text.set_color('white')
        plt.show()

    def myLegend(self, position=None):
        # 图例
        plt.legend(prop=self.my_font, loc=position)

    def myGrid(self):
        # 网格
        plt.grid(alpha=0.1, linestyle='--')

    def mySave(self):
        # 保存图片
        plt.savefig(f'{self.title}.svg')

    def myAxis(self, xRange=(-6, 6), yRange=(-6, 6)):
        '''
        绘制数轴
        :param xRange: x轴显示范围
        :param yRange: y轴显示范围
        '''
        # 获取画布对象
        ax = plt.gca()

        # 设置画布的包围线
        ax.spines['right'].set_color('none')  # 取消右边线
        ax.spines['top'].set_color('none')  # 取消上边线
        ax.spines['bottom'].set_color('#69abfc')  # 蓝色底边线
        ax.spines['left'].set_color('#97f8cc')  # 绿色左边线

        # 设置轴显示的范围
        plt.xlim([min(xRange), max(xRange)])
        plt.ylim([min(yRange), max(yRange)])

        # 移动包围线，data表示按照刻度值来移动，0代表刻度值为0的位置
        ax.spines['bottom'].set_position(('data', 0))
        ax.spines['left'].set_position(('data', 0))

        # 设置刻度线样式
        plt.tick_params(axis='both',
                        colors='white',
                        direction='out',
                        length=4,
                        width=0.5,
                        pad=5)

        # 刻度值范围
        xRange = range(min(xRange), max(xRange) + 1)
        yRange = range(min(yRange), max(yRange) + 1)

        # 刻度值
        plt.xticks(
            xRange,
            color='white',
            size=7.63848
        )
        plt.yticks(
            yRange,
            color='white',
            size=7.63848
        )


if __name__ == '__main__':
    data = {
        'act_buy_xl': [197197240.0, 51190385.0, 95832037.0, 62888584.0, 89483108.0, 303852950.0, 110875276.0,205009480.0],
        'l_net_value': [0.03, 0.01, 0.02, 0.00, -0.13, 0.09, 0.02, 0.02]
    }
    date_index = pd.DatetimeIndex(['2025-01-16', '2025-01-17', '2025-01-20', '2025-01-21','2025-01-22', '2025-01-23', '2025-01-24', '2025-01-27'])
    df = pd.DataFrame(data, index=date_index)
    x1 = df.index
    y1 = df['act_buy_xl']
    data = [x1, y1]
    drawEcharts = DrawEcharts(title='2029年公司的每月营收情况', xTitle='月份', yTitle='营业额', dpi=110)
    drawEcharts.myPlot_df(data, xLabelFormat='{}月', yLabelFormat='{}万元', myLabel=['第一支股票'])



    # # 【绘制折线图】
    # x1 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    # y1 = [0, 9, 2, 3, 6, 5, 8, 7, 8, 1, 2, 7, 12]
    # x2 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    # y2 = [10, 9, 2, 3, 15, 5, 8, 7, 8, 5, 2, 7, 16]
    # x3 = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
    # y3 = [20, 2, 2, 3, 2, 25, 8, 1, 29, 5, 2, 27, 8]
    # data = [x1, y1, x2, y2, x3, y3]
    # drawEcharts = DrawEcharts(title='2029年公司的每月营收情况', xTitle='月份', yTitle='营业额', dpi=110)
    # drawEcharts.myPlot(data, xLabelFormat='{}月', yLabelFormat='{}万元', myLabel=['前沿课程战队', '科技产品战队', '科幻作品战队'])

    # 【绘制数轴】
    # drawEcharts = DrawEcharts(title='数轴', dpi=110)
    # drawEcharts.myAxis(xRange=(-7, 8), yRange=(0, 10))
    # drawEcharts.myPlot(data, myLabel=['前沿课程战队', '科技产品战队', '科幻作品战队'])
    # plt.plot([3, 4, 5, 6, 9], [3, 6, 4, 7, 20])
    # plt.show()

    # 【绘制散点图】
    # x1 = [5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17]
    # y1 = [9, 10, 12, 13, 13, 13, 14, 15, 16, 17, 17, 17, 17]
    # data = [x1, y1]
    # drawEcharts = DrawEcharts(title='2029年广告投入与营收关系研究', xTitle='广告支出', yTitle='营业额', dpi=110)
    # drawEcharts.myScatter(data, xLabelFormat='{}万元', yLabelFormat='{}百万元')

    # 【绘制竖向柱状图】
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    # data = [x1, y1]
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # drawEcharts.myBar(data, yLabelFormat='{}万元')

    # 【绘制横向柱状图】
    # 柱状图数据
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    #
    # # 构造数据
    # data = [x1, y1]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', yTitle='战队名', xTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBarH(data, xLabelFormat='{}万元')

    # 【绘制横向柱状图】
    # # 柱状图数据
    # # x1 = ['战队一', '战队二', '战队三', '战队四']
    # # y1 = ['9.5', '10', '12.4', '15']
    # # x2 = ['战队一', '战队二', '战队三', '战队四']
    # # y2 = ['10.5', '9', '9.4', '7']
    # # 构造数据
    # data = [x1, y1, x2, y2]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', yTitle='战队名', xTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBarH(data, xLabelFormat='{}万元')

    # 【绘制横向柱状图】
    # 柱状图数据
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    # x3 = ['战队一', '战队二', '战队三', '战队四']
    # y3 = ['8', '4', '10.5', '11']
    # # 构造数据
    # data = [x1, y1, x2, y2, x3, y3]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', yTitle='战队名', xTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBarH(data, xLabelFormat='{}万元')

    # 【绘制并列柱状图】
    # 柱状图数据
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    #
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    #
    # # 构造数据
    # data = [x1, y1, x2, y2]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBar(data, yLabelFormat='{}万元')

    # 【绘制并列柱状图】
    # 柱状图数据
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    #
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    #
    # x3 = ['战队一', '战队二', '战队三', '战队四']
    # y3 = ['8', '4', '10.5', '11']
    #
    # # 构造数据
    # data = [x1, y1, x2, y2, x3, y3]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBar(data, yLabelFormat='{}万元')

    # 【绘制并列柱状图】
    # 柱状图数据
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    #
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    #
    # x3 = ['战队一', '战队二', '战队三', '战队四']
    # y3 = ['8', '4', '10.5', '11']
    #
    # x4 = ['战队一', '战队二', '战队三', '战队四']
    # y4 = ['4.4', '5.6', '7.5', '10']
    #
    # # 构造数据
    # data = [x1, y1, x2, y2, x3, y3, x4, y4]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBar(data, yLabelFormat='{}万元')

    # 【绘制并列柱状图】
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    # x3 = ['战队一', '战队二', '战队三', '战队四']
    # y3 = ['8', '4', '10.5', '11']
    # x4 = ['战队一', '战队二', '战队三', '战队四']
    # y4 = ['4.4', '5.6', '7.5', '10']
    # x5 = ['战队一', '战队二', '战队三', '战队四']
    # y5 = ['9.5', '10', '12.4', '15']
    # x6 = ['战队一', '战队二', '战队三', '战队四']
    # y6 = ['10.5', '9', '9.4', '7']
    # x7 = ['战队一', '战队二', '战队三', '战队四']
    # y7 = ['8', '4', '10.5', '11']
    # x8 = ['战队一', '战队二', '战队三', '战队四']
    # y8 = ['4.4', '5.6', '7.5', '10']
    # data = [x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBar(data, yLabelFormat='{}万元')

    # 【绘制竖向柱状图】
    # x1 = ['战队一', '战队二', '战队三', '战队四']
    # y1 = ['9.5', '10', '12.4', '15']
    # x2 = ['战队一', '战队二', '战队三', '战队四']
    # y2 = ['10.5', '9', '9.4', '7']
    # x3 = ['战队一', '战队二', '战队三', '战队四']
    # y3 = ['8', '4', '10.5', '11']
    # x4 = ['战队一', '战队二', '战队三', '战队四']
    # y4 = ['4.4', '5.6', '7.5', '10']
    # x5 = ['战队一', '战队二', '战队三', '战队四']
    # y5 = ['9.5', '10', '12.4', '15']
    # x6 = ['战队一', '战队二', '战队三', '战队四']
    # y6 = ['10.5', '9', '9.4', '7']
    # x7 = ['战队一', '战队二', '战队三', '战队四']
    # y7 = ['8', '4', '10.5', '11']
    # x8 = ['战队一', '战队二', '战队三', '战队四']
    # y8 = ['4.4', '5.6', '7.5', '10']
    # data = [x1, y1, x2, y2, x3, y3, x4, y4]
    # # 实例化画图工具
    # drawEcharts = DrawEcharts(title='2029年各个战队的营业额情况', xTitle='战队名', yTitle='营业额', dpi=110)
    # # 绘制多条折线
    # drawEcharts.myBarA(data, yLabelFormat='{}万元')

    # 【绘制直方图】
    # drawEcharts = DrawEcharts(title='3年内所有电影播放时长研究', xTitle='播放时长', yTitle='数量', dpi=110)
    # bins = 10
    # # 一维数组
    # # filmTiem = np.random.randint(90, 130, 500)
    # # drawEcharts.myHist(filmTiem, bins)
    # # 多维数组
    # filmTiem = [np.random.randint(90, 130, 500), np.random.randint(90, 130, 500), np.random.randint(90, 130, 500)]
    # drawEcharts.myHist(filmTiem, bins, ['2028年', '2029年', '2030年'])

    # 【绘制饼图】
    # data = [55, 35, 10]
    # labels = ['战队一', '战队二', '战队三']
    # colors = ['red', 'green', 'blue']
    # explode = [0, 0.05, 0]
    #
    # drawEcharts = DrawEcharts(title='本月个战队营业额', dpi=110)
    # drawEcharts.myPie(data, labels)
    pass