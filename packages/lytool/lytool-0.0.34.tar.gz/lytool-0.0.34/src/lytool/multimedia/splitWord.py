import re

def getWordToGenerateVoice(chineseList, wordsList):
    '''
    按照分割符号拆分单词
    chineseList:
    wordsList： ['a|b', 'on【e】']
    return ["说[0.5s]say[1s]有[0.5s]have[1s]狼[0.5s]wolf[1s]来[0.5s]come[1s]老鼠[0.5s]mouse[1s]狐狸[0.5s]fox[1s]帮助[0.5s]help[1s]水[0.5s]water[1s]羊[0.5s]sheep[1s]看[0.5s]look[1s]"]
    '''
    wordList = []
    for word in wordsList:
        parts = re.findall(r'(\w+)|(【\w+】)|( )|([,.?!ˈ])|(《\w+》)', word)
        wordOnceList = []
        for i in parts:
            for j in i:
                if len(j) >= 1:
                    wordOnceList.append(j)
        word = ''.join(wordOnceList)
        word = word.replace('《', '').replace('》', '').replace('|', '').replace('【', '').replace('】', '')
        wordList.append(word)
    chineseList = [i.split('.')[-1].replace(' ', '') for i in chineseList]
    # 两两配对
    paired = [a + '[0.5s]' + b + '[1s]' for a, b in zip(chineseList, wordList)]
    # 每10个元素拼接成一个字符串
    result = [''.join(paired[i:i + 10]) for i in range(0, len(paired), 10)]
    return result


def getWordToDatabase(oneUnitWords):
    '''
    按照分割符号拆分单词
    oneUnitWords： ['a|b', 'on【e】']
    return [[{'a':1}, {'b':2}], [{'on':1}, {'e':0}]]
    '''
    res = []
    for word in oneUnitWords:
        parts = re.findall(r'(\w+)|(【\w+】)|( )|([,.?!ˈ])|(《\w+》)', word)
        n = 1
        b = []
        for i in parts:
            for j in i:
                wordItem = {}
                if len(j) > 0:
                    # -2无下划线 -1无下划线 0灰色 1紫色 2白色
                    if "【" in j:
                        j = j.replace('【', '').replace('】', '')
                        wordItem[j] = 0
                    elif "《" in j:
                        n -= 1
                        j = j.replace('《', '').replace('》', '')
                        wordItem[j] = 0
                    elif " " == j:
                        wordItem['&nbsp;'] = -2
                        # wordItem[j] = -2
                    elif "ˈ" == j or "," == j or "." == j or "?" == j or "!" == j or "ˌ" == j:
                        wordItem[j] = -1
                    else:
                        wordItem[j] = n
                        n += 1
                    b.append(wordItem)
        res.append(b)
    return res