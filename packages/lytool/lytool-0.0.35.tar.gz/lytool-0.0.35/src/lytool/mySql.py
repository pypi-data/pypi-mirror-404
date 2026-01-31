# -*- coding: utf-8 -*
import pymysql
class MySql(object):
    def __init__(self, ip, userName, passWord, dataBase):
        self.ip = ip
        self.userName = userName
        self.passWord = passWord
        self.dataBase = dataBase

    #链接
    def connect(self):
        self.db = pymysql.connect(self.ip, self.userName, self.passWord, self.dataBase)
        self.cursor = self.db.cursor()

    #断开
    def close(self):
        self.cursor.close()
        self.db.close()

    #创建表
    def createTable(self):
        sql = "create table if not exists students (id varchar(255) not null, name varchar(255) not null, age int not null, primary key (id))"
        self.__edit(sql)

    #显示字段
    def show_fieldName(self, table):
        self.connect()
        self.cursor.execute('desc {};'.format(table))
        resField = self.cursor.fetchall() #(('','',''),('','',''))
        resFieldList = []
        for row in resField:
            resFieldName = row[0] # + '_' + row[1]
            resFieldList.append(resFieldName)
        self.close()
        return resFieldList

    #查单条数据
    def get_one(self, sql):
        res = None
        try:
            self.connect()
            self.cursor.execute(sql)
            res = self.cursor.fetchone()
            self.close()
        except:
            print('查询失败')
        return res

    #查所有数据
    def get_all(self, sql):
        res = ()
        try:
            self.connect()
            self.cursor.execute(sql)
            res = self.cursor.fetchall()
            self.close()
        except:
            print('查询失败')
        return res

    #插入数据
    def insert(self,table, data):
        self.data = data #data为字典格式
        keys = ','.join(data.keys()) #'key1,key2,key3'
        values = ','.join(['%s']*len(self.data)) #'%s,%s,%s,'
        #"insert into database ('key1,key2,key3') values ('%s,%s,%s')"
        sql = "insert into {table} ({keys}) values ({values})".format(table=table, keys=keys, values=values)
        self.__edit(sql)
        return

    #更新数据
    def update(self, sql):
        return self.__edit(sql)

    #删除数据
    def delete(self, sql):
        return self.__edit(sql)

    #相同函数代码
    def __edit(self, sql):
        count = 0 #提交失败返回0
        print(tuple(self.data.values()))
        try:
            self.connect()
            count = self.cursor.execute(sql, tuple(self.data.values())) #(value1,value2,value3)传入sql语句的%s位置，即        #"insert into database ('key1,key2,key3') values ('value1,value2,value3')"
            # count = self.cursor.execute(sql) #创建表的时候此条代码取消注释，上条代码增加注释
            self.db.commit() #数据库执行
            self.close()
            print('成功存入mysql')
        except:
            print('事务提交失败')
            self.db.rollback() #事件回滚
            # exit()
        return count

if __name__ == '__main__':
    mysql = MySql('localhost', 'root', '135cylpsx', 'stock_db')
    mysql.connect()
    res = mysql.get_all('select * from focus;')
    print(res)


    # innerUrl = mysql.get_all('select distinct innerUrl from goods;')
    # innerUrlList = []
    # for url in innerUrl:
    #     innerUrlList.append(url[0])
    # if 'https://item.jd.com/54285320706.html' in innerUrlList:
    #     print('存在该url')
    # else:
    #     print('不存在该url')
    # mysql.connect()
    # data = {'一级分类': '医药保健', '二级分类': '保健器械', '三级分类': '血压计', '四级分类': '上臂式', '搜索分类': '', '商品图片': 'https://img11.360buyimg.com/n7/jfs/t19210/275/557995777/180053/1b8b85d3/5a94fc67N5404068e.jpg', '商品价格': '199.0', '商品标题': '乐心i5升级版 电子血压计 家用上臂式 高血压测量仪 WiFi传输数据 智能远程血压计 微信互联 USB充电 【京东物流，品质保证】乐心智能wifi血压计，远程传输，微信互联，USB充电！一年内免费换新！会场', '评论数量': '22000.0', '店铺名称': '', '商品图标': '自营', '子图列表': 'https://img12.360buyimg.com/n5/jfs/t19210/275/557995777/180053/1b8b85d3/5a94fc67N5404068e.jpg,https://img12.360buyimg.com/n5/jfs/t3160/193/1047642497/71637/75410daa/57c575dfN51ea5a25.jpg,https://img12.360buyimg.com/n5/jfs/t3151/187/1062377306/160467/4fe8c807/57c57612N5c15b428.jpg,https://img12.360buyimg.com/n5/jfs/t25996/291/208658609/108901/630dd181/5b690513N03b0f143.jpg,https://img12.360buyimg.com/n5/jfs/t3115/312/1084324425/93969/191814c/57c57619N085a2ebb.jpg', '品牌': '乐心（lifesense）', '商品名称': '乐心LS805-F', '商品编号': '3138617', '货号': '', '店铺': '', '商品毛重': '0.82kg', '商品产地': '中国广东', '国产进口': '国产', '电源': '充电', '分类': '上臂式', '类别': '', '特色': '全自动，智能加压，大屏背光，误动作提醒，心律不齐提醒，WiFi传输', '价位': '100-199', '规格': '', '尺寸': '', '原料': '', '数量': '', '用途': '', '性质': '', '尺码': '', '裙长': '', '面料': '', '厚度': '', '领型': '', '流行元素': '', '适用季节': '', '是否有兜': '', '适用场景': '', '适用人群': '', '分子筛': '', '调码方式': '', '记忆功能': '', '测量部位': '', '智能警报': '', '充电方式': '', '压力范围': '', '工作模式': '', '压力模式': '', '重量': '', '适用部位': '', '电源方式': '', '适用症状': '', '包装': '', '蓝帽标识': '', '款式': '', '袖长': '', '是否可外穿': '', '形态': '', '形状': '', '使用方式': '', '风格': '', '材质': '', '使用对象': '', '选购热点': '', '适用类型': '', '药品剂型': '', '使用方法': '', '主要成份': '', '功效': '', '功能': '', '控制类型': '', '商品详情图片': 'https://img30.360buyimg.com/sku/jfs/t10033/44/65601698/188193/91376f6/59c4c1d5Nafac3971.jpg,https://img30.360buyimg.com/sku/jfs/t8467/254/751640691/149223/a402d974/59ae5f64Na186d8e5.jpg,https://img30.360buyimg.com/sku/jfs/t8533/220/735008759/211266/39733e3a/59ae5f64N1d8be6c3.jpg,https://img30.360buyimg.com/sku/jfs/t7234/90/2425550181/186590/2a884206/59ae5f64N31532940.jpg,https://img30.360buyimg.com/sku/jfs/t8695/241/747158458/173738/73f35a31/59ae5f64N9d34a1cc.jpg,https://img30.360buyimg.com/sku/jfs/t8623/54/2195036173/175633/2e8fa1d3/59c4c1bfNed651fd4.jpg,https://img30.360buyimg.com/sku/jfs/t10411/27/57034466/228954/bd301edc/59c4c1d5Ne9ad59cf.jpg,https://img30.360buyimg.com/sku/jfs/t9526/55/57418414/185616/533430ff/59c4c1d5N016174a1.jpg,https://img30.360buyimg.com/sku/jfs/t9034/186/745718718/205145/7f0d790c/59ae5f6fN4b94578c.jpg,https://img30.360buyimg.com/sku/jfs/t8815/212/740131132/190975/70121fb3/59ae5f6fNf037fffa.jpg,https://img30.360buyimg.com/sku/jfs/t8119/227/734950816/225979/8390c947/59ae5f6fN4b469c7b.jpg,https://img30.360buyimg.com/sku/jfs/t8851/223/758197912/143246/3468d554/59ae5f6dN70d8716d.jpg,https://img30.360buyimg.com/sku/jfs/t7990/227/2407569715/170586/52c6151/59ae5f64N78a6e586.jpg,https://img30.360buyimg.com/sku/jfs/t22372/129/480270394/112573/ab92e78/5b0e44fdN751400ed.jpg', '商品视频': 'https://jdvideo.300hu.com/vodtransgzp1251412368/9031868223013059664/f0.f30.mp4?dockingId=bc6c0597-7b96-4fa6-acda-e1fcbf25ce19&storageSource=3', '医疗器械注册证编号或者备案凭证编号': '', '医疗器械名称': '', '型号': 'I5', '注册人或者备案人信息': '', '生产企业': '', '生产许可证或者备案凭证编号': '', '高血压警示': '有', '语音播报': '无', '加压方式': '智能加压', '测量时间': '', '记忆功能_次': '', '测量范围': '压力：0-40KPa/0-299mmHg 脉搏：（40-199）次/分钟', '是否自动关闭': '', '测量方法': '', '测量精度': '', '产品尺寸_cm': '', '显示方式': '高清大屏', '结构及组成': '', '适用范围': '', '通气模式': '', '氧气浓度': '', '氧气流量': '', '功率_w': '', '雾化颗粒是否可调': '', '雾化量是否可调': '', '禁忌症': '', '贮藏条件': '', '压缩机寿命': '', '雾化粒大小分布': '', '容量': '', '治疗板尺寸': '', '产品净重_kg': '', '最大载重_kg': '', '座宽_cm': '', '折叠后长宽高_cm': '', '前后轮尺寸_cm': '', '轮胎类型': '', '最小转弯半径_cm': '', '爬坡度数_度': '', '电池类型': '', '电池容量_AH': '', '理论充电时间_H': '', '最大速率_千瓦时': '', '额定续航_KM': '', '药品商品名': '', '药品通用名': '', '批准文号': '', '产品规格': '', '用法用量': '', '有效期': '', '适用年龄': '', '适用症功能主治': '', '包装规格': '', '库内是否按批号管理': '', '库内是否按供应商管理': '', '不良反应': '', '保质期': '', '功用': ''}
    # mysql.insert('goods', data)    #goods是表名
    # print(mysql.get_all('select innerurl from goods'))
    # mysql.close()

    #创建数据库
    #create database yjs default character set utf8