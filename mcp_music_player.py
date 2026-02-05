# MCP 音乐播放器 - 供语音助手调用
# 返回 path（本机路径）与 stream_url（供 ESP32/网络设备拉流播放）
from fastmcp import FastMCP
import os
import random
import sys
from urllib.parse import quote

if sys.platform == "win32":
    sys.stderr.reconfigure(encoding="utf-8")
    sys.stdout.reconfigure(encoding="utf-8")

# 音乐目录（nginx 网站下的 JAYCHOU 绝对路径）
MUSIC_DIR = "/www/wwwroot/114.67.208.171/JAYCHOU"
# 音乐流 base URL：ESP32 等设备通过此 URL 拉流。需用 HTTP 服务暴露 JAYCHOU 目录后配置
# 例：http://192.168.1.100:8080/  或 https://echeverra.cn/mymusic/jayChou/
_raw = os.environ.get("MUSIC_BASE_URL", "").strip()
MUSIC_BASE_URL = (_raw.rstrip("/") + "/") if _raw else ""

mcp = FastMCP("MusicPlayer")

# 播放状态（跨 tool 调用保持）
_playlist: list[str] = []   # 当前列表为完整路径
_current_index: int = 0
_is_playing: bool = False


def _get_all_songs() -> list[str]:
    """获取音乐目录下所有 .mp3 的完整路径，按文件名排序。"""
    if not os.path.isdir(MUSIC_DIR):
        return []
    paths = []
    for name in os.listdir(MUSIC_DIR):
        if name.lower().endswith(".mp3"):
            paths.append(os.path.join(MUSIC_DIR, name))
    return sorted(paths)


def _ensure_playlist() -> list[str]:
    """确保播放列表已初始化（使用当前目录下所有 mp3）。"""
    global _playlist
    if not _playlist:
        _playlist = _get_all_songs()
    return _playlist


def _path_to_display_name(path: str) -> str:
    """从完整路径得到展示名（不含路径与扩展名）。"""
    return os.path.splitext(os.path.basename(path))[0]


def _path_to_stream_url(path: str) -> str | None:
    """若有 MUSIC_BASE_URL，返回该歌曲的流媒体 URL（供 ESP32 connecttohost 等使用）。"""
    if not MUSIC_BASE_URL:
        return None
    filename = os.path.basename(path)
    return MUSIC_BASE_URL + quote(filename)


def _song_item(path: str) -> dict:
    """单首歌曲的返回项（含 path 与可选的 stream_url）。"""
    item = {"name": _path_to_display_name(path), "path": path}
    url = _path_to_stream_url(path)
    if url:
        item["stream_url"] = url
        item["audio_url"] = url  # 语音助手常用字段，用于触发播放
    return item


def _play_payload(path: str, action: str = "play") -> dict:
    """统一构造「需要播放」时的返回结构，便于语音助手识别并真正播放。"""
    name = _path_to_display_name(path)
    url = _path_to_stream_url(path)
    out = {
        "success": True,
        "path": path,
        "name": name,
        "action": action,
        "should_play": True,
        "reply_for_tts": f"正在播放：{name}",
        "message": f"请使用下方 audio_url 或 stream_url 进行播放，不要只朗读。正在播放：{name}",
    }
    if url:
        out["stream_url"] = url
        out["audio_url"] = url
    return out


@mcp.tool()
def list_songs() -> dict:
    """列出所有可播放的歌曲。返回歌曲展示名、path 与 stream_url（若已配置 MUSIC_BASE_URL）。语音助手/ESP32 可用 stream_url 播放。"""
    songs = _ensure_playlist()
    items = [_song_item(p) for p in songs]
    return {"success": True, "songs": items, "count": len(items)}


@mcp.tool()
def play_random() -> dict:
    """随机选一首歌并设为当前曲目。返回 audio_url/stream_url，语音助手必须用该 URL 调用播放器播放，不能只朗读结果。"""
    global _current_index
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "message": "没有找到任何音乐文件", "path": None, "name": None, "should_play": False}
    _current_index = random.randint(0, len(playlist) - 1)
    path = playlist[_current_index]
    return _play_payload(path, "play")


@mcp.tool()
def play_song(song_name: str) -> dict:
    """根据用户说的歌名或关键词播放指定歌曲。song_name 可以是完整歌名或部分关键词（如「斗牛」「龙卷风」）。返回 audio_url：语音助手必须用该 URL 触发实际播放，不能只朗读。"""
    global _current_index
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "message": "没有找到任何音乐文件", "path": None, "name": None, "should_play": False}
    key = (song_name or "").strip().lower()
    if not key:
        return {"success": False, "message": "请提供歌名或关键词", "path": None, "name": None, "should_play": False}
    for i, path in enumerate(playlist):
        name = _path_to_display_name(path)
        if key in name.lower():
            _current_index = i
            return _play_payload(path, "play")
    return {
        "success": False,
        "message": f"未找到包含「{song_name}」的歌曲，可先调用 list_songs 查看歌单。",
        "path": None,
        "name": None,
        "should_play": False,
    }


@mcp.tool()
def play() -> dict:
    """开始/继续播放。返回 audio_url，语音助手必须用该 URL 触发播放。"""
    global _is_playing
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "message": "没有找到任何音乐文件", "path": None, "name": None, "should_play": False}
    _is_playing = True
    path = playlist[_current_index]
    return _play_payload(path, "play")


@mcp.tool()
def pause() -> dict:
    """暂停播放。语音助手收到后应暂停当前正在播放的音频。"""
    global _is_playing
    _is_playing = False
    return {
        "success": True,
        "action": "pause",
        "should_play": False,
        "reply_for_tts": "已暂停",
        "message": "已请求暂停，请在助手侧执行暂停。",
    }


@mcp.tool()
def next_song() -> dict:
    """下一首。返回 audio_url，语音助手必须用该 URL 播放，不能只朗读。"""
    global _current_index
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "message": "没有找到任何音乐文件", "path": None, "name": None, "should_play": False}
    _current_index = (_current_index + 1) % len(playlist)
    path = playlist[_current_index]
    out = _play_payload(path, "play")
    out["reply_for_tts"] = f"下一首：{_path_to_display_name(path)}"
    out["message"] = f"下一首，请使用 audio_url 播放：{_path_to_display_name(path)}"
    return out


@mcp.tool()
def previous_song() -> dict:
    """上一首。返回 audio_url，语音助手必须用该 URL 播放。"""
    global _current_index
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "message": "没有找到任何音乐文件", "path": None, "name": None, "should_play": False}
    _current_index = (_current_index - 1) % len(playlist)
    path = playlist[_current_index]
    out = _play_payload(path, "play")
    out["reply_for_tts"] = f"上一首：{_path_to_display_name(path)}"
    out["message"] = f"上一首，请使用 audio_url 播放：{_path_to_display_name(path)}"
    return out


@mcp.tool()
def get_current() -> dict:
    """获取当前曲目信息，不改变播放状态。返回含 stream_url/audio_url。"""
    playlist = _ensure_playlist()
    if not playlist:
        return {"success": False, "path": None, "name": None}
    path = playlist[_current_index]
    out = {"success": True, "path": path, "name": _path_to_display_name(path), "index": _current_index + 1, "total": len(playlist)}
    url = _path_to_stream_url(path)
    if url:
        out["stream_url"] = out["audio_url"] = url
    return out


if __name__ == "__main__":
    mcp.run(transport="stdio")
