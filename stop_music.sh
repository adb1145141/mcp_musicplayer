#!/bin/bash
# 停止音乐拉流服务

cd "$(dirname "$0")"
PID_FILE="serve_music.pid"

if [ ! -f "$PID_FILE" ]; then
  echo "未找到 PID 文件，服务可能未运行"
  exit 0
fi
PID=$(cat "$PID_FILE")
if kill -0 "$PID" 2>/dev/null; then
  kill "$PID"
  echo "已停止音乐服务 (PID $PID)"
else
  echo "进程 $PID 已不存在"
fi
rm -f "$PID_FILE"
