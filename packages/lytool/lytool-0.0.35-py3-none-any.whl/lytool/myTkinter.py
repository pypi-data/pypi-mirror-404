import tkinter
from tkinter import ttk
class MyTkinter(object):
    def __init__(self, title, winSize):
        self.win = tkinter.Tk()
        self.win.title(title)
        self.win.geometry(winSize)
        self.top = tkinter.TOP
        self.bottom = tkinter.BOTTOM
        self.left = tkinter.LEFT
        self.right = tkinter.RIGHT
        self.x = tkinter.X
        self.y = tkinter.Y
        self.both = tkinter.BOTH
        self.browse = tkinter.BROWSE #支持鼠标拖动选择
        self.single = tkinter.SINGLE #不支持鼠标拖动选择
        self.extended = tkinter.EXTENDED #支持shift、ctrl
        self.multiple = tkinter.MULTIPLE #多选显示
        self.active = tkinter.ACTIVE #头插入
        self.end = tkinter.END #尾插入
        self.horizontal = tkinter.HORIZONTAL #水平方向
        self.vertical = tkinter.VERTICAL #垂直方向

    #标签
    def lable(self, parentWin, text, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None): #tkinter.TOP tkinter.BOTTOM tkinter.LEFT tkinter.RIGHT
        label = tkinter.Label(parentWin, text=text)
        if layoutMode == 'place': #绝对布局
            label.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            label.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            label.grid(row=row, column=column)

    #按钮
    def button(self, parentWin, text, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None, command=None):
        button = tkinter.Button(parentWin, text=text, command=command)
        if layoutMode == 'place': #绝对布局
            button.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            button.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            button.grid(row=row, column=column)

    #输入
    def entry(self, parentWin, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        e = tkinter.Variable()
        entry = tkinter.Entry(parentWin, textvariable=e)
        if layoutMode == 'place': #绝对布局
            entry.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            entry.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            entry.grid(row=row, column=column)
        return e

    #获取输入值
    def getEntry(self, e):
        entryInfo = e.get()
        return entryInfo

    #设置输入值
    def setEntry(self, e, str):
        e.set(str)

    #文本
    def text(self, parentWin, width, height, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        self.text = tkinter.Text(parentWin, width=width, height=height)
        if layoutMode == 'place': #绝对布局
            self.text.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            self.text.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            self.text.grid(row=row, column=column)


    #插入文本
    def insertText(self, str, mode=tkinter.END): #mode=tkinter.INSERT头插入
        self.text.insert(mode, str)

    #滚动条文本
    def scrollText(self, parentWin, width, height, sideScr=tkinter.RIGHT, fillScr=tkinter.Y, sideText=tkinter.LEFT, fillText=tkinter.Y):
        scroll = tkinter.Scrollbar()
        self.scrollText = tkinter.Text(parentWin, width=width, height=height)
        scroll.pack(side=sideScr, fill=fillScr)
        self.scrollText.pack(side=sideText, fill=fillText)
        scroll.config(command=self.scrollText.yview)
        self.scrollText.config(yscrollcommand=scroll.set)

    #插入滚动条文本
    def insertScrollText(self, str, mode=tkinter.END):
        self.scrollText.insert(mode, str)

    #多选框
    def checkButton(self, parentWin, textList, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        self.hobby1 = tkinter.BooleanVar()  # 生成一个布尔类型的变量
        self.str1 = textList[0]
        check1 = tkinter.Checkbutton(parentWin, text=textList[0], variable=self.hobby1, command=self.getCheckButtonValue)
        if layoutMode == 'place': #绝对布局
            check1.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            check1.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            check1.grid(row=row, column=column)

        self.hobby2 = tkinter.BooleanVar()  # 生成一个布尔类型的变量
        self.str2 = textList[1]
        check2 = tkinter.Checkbutton(parentWin, text=textList[1], variable=self.hobby2, command=self.getCheckButtonValue)
        if layoutMode == 'place': #绝对布局
            check2.place(x=x, y=y)
        elif layoutMode == 'pack': #相对布局
            check2.pack(side=side, fill=fill)
        elif layoutMode == 'grid': #表格布局
            check2.grid(row=row, column=column)

        self.hobby3 = tkinter.BooleanVar()  # 生成一个布尔类型的变量
        self.str3 = textList[2]
        check3 = tkinter.Checkbutton(parentWin, text=textList[2], variable=self.hobby3, command=self.getCheckButtonValue)
        if layoutMode == 'place':  # 绝对布局
            check3.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            check3.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            check3.grid(row=row, column=column)

    #获取多选框的值
    def getCheckButtonValue(self):
        message = ''
        if self.hobby1.get() == True:
            message += self.str1 + '\n'
        if self.hobby2.get() == True:
            message += self.str2 + '\n'
        if self.hobby3.get() == True:
            message += self.str3 + '\n'
        self.text.delete(0.0, tkinter.END)  # 参数1：从开头清除，0行0列；参数2,：清空到最后
        self.text.insert(tkinter.INSERT, message)

    #单选框
    def radioButton(self, parentWin, textList, valueList, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        self.variable = tkinter.IntVar()
        radio1 = tkinter.Radiobutton(parentWin, text=textList[0], value=valueList[0], variable=self.variable, command=self.getRadioButton)  # text:单选框显示的内容,value:单选框所代表的数据
        if layoutMode == 'place':  # 绝对布局
            radio1.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            radio1.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            radio1.grid(row=row, column=column)
        radio2 = tkinter.Radiobutton(parentWin, text=textList[1], value=valueList[1], variable=self.variable, command=self.getRadioButton)
        if layoutMode == 'place':  # 绝对布局
            radio2.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            radio2.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            radio2.grid(row=row, column=column)

    #获取单选框的值
    def getRadioButton(self):
        print(self.variable.get())

    #列表控件
    def packListBox(self, parentWin, selectMode, insertMode, textList):
        self.lb = tkinter.Listbox(parentWin, selectmode=selectMode)  # self.expanded = tkinert.EXPANDED使Listbox支持Shift和Control
        for text in textList:
            self.lb.insert(insertMode, text) #self.end = tkinter.END
        # 添加滚动条
        sc = tkinter.Scrollbar(parentWin)
        sc.pack(side=tkinter.RIGHT, fill=tkinter.Y)
        self.lb.pack(side=tkinter.LEFT, fill=tkinter.Y)
        self.lb.configure(yscrollcommand=sc.set)
        sc['command'] = self.lb.yview  # 给属性赋值
        #添加事件
        self.lb.bind('<Double-Button-1>', self.getListBoxValue)  # 双击-按钮-左键

    #获取列表控件的值
    def getListBoxValue(self, event):
        print(self.lb.get(self.lb.curselection()))

    #删除列表控件的值
    def deleteListBoxValue(self, start, end):
        self.lb.delete(start, end)

    #获得列表控件值得个数
    def getListBoxValueSize(self):
        size = self.lb.size()
        return size

    #范围控件
    #父级，值开始，值结束，方向，框长度，布局方式，值显示倍数
    def Scale(self, parentWin, start, end, orient, length, layoutMode, tickinterval=1, x=None, y=None, side=None, fill=None, row=None, column=None):
        scale = tkinter.Scale(parentWin, from_=start, to=end, orient=orient, length=length, tickinterval=tickinterval)
        if layoutMode == 'place':  # 绝对布局
            scale.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            scale.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            scale.grid(row=row, column=column)

    #主菜单
    def menu(self, downMenuName, menuLabelFuctionDict):
        menubar = tkinter.Menu(self.win) #创建菜单栏
        self.win.config(menu=menubar) #配置在主窗口
        downMenu = tkinter.Menu(menubar, tearoff=False) #下拉菜单
        downMenu.add_separator() #设置分割线
        for menuLabel , function in menuLabelFuctionDict.items():
            downMenu.add_command(label=menuLabel, command=function)
        menubar.add_cascade(label=downMenuName, menu=downMenu)

    #主菜单退出
    def quit(self):
        self.win.quit()

    #右键菜单
    def rightKeyMenu(self, parentWin, menuLabelName, menuLabelFunctionDict):
        def showRightKeyMenu(event):
            rightKeyMenubar.post(event.x_root, event.y_root)
        rightKeyMenubar = tkinter.Menu(parentWin)
        rightKeyMenu = tkinter.Menu(rightKeyMenubar, tearoff=False)
        for nextMenuLabel, function in menuLabelFunctionDict.items():
            rightKeyMenu.add_command(label=nextMenuLabel, command=function)
        rightKeyMenubar.add_cascade(label=menuLabelName, menu=rightKeyMenu)
        self.win.bind('<Button-3>', showRightKeyMenu)

    #下拉控件
    def comboBox(self, parentWin, comboValueTuple, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        cv = tkinter.StringVar()
        com = ttk.Combobox(parentWin, textvariable=cv)
        if layoutMode == 'place':  # 绝对布局
            com.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            com.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            com.grid(row=row, column=column)
        # 设置下拉属性
        com['value'] = comboValueTuple
        com.current(0)
        # 绑定事件
        def function(event):
            print(com.get())  # 选其一来取值
            print(cv.get())
        com.bind('<<ComboboxSelected>>', function)

    #Frame框架控件
    def frame(self, parentWin, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        frame = tkinter.Frame(parentWin)
        if layoutMode == 'place':  # 绝对布局
            frame.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            frame.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            frame.grid(row=row, column=column)
        return frame

    #表格数据
    def packExcelWin(self, parentWin, width, columnHeadingDict, rowNameDataTupleDict, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None):
        self.tree = ttk.Treeview(parentWin)
        columnsList = []
        for key in columnHeadingDict.keys():
            columnsList.append(key)
        columnsTuple = tuple(columnsList)
        self.tree['columns'] = columnsTuple
        for columnName, headingName in columnHeadingDict.items():
            # 设置列
            self.tree.column(columnName, width=width)
            # 设置表头
            self.tree.heading(columnName, text=headingName)
        self.rowNum = 0
        for rowName, dataTuple in rowNameDataTupleDict.items():
            if type(dataTuple) == type(()):
                # 添加数据
                self.tree.insert('', self.rowNum, text=rowName, values=dataTuple)
                self.rowNum += 1
            else:
                print('please type == tuple')
        self.tree.pack(side=side, fill=fill)

    def insertExcelWin(self,rowNameDataTupleDict):
        self.rowNum  += 1
        for rowName, dataTuple in rowNameDataTupleDict.items():
            if type(dataTuple) == type(()):
                # 添加数据
                self.tree.insert('', self.rowNum, text=rowName, values=dataTuple)
                self.rowNum += 1
            else:
                print('please type == tuple')

    #数状结构
    def packTreeview(self, parentWin, AtreeRowDataList, layoutMode, x=None, y=None, side=None, fill=None, row=None, column=None, BtreeRowDataList=None, CtreeRowDataList=None):
        tree = ttk.Treeview(parentWin)
        if layoutMode == 'place':  # 绝对布局
            tree.place(x=x, y=y)
        elif layoutMode == 'pack':  # 相对布局
            tree.pack(side=side, fill=fill)
        elif layoutMode == 'grid':  # 表格布局
            tree.grid(row=row, column=column)
        # 添加A级树枝
        BtreeWin = []
        for rowData in AtreeRowDataList:
            BtreeNum = tree.insert('', rowData[0], rowData[1], text=rowData[2], values=rowData[3], open=True)  # 参数1：父级窗体，参数2：插入位置，参数4：显示内容,参数5：值，参数6：是否展开
            BtreeWin.append(BtreeNum)
        # 添加B级树枝
        CtreeWin = []
        if BtreeRowDataList != None:
            for BRowData in BtreeRowDataList:
                Cwin = tree.insert(BtreeWin[BRowData[-1]], BRowData[0], BRowData[1], text=BRowData[2], values=BRowData[3])
                CtreeWin.append(Cwin)
        # 添加C级树枝
        if CtreeRowDataList != None:
            for CRowData in CtreeRowDataList:
                tree.insert(CtreeWin[CRowData[-1]], CRowData[0], CRowData[1], text=CRowData[2], values=CRowData[3])

    #生成树状结构行数据的列表
    def makeTreeRowDataList(self, rowDataList):
        makeTreeRowDataList = []
        rowNum = 0
        for rowData in rowDataList:
            row = [rowNum, rowData[0], rowData[0], rowData[1], rowData[2]] # 父级树，插入位置，插入数据，显示数据，该项值，父级树索引
            rowNum += 1
            makeTreeRowDataList.append(row)
        return makeTreeRowDataList

    def mainloop(self):
        self.win.mainloop()

if __name__ == '__main__':
    mytk = MyTkinter('我的窗口', '400x400+200+200')
    #标签
    '''
    mytk.lable(mytk.win, '封装标签', 'place', 40, 20)
    mytk.lable(mytk.win, '封装标签', 'pack', side=mytk.bottom, fill=mytk.x)
    mytk.lable(mytk.win, '封装标签', 'grid', row=0, column=1)
    mytk.lable(mytk.win, '封装标签', 'grid', row=1, column=0)
    '''

    #按钮
    '''
    def function():
        print('传入函数成功')
    mytk.button(mytk.win, '封装按钮', 'pack', command=function)
    '''
    #输入
    '''
    e = mytk.entry(mytk.win, 'pack')
    e.set('123')
    #mytk.setEntry(e, '123')
    mytk.button(mytk.win, '打印', mytk.getEntry)
    '''
    #文本
    '''
    mytk.packText(10, 5)
    mytk.insertText('i’am happy')
    '''
    #滚动条文本
    '''
    mytk.packScrollText(mytk.win, 10, 5)
    mytk.insertScrollText('字数够了就会出现滚动条')
    '''
    #多选框控件
    '''
    mytk.packText(20, 5)
    mytk.packCheckButton(mytk.win, ['justin', 'mia', 'coco'])
    '''
    #单选框
    '''
    mytk.packRadioButton(mytk.win, ['one','two'], ['1','2'], mytk.top, mytk.x)
    '''
    #列表控件,清屏
    '''
    mytk.packListBox(mytk.win, mytk.single, mytk.end, ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'a', 'b', 'c', 'd', 'e', 'f', 'g', 'h'], mytk.right, )
    mytk.deleteListBoxValue(0, mytk.getListBoxValueSize())
    '''
    #下拉菜单
    '''
    def func1():
        print('one')
    def func2():
        print('two')
    mytk.menu('语言', {'python': func1, 'java': func2, 'quite': mytk.quit})
    '''
    #右键菜单
    '''
    def func1():
        print('boy')
    def func2():
        print('gril')
    mytk.rightKeyMenu(mytk.win, 'name', {'justin': func1, 'mia': func2})
    '''
    #下拉控件
    '''
    mytk.packComboBox(mytk.win, ('北京', '上海', '成都'))
    '''
    #Frame框架控件
    '''
    frame = mytk.frame(mytk.win)
    frame1 = mytk.frame(frame, mytk.left, mytk.y)
    frame2 = mytk.frame(frame, mytk.right, mytk.y)
    frame3 = mytk.frame(frame1, mytk.top, mytk.y)
    frame4 = mytk.frame(frame1, mytk.bottom, mytk.y)
    frame5 = mytk.frame(frame2, mytk.top, mytk.y)
    frame6 = mytk.frame(frame2, mytk.bottom, mytk.y)
    mytk.packLable(frame3, 'frame1Label', mytk.top)
    mytk.packLable(frame6, 'frame2Label', mytk.bottom)
    '''
    #列表数据
    '''
    mytk.packExcelWin(mytk.win, 100, {'name':'姓名','age':'年龄','gender':'性别'}, {'numer1':('陈艺龙','30','男'),'numer2':('彭淑贤','31','女'),'numer3':('陈紫妍','9','女')})
    mytk.insertExcelWin({'numer4':('果果','3','女')})
    '''
    #树结构
    '''
    AtreeRowDataList = mytk.makeTreeRowDataList([['中国', 1, 0], ['美国', 2, 0], ['日本', 3, 0]]) #[树结构行显示，值，父级索引]
    BtreeRowDataList = mytk.makeTreeRowDataList([['黑龙江', 1, 0], ['四川', 2, 0], ['纽约', 1, 1], ['芝加哥', 2, 1], ['札幌市', 1, 2], ['函馆市', 2, 2]])
    CtreeRowDataList = mytk.makeTreeRowDataList([['哈尔滨市', 1, 0], ['成都市', 1, 1], ['曼哈顿', 1, 2], ['伊利诺伊', 1, 3], ['萨哈林岛', 1, 4], ['北海道', 1, 5]])
    mytk.packTreeview(mytk.win, AtreeRowDataList, BtreeRowDataList, CtreeRowDataList)
    '''
    mytk.mainloop()