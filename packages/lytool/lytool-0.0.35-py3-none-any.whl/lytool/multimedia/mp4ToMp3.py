import os
from moviepy import VideoFileClip

def extract_audio_from_mp4(mp4_file, mp3_file):
    # 加载视频文件
    video = VideoFileClip(mp4_file)
    # 提取音频
    audio = video.audio
    # 保存为MP3
    audio.write_audiofile(mp3_file)
    # 关闭视频和音频对象
    audio.close()
    video.close()


def mp4ToMp3(topDir):
    for dirName in os.listdir(topDir):
        dirPath = os.path.join(topDir, dirName)
        for fileName in os.listdir(dirPath):
            filePath = os.path.join(dirPath, fileName)
            if '.mp4' in filePath or '.MP4' in filePath:
                mp3Path = filePath.replace('.mp4', '.mp3').replace('.MP4', '.mp3')
                if os.path.exists(mp3Path) == False:
                    extract_audio_from_mp4(filePath, mp3Path)

def removeMp4(topDir):
    for dirName in os.listdir(topDir):
        dirPath = os.path.join(topDir, dirName)
        for fileName in os.listdir(dirPath):
            filePath = os.path.join(dirPath, fileName)
            if '.mp4' in filePath or '.MP4' in filePath:
                if os.path.exists(filePath) == True:
                    os.remove(filePath)

if __name__ == '__main__':

    topDir = r'E:\project\program\ly_dictation\lyd_db\video\videoLibrary\re_primarySchool\mp4_srt'

    # mp4ToMp3(topDir)
    removeMp4(topDir)