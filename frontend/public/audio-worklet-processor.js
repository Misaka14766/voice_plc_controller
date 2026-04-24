class MyAudioProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.isConnected = false;

    // 监听主线程（Vue）发过来的消息
    this.port.onmessage = (event) => {
      const { type } = event.data;
      if (type === 'connect') this.isConnected = true;
      if (type === 'disconnect') this.isConnected = false;
    };
  }

  process(inputs, outputs, parameters) {
    // 未连接时不处理音频
    if (!this.isConnected) return true;

    const input = inputs[0];
    if (!input || input.length === 0) return true;

    // 获取单声道音频数据
    const inputData = input[0];

    // 转 16bit PCM（所有 ASR 标准格式）
    const pcm16 = new Int16Array(inputData.length);
    for (let i = 0; i < inputData.length; i++) {
      let s = Math.max(-1, Math.min(1, inputData[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }

    // 发送给 Vue 主线程
    this.port.postMessage(
      { type: 'audioData', data: pcm16.buffer },
      [pcm16.buffer]
    );

    return true;
  }
}

// 注册名称
registerProcessor('audio-worklet-processor', MyAudioProcessor);