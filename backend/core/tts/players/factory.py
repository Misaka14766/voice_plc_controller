from backend.config import settings
from .pygame_player import PygamePlayer
from .system_player import SystemPlayer


def get_player():
    """根据配置返回播放器实例"""
    player_type = settings.TTS_PLAYER.lower()
    if player_type == "pygame":
        return PygamePlayer()
    elif player_type == "system":
        return SystemPlayer()
    else:
        raise ValueError(f"未知的播放器类型: {player_type}")