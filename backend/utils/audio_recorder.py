import pyaudio
import queue
from backend.config import settings

class AudioRecorder:
    def __init__(self):
        self.p = pyaudio.PyAudio()
        self.stream = None
        self.recording = False
        self.queue = queue.Queue()
        self.chunk = settings.AUDIO_CHUNK  # 默认 1024

    def start(self):
        self.stream = self.p.open(
            format=settings.AUDIO_FORMAT,          # paInt16
            channels=1,
            rate=settings.ASR_SAMPLE_RATE,
            input=True,
            frames_per_buffer=self.chunk,
            stream_callback=self._callback
        )
        self.recording = True

    def _callback(self, in_data, frame_count, time_info, status):
        if self.recording:
            self.queue.put(in_data)
        return (None, pyaudio.paContinue)

    def stop(self):
        self.recording = False
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        # 清空队列
        while not self.queue.empty():
            self.queue.get()

    def get_chunk(self, timeout=0.1):
        try:
            return self.queue.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        if self.stream:
            self.stream.close()
        self.p.terminate()