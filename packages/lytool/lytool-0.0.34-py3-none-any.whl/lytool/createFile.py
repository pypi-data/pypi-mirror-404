import os
path = os.curdir
for i in range(1,5001):
    filePath = os.path.join(path, '{}.html'.format(i))
    with open(filePath, 'w') as f:
        f.write('')