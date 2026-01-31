import subprocess

def compress_mp4(input_file, output_file, crf=28):
    """
    使用 FFmpeg 压缩 MP4 视频
    :param input_file: 输入文件路径
    :param output_file: 输出文件路径
    :param crf: 压缩质量 (0-51, 23是默认值, 数值越大压缩率越高)
    """
    command = [
        'ffmpeg',
        '-i', input_file,
        '-vcodec', 'libx264',
        '-crf', str(crf),
        '-preset', 'fast',
        '-acodec', 'copy',  # 保持音频不变
        output_file
    ]
    subprocess.run(command, check=True)

if __name__ == '__main__':
    compress_mp4(r"C:\Users\cheny\Desktop\myPythonTool\AI绘画\merged_output.mp4", '../output.mp4', crf=28)
