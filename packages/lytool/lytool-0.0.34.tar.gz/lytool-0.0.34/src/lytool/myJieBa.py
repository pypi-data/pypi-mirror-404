import jieba
def myJieBa(text):
    text_list = [i for i in jieba.cut(text) if len(i) > 0 and i != '，' and i != '。' and i != '！' and i != '；' and i != '？']
    return text_list