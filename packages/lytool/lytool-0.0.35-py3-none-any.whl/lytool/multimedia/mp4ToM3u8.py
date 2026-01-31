import os.path

import ffmpeg

def mp4ToM3u8(inputFileName, outFileName, m3u8DirPath, m3u8DirName):
    (
        ffmpeg
        .input(inputFileName)
        .output(
            outFileName,
            format="hls",          # 输出 HLS 格式
            hls_time=10,           # 每个 TS 片段时长（秒）
            hls_list_size=0,       # 保留所有片段记录（0 表示无限）
            hls_segment_filename=os.path.join(m3u8DirPath, f"{m3u8DirName}_%03d.ts"),   # TS 片段命名格式
            vcodec="libx264",      # 视频编码
            acodec="aac",          # 音频编码
            crf=23,                # 视频质量（0-51，越小质量越高）
        )
        .run()
    )

def oneVideoToM3u8(inputFileName):
    m3u8DirPath = inputFileName.split('.')[0]
    m3u8DirName = m3u8DirPath.split('\\')[-1]
    if not os.path.exists(m3u8DirPath):
        os.makedirs(m3u8DirPath)
    outFileName = os.path.join(m3u8DirPath, m3u8DirPath.split('\\')[-1] + '.m3u8')
    mp4ToM3u8(inputFileName, outFileName, m3u8DirPath, m3u8DirName)


if __name__ == '__main__':
    inputFileName = r"E:\project\program\ly_dictation\lyd_db\video\videoLibrary\aesopFables\1_20\aesopFables1_20.mp4"
    oneVideoToM3u8(inputFileName)


