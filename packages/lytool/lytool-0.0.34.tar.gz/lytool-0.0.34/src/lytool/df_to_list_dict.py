# df 转为 [{k:v1},{k:v2}]

import pandas as pd
def df_to_ld(df):
    data_list = []
    for i in range(len(df)):
        data_dict = {}
        for key, value in df.iloc[i].items():
            data_dict[key] = value
        data_list.append(data_dict)
    return data_list

if __name__ == '__main__':
    df = pd.DataFrame([
        {'a':1,'b':2},
        {'a':11,'b':22},
    ])
    data_list = df_to_ld(df)
    print(data_list, '')
