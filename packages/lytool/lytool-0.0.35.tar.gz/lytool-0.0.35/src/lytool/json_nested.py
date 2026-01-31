# json嵌套
# from myClass.operating_mysql import Operating_MySql
# operating_mySql = Operating_MySql('college')
# ability = operating_mySql.get_json(sql='''select * from ability''')
# print(ability)

# (1, '编程能力', '', 0),
# (2, '数学能力', '', 0),
# (3, '核心能力', '', 0),
# (4, '自然语言', '', 0),
# (5, '机器视觉', '', 0),
# (6, '商业智能', '', 0);


abc = {
    "编程能力": [
        {"大课名": "python入门", "章": "第一章", "节": "第1节", "章节名": "导学视频", "课程名": "导学视频", "播放地址": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/a9045979-98bd-4969-901f-7aec7df9dc55.mp4", "大课图片": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/d6d2865a-9c71-42a6-bc92-843ee831f473.png"},
        {"大课名": "python入门", "章": "第一章", "节": "第2节", "章节名": "安装环境", "课程名": "windows系统中安装python环境", "播放地址": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/a9045979-98bd-4969-901f-7aec7df9dc55.mp4", "大课图片": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/d6d2865a-9c71-42a6-bc92-843ee831f473.png"},
        {"大课名": "python入门", "章": "第二章", "节": "第1节", "章节名": "初始python脚本", "课程名": "Mac系统中安装Python环境", "播放地址": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/a9045979-98bd-4969-901f-7aec7df9dc55.mp4", "大课图片": "https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/d6d2865a-9c71-42a6-bc92-843ee831f473.png"},
        {"大课名": "python入门", "章": "第三章", "节": "第1节", "章节名": "python运算符", "安装包": [{"windows安装软件":"https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/29bbb912-28fa-4680-b511-0f9f05a7d652.rar", "mac安装软件":"https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/29bbb912-28fa-4680-b511-0f9f05a7d652.rar", "文档":"https://vkceyugu.cdn.bspapp.com/VKCEYUGU-20e48e66-e9f3-408b-9b09-7f394b49da0c/29bbb912-28fa-4680-b511-0f9f05a7d652.rar"}]}
    ]
}
