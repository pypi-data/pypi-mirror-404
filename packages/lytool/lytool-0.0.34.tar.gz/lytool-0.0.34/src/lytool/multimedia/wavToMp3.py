import os
from pydub import AudioSegment

def wavToMp3(filePath):
    audio = AudioSegment.from_wav(filePath)
    audio.export(filePath.replace('.wav', '')+'.mp3', format="mp3", bitrate="192k")  # bitrate 可选：128k, 192k, 320k
    os.remove(filePath)