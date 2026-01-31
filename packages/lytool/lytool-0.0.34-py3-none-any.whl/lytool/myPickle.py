import pickle
def white_pickle_file(data, file_path='./1.txt'):
    with open(file_path, 'wb') as f:
        pickle.dump(data, f)

def read_pickle_file(file_path='./1.txt'):
    with open(file_path, 'rb') as f:
        data = pickle.load(f)
    return data