import os

if __name__ == '__main__':
    topDir = r'E:\project\program\ly_dictation\lyd_db\video\videoLibrary\juniorHighSchool'
    for dirName in os.listdir(topDir):
        dirPath = os.path.join(topDir, dirName)
        for fileName in os.listdir(dirPath):
            filePath = os.path.join(dirPath, fileName)
            if '.mp3' in filePath or '.MP3' in filePath:
                if '-' in filePath:
                    if os.path.exists(filePath):
                        os.remove(filePath)
                # mp3Path = filePath.replace('.mp4', '.mp3').replace('.MP4', '.mp3')
