from pydub import AudioSegment
from pydub.utils import make_chunks


def splitMp3(self, mp3Path):
    # 加载音频文件
    audio = AudioSegment.from_file(mp3Path, format="mp3")

    # 方法1：按时间分割（例如每10秒一段）
    chunk_length_ms = 20000  # 10秒
    chunks = make_chunks(audio, chunk_length_ms)

    # 保存分割后的片段
    for i, chunk in enumerate(chunks):
        chunk.export(f"{mp3Path}/output_chunk_{i}.mp3", format="mp3")