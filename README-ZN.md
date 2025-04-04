# 双语字幕生成器

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.0%2B-green.svg)](https://flask.palletsprojects.com/)
[![Whisper](https://img.shields.io/badge/Whisper-Medium-orange.svg)](https://openai.com/research/whisper)

一个用于从视频文件生成双语字幕或翻译现有SRT字幕的Web应用程序。基于OpenAI的Whisper语音识别和自定义翻译API。

## 功能

- 🎥 视频转双语字幕
- 🔊 自动提取音频
- 🌍 多语言翻译（中文/英文/西班牙文/法文/德文/日文/韩文/其他）
- ⏳ 实时进度跟踪
- 📄 SRT文件翻译
- 📁 批量处理支持

## 安装

### 环境要求
- Python 3.8+
- NVIDIA GPU（推荐）
- FFmpeg（用于音频处理）

```bash
# 克隆仓库
git clone https://github.com/sakmist/bilingual-subtitle-generator.git
cd bilingual-subtitle-generator

# 安装依赖
pip install -r requirements.txt

# 创建上传目录
mkdir uploads
```

## 使用

### 1. 启动服务器
```bash
python app.py
```

### 2. 访问Web界面
在浏览器中打开 `http://localhost:5000`

### 3. 处理文件
- **视频处理**：
  1. 上传视频文件（MP4/AVI/MOV）
  2. 选择目标语言
  3. 下载生成的字幕文件

- **字幕翻译**：
  1. 上传现有的SRT文件
  2. 选择目标语言
  3. 下载翻译后的字幕文件

![屏幕截图 2025-03-23 150235](https://github.com/user-attachments/assets/709910fb-4473-4fd7-b77a-27cdca603946)

## 配置

修改 `app.py` 以自定义设置：
```python
# Whisper配置
model = whisper.load_model("medium", device="cuda:1")  # 根据需要更改设备

# 翻译API端点
'http://your-translation-server/v1/chat/completions'  # 替换为你的端点
类似OpenAI 原代码为lms
```

## 技术细节

### 架构
```mermaid
graph TD
    A[用户上传] --> B{文件类型}
    B -->|视频| C[提取音频]
    B -->|SRT| D[解析字幕]
    C --> E[Whisper转录]
    D --> F[翻译API]
    E --> F
    F --> G[生成双语SRT]
    G --> H[用户下载]
```

### 支持格式
| 类型       | 格式                   |
|------------|---------------------------|
| 视频      | MP4, AVI, MOV, MKV        |
| 音频      | WAV (自动生成)      |
| 字幕      | SRT                       |

## 常见问题

**Q: 模型下载失败**  
A: 手动下载Whisper模型到 `~/.cache/whisper`

**Q: 翻译服务不可用**  
A: 确保你的翻译API端点正在运行并可访问

**Q: GPU内存不足**  
A: 尝试使用较小的Whisper模型（如 `base` 代替 `medium`）

## 许可证

MIT许可证。详见 [LICENSE](LICENSE)。

## 贡献

欢迎贡献！请按照以下步骤操作：
1. Fork仓库
2. 创建你的功能分支
3. 提交你的更改
4. 推送到分支
5. 提交Pull Request

---

**注意**：该项目需要单独的翻译服务以实现完整功能。演示实现使用了一个自定义API端点，应替换为你首选的翻译服务。
