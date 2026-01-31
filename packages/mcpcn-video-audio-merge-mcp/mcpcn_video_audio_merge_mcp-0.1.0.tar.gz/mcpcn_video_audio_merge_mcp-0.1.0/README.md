# Video Audio Merge MCP

将视频文件与音频文件合并的 MCP Server。

## 功能

- 将音频文件合并到视频文件中
- 支持替换原有音频或添加新音频轨道
- 支持多种音频格式：mp3、aac、wav、flac、m4a、ogg、wma
- 支持批量处理多个视频文件

## 安装

```bash
uvx mcpcn-video-audio-merge-mcp
```

或通过 pip 安装:

```bash
pip install mcpcn-video-audio-merge-mcp
```

## 使用

```bash
mcpcn-video-audio-merge-mcp
```

## 工具

### merge_video_audio

将音频文件合并到视频文件中。

**参数:**
- `video_paths`: 输入视频文件路径列表,支持多个视频
- `audio_path`: 输入音频文件路径
- `output_dir`: 输出目录,合并后的视频文件保存位置
- `replace_audio`: 是否替换原有音频(默认 True),如果为 False 则添加新音频轨道
- `audio_codec`: 音频编码格式(默认 'aac')

## 依赖

- Python >=3.12
- FFmpeg(需系统安装)

## License

MIT License
