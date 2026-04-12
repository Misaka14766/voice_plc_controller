import json
import time
import threading
import logging
from typing import Optional

from aliyunsdkcore.client import AcsClient
from aliyunsdkcore.request import CommonRequest

logger = logging.getLogger(__name__)


class AliyunTokenManager:
    """阿里云 Token 管理器，自动刷新"""

    def __init__(self, access_key_id: str, access_key_secret: str, region: str = "cn-shanghai"):
        self.access_key_id = access_key_id
        self.access_key_secret = access_key_secret
        self.region = region

        self._token: Optional[str] = None
        self._expire_time: int = 0
        self._lock = threading.Lock()
        self._refresh_margin = 300  # 提前 5 分钟刷新

    def get_token(self) -> str:
        """获取当前有效的 Token，必要时自动刷新"""
        with self._lock:
            if self._should_refresh():
                self._refresh_token()
            return self._token or ""

    def _should_refresh(self) -> bool:
        """判断是否需要刷新 Token"""
        if self._token is None:
            return True
        current_time = int(time.time())
        return current_time >= (self._expire_time - self._refresh_margin)

    def _refresh_token(self):
        """通过 AK/SK 获取新 Token"""
        if not self.access_key_id or not self.access_key_secret:
            logger.error("阿里云 AK/SK 未配置，无法获取 Token")
            return

        try:
            client = AcsClient(self.access_key_id, self.access_key_secret, self.region)

            request = CommonRequest()
            request.set_method('POST')
            request.set_domain('nls-meta.cn-shanghai.aliyuncs.com')
            request.set_version('2019-02-28')
            request.set_action_name('CreateToken')

            response = client.do_action_with_exception(request)
            data = json.loads(response)

            if 'Token' in data and 'Id' in data['Token']:
                self._token = data['Token']['Id']
                self._expire_time = data['Token']['ExpireTime']
                logger.info(f"Token 获取成功，有效期至: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self._expire_time))}")
            else:
                logger.error(f"Token 响应格式异常: {data}")

        except Exception as e:
            logger.error(f"获取阿里云 Token 失败: {e}")
            raise