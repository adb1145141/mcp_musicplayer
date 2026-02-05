#!/bin/bash
# 启动音乐拉流服务（供 MCP 返回的 stream_url 使用）
# 停止用: ./stop_music.sh

cd "$(dirname "$0")"
PORT=8080
PID_FILE="serve_music.pid"

if [ -f "$PID_FILE" ]; then
  OLD_PID=$(cat "$PID_FILE")
  if kill -0 "$OLD_PID" 2>/dev/null; then
    echo "音乐服务已在运行 (PID $OLD_PID)，端口 $PORT"
    echo "拉流地址: http://127.0.0.1:$PORT/"
    exit 0
  fi
  rm -f "$PID_FILE"
fi

# 端口已被占用时视为已在运行（可能是之前未用本脚本启动的）
if command -v ss &>/dev/null; then
  if ss -tlnp 2>/dev/null | grep -q ":$PORT "; then
    echo "端口 $PORT 已监听，音乐拉流服务可能已在运行"
    echo "拉流地址: http://127.0.0.1:$PORT/"
    exit 0
  fi
elif command -v netstat &>/dev/null; then
  if netstat -tln 2>/dev/null | grep -q ":$PORT "; then
    echo "端口 $PORT 已监听，音乐拉流服务可能已在运行"
    echo "拉流地址: http://127.0.0.1:$PORT/"
    exit 0
  fi
fi

# 用本机 Python 即可（仅用标准库）
python3 serve_music.py "$PORT" &
echo $! > "$PID_FILE"
sleep 1
if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
  echo "音乐服务已启动，端口 $PORT"
  echo "拉流地址: http://127.0.0.1:$PORT/"
  echo "停止: ./stop_music.sh"
else
  echo "启动失败（若端口被占用可先执行 ./stop_music.sh 或 kill 占用进程）"
  rm -f "$PID_FILE"
  exit 1
fi
