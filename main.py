import os
import json
import re
import copy
import requests
from flask import Flask, render_template, request, jsonify, Response
from moviepy import VideoFileClip
import whisper
from datetime import timedelta
app = Flask(__name__)

# 支持的语言列表
LANGUAGES = {
    'no': '不翻译',
    'cn': "Chinese",
    'en': 'English',
    'es': 'Spanish',
    'fr': 'French',
    'de': 'German',
    'ja': 'Japanese',
    'ko': 'Korean'
}

def extract_audio(video_path, output_audio_path="temp_audio.wav"):
    """从视频中提取音频"""
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(output_audio_path, codec="pcm_s16le", fps=16000)  # Whisper需要16kHz采样率
    return output_audio_path


def transcribe(audio_path):
    """使用Whisper模型转录音频并翻译"""
    model = whisper.load_model("medium",device="cuda:1")  # 加载medium模型
    result = model.transcribe(audio_path)  # 直接生成英文字幕并翻译
    return result["segments"]


def create_bilingual_srt(segments, output_path="output.srt"):
    """生成中英双语SRT文件"""
    srt_content = []
    for i, segment in enumerate(segments, 1):
        start = timedelta(seconds=segment['start'])
        end = timedelta(seconds=segment['end'])
        text_en = segment['text'].strip()
        text_zh = segment.get('translation', '').strip()  # 假设翻译结果在字段中

        # 格式化为SRT
        srt_block = f"{i}\n{start} --> {end}\n{text_en}\n{text_zh}\n\n"
        srt_content.append(srt_block)

    with open(output_path, "w", encoding="utf-8") as f:
        f.writelines(srt_content)


def parse_srt(content):
    """解析SRT文件内容为结构化的列表"""
    blocks = []
    pattern = re.compile(
        r'(\d+)\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)(?=\n\n|\Z)',
        re.DOTALL
    )
    matches = pattern.findall(content)
    for match in matches:
        blocks.append({
            'index': int(match[0]),
            'start': match[1],
            'end': match[2],
            'text': match[3].strip()
        })
    return blocks


def build_srt(blocks):
    """将结构化列表转换回SRT格式"""
    srt_content = []
    for block in blocks:
        srt_content.append(
            f"{block['index']}\n"
            f"{block['start']} --> {block['end']}\n"
            f"{block['text']}\n"
        )
    return "\n".join(srt_content)


@app.route('/')
def index():
    return render_template('index.html', languages=LANGUAGES)
@app.route('/video',methods=['POST'])
@app.route('/video',methods=['POST'])
def get_video_to_srt():
    try:
        # 在请求上下文中提前获取所有必要数据
        target_lang = request.form['language']
        video_file = request.files['video_file']
        video_file_name = f"./uploads/{video_file.filename}"
        with open(video_file_name,"wb") as video_data:
            video_data.write(video_file.read())
            video_data.close()

        # 将必要参数传入生成器
        return Response(
            video_worker(video_file_name,video_file,target_lang),
            mimetype='text/event-stream'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500
def video_worker(video_file_name,video_file,target_lang):
    # 步骤1: 提取音频
    yield json.dumps({
        "progress": 0,
        "task":"提取音频"
    }) + "\n"
    audio_path = extract_audio(video_file_name, output_audio_path=f"./uploads/{video_file.filename}.wav")

    # 步骤2: 转录并翻译
    yield json.dumps({
        "progress": 5,
        "task":"转录中，此处比较耗时，耐心等待"
    }) + "\n"
    segments = transcribe(audio_path)
    original_blocks = []
    for i, segment in enumerate(segments, 1):
        start = timedelta(seconds=segment['start'])
        end = timedelta(seconds=segment['end'])
        text = segment['text'].strip()
        original_blocks.append({
            'index': i,
            'start': str(start).replace('.', ','),
            'end': str(end).replace('.', ','),
            'text':text
        })
    yield json.dumps({
        "progress": 10,
        "task":"提交翻译"
    }) + "\n"
    filename = f"{''.join(video_file.filename.rsplit('.')[:-1])}_{target_lang}.srt"

    # 创建深拷贝避免修改原始数据
    translated_blocks = copy.deepcopy(original_blocks)
    if target_lang != 'no':
        for chunk in generate(target_lang, original_blocks, translated_blocks, filename):
            yield chunk
    else:
        yield json.dumps({
            "completed": True,
            "filename": filename,
            "srt_content": build_srt(translated_blocks),
            "original": original_blocks,
            "translated": translated_blocks
        }) + "\n".encode('utf-8')

@app.route('/srt', methods=['POST'])
@app.route('/srt', methods=['POST'])
def translate_subtitles():
    try:
        # 在请求上下文中提前获取所有必要数据
        target_lang = request.form['language']
        srt_file = request.files['srt_file']
        srt_content = srt_file.read().decode('utf-8')
        filename = f"{''.join(srt_file.filename.rsplit('.')[:-1])}_{target_lang}.srt"
        original_blocks = parse_srt(srt_content)

        # 创建深拷贝避免修改原始数据
        translated_blocks = copy.deepcopy(original_blocks)

        # 将必要参数传入生成器
        return Response(
            generate(target_lang, original_blocks, translated_blocks, filename),
            mimetype='text/event-stream'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def generate(target_lang, original_blocks, translated_blocks, filename,double_srt=True):
    """流式生成器函数"""
    try:
        chunk_size = 10
        total_chunks = (len(original_blocks) + chunk_size - 1) // chunk_size

        for chunk_idx in range(total_chunks):
            start = chunk_idx * chunk_size
            end = start + chunk_size
            current_chunk = original_blocks[start:end]
            current_data = {_['index']: _['text'] for _ in current_chunk}

            # 发送实时进度
            progress = (chunk_idx + 1) / total_chunks * 100
            yield json.dumps({
                "progress": round(progress, 1),
                "task":f"在翻译{start}-{end}共{total_chunks}"
            }) + "\n"

            # 翻译处理
            system_prompt = f"""You are a professional translator. Translate video subtitles to {LANGUAGES[target_lang]}.
            Preserve numbering and JSON structure.Only provide the translated content by JSON structure, do not include any explanations."""
            while True:
                response = requests.post(
                    'http://192.168.1.12:1234/v1/chat/completions',
                    json={
                        'model': 'gemma-3-12b-it',
                        'messages': [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": f"{current_data}"},
                        ],
                        'temperature': 0.7
                    }
                )

                translated_chunk = response.json()['choices'][0]['message']['content']
                try:
                    matches = re.findall(r'\{.*?\}', translated_chunk, re.DOTALL)
                    translated_dict = json.loads(matches[0])
                    for key in translated_dict:
                        if not double_srt:
                            translated_blocks[int(key) - 1]['text'] = translated_dict[key]
                        else:
                            translated_blocks[int(key) - 1]['text'] += f"\n{translated_dict[key]}"

                    break
                except Exception as e:
                    yield json.dumps({"noshow": f"解析错误: {str(e)}"}) + "\n"
                    # return


        # 生成最终结果
        srt_content = build_srt(translated_blocks)
        yield json.dumps({
            "completed": True,
            "filename": filename,
            "srt_content": srt_content,
            "original": original_blocks,
            "translated": translated_blocks
        }) + "\n"

    except Exception as e:
        yield json.dumps({"error": str(e)}) + "\n"


if __name__ == '__main__':
    app.run(debug=False,host="0.0.0.0" ,port=5000)