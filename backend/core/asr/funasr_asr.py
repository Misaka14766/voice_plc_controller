import numpy as np
from funasr import AutoModel
from .base import BaseASR
from backend.config import settings
import logging

logger = logging.getLogger(__name__)


class FunASRStream(BaseASR):
    def __init__(self):
        self.model = AutoModel(
            model=settings.ASR_MODEL,
            device=settings.ASR_DEVICE,
            disable_pbar=True,
            disable_update=True,
        )
        self.cache = {}
        self.callback = None

        # 流式参数
        self.chunk_size = settings.asr_chunk_size
        self.encoder_chunk_look_back = settings.ASR_ENCODER_CHUNK_LOOK_BACK
        self.decoder_chunk_look_back = settings.ASR_DECODER_CHUNK_LOOK_BACK

        self.sample_rate = settings.ASR_SAMPLE_RATE
        self.chunk_stride = self.chunk_size[1] * 960

        # 音频缓冲区
        self.buffer = np.array([], dtype=np.float32)

        # 累积文本
        self.full_text = ""

        logger.info(
            f"FunASR 流式模型加载成功，chunk_size={self.chunk_size}, "
            f"stride={self.chunk_stride} samples ({self.chunk_stride/self.sample_rate:.2f}s)"
        )

    def set_callback(self, callback=None):
        self.callback = callback

    def start(self):
        self.full_text = ""
        self.buffer = np.array([], dtype=np.float32)

    def stop(self):
        pass

    def feed_chunk(self, chunk: bytes, is_final: bool = False) -> str:
        # 将新音频数据加入缓冲区
        if len(chunk) > 0:
            audio_np = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32768.0
            self.buffer = np.concatenate([self.buffer, audio_np])

        # 处理缓冲区中的完整块
        while len(self.buffer) >= self.chunk_stride:
            speech_chunk = self.buffer[:self.chunk_stride]
            self.buffer = self.buffer[self.chunk_stride:]

            res = self.model.generate(
                input=speech_chunk,
                cache=self.cache,
                is_final=False,
                chunk_size=self.chunk_size,
                encoder_chunk_look_back=self.encoder_chunk_look_back,
                decoder_chunk_look_back=self.decoder_chunk_look_back,
            )
            if res and len(res) > 0:
                text = res[0].get("text", "")
                if text:
                    # 直接拼接新识别的文本（增量）
                    self.full_text += text
                    if self.callback:
                        self.callback(self.full_text, False)

        # 最终帧处理剩余数据
        if is_final:
            if len(self.buffer) > 0:
                res = self.model.generate(
                    input=self.buffer,
                    cache=self.cache,
                    is_final=True,
                    chunk_size=self.chunk_size,
                    encoder_chunk_look_back=self.encoder_chunk_look_back,
                    decoder_chunk_look_back=self.decoder_chunk_look_back,
                )
            else:
                res = self.model.generate(
                    input=None,
                    cache=self.cache,
                    is_final=True,
                    chunk_size=self.chunk_size,
                    encoder_chunk_look_back=self.encoder_chunk_look_back,
                    decoder_chunk_look_back=self.decoder_chunk_look_back,
                )
            if res and len(res) > 0:
                final_text = res[0].get("text", "")
                if final_text:
                    self.full_text += final_text

            # 通过回调通知最终结果
            if self.callback:
                self.callback(self.full_text, True)

            return self.full_text

        return self.full_text

    def reset(self):
        self.cache = {}
        self.buffer = np.array([], dtype=np.float32)
        self.full_text = ""