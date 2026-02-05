#!/usr/bin/env python3
"""
在局域网内暴露 JAYCHOU 音乐目录，供 ESP32 / 语音助手通过 stream_url 拉流播放。

用法:
  python serve_music.py [端口]
  默认端口 8080。确保防火墙放行该端口。

MCP 配置 stream_url:
  本机或同一局域网内播放时，设环境变量（或 mcp_config.json 的 env）:
  MUSIC_BASE_URL=http://<本机局域网IP>:8080/
  例如: MUSIC_BASE_URL=http://192.168.1.100:8080/
"""
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

# 与 mcp_music_player.py 一致
MUSIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "JAYCHOU")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8080


class MusicHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=MUSIC_DIR, **kwargs)

    def end_headers(self):
        # 允许跨域，方便 ESP32 等设备拉流
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()


def main():
    if not os.path.isdir(MUSIC_DIR):
        print(f"错误: 音乐目录不存在: {MUSIC_DIR}")
        sys.exit(1)
    server = HTTPServer(("0.0.0.0", PORT), MusicHandler)
    print(f"音乐服务: http://0.0.0.0:{PORT}/")
    print(f"目录: {MUSIC_DIR}")
    print("按 Ctrl+C 停止")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.shutdown()


if __name__ == "__main__":
    main()
