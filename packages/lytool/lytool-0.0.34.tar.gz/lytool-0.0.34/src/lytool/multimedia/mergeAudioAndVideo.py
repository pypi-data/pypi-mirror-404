import os
from moviepy import VideoFileClip, concatenate_videoclips
from pydub import AudioSegment


def merge_mp3_files(file_list, output_file):
    """
    合并多个MP3文件

    :param file_list: MP3文件路径列表
    :param output_file: 合并后的输出文件路径
    """
    combined = AudioSegment.empty()

    for file in file_list:
        sound = AudioSegment.from_mp3(file)
        combined += sound

    combined.export(output_file, format="mp3")

def merge_mp4_files(file_list, output_file):
    """
    使用moviepy合并MP4文件

    :param file_list: MP4文件路径列表
    :param output_file: 合并后的输出文件路径
    """
    clips = [VideoFileClip(file) for file in file_list]
    final_clip = concatenate_videoclips(clips)
    final_clip.write_videofile(output_file, codec="libx264", audio_codec="aac")



def extract_number(filepath):
    # 获取文件名部分（去掉路径）
    filename = filepath.split('\\')[-1]
    # 提取数字部分（去掉扩展名）
    number_part = filename.split('_')[-1].split('.')[0]
    return int(number_part)

if __name__ == '__main__':
    topDir = r'E:\AItool\comfyUI\ComfyUI-aki-v1.4\input\digitalHuman\aesopFables'
    files = []
    for i in os.listdir(topDir):
        if os.path.isdir(os.path.join(topDir, i)):
            for j in os.listdir(os.path.join(topDir, i)):
                if j.endswith('.mp4'):
                    files.append(os.path.join(topDir, i, j))

    # 使用sorted函数和自定义的key进行排序
    sorted_list = sorted(files, key=extract_number)
    merge_mp4_files(sorted_list, "merged_output.mp4")
    