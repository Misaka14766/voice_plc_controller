type OnPartialCallback = (text: string) => void
type OnFinalCallback = (text: string) => void
type OnErrorCallback = (error: Event) => void

export class ASRWebSocket {
  private ws: WebSocket | null = null
  private _isConnected = false
  public onPartial: OnPartialCallback | null = null
  public onFinal: OnFinalCallback | null = null
  public onError: OnErrorCallback | null = null

  connect() {
    const wsUrl = `${import.meta.env.VITE_WS_BASE_URL}/ws/asr`
    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      this._isConnected = true
      console.log('WebSocket 已连接')
    }

    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'partial' && this.onPartial) {
          this.onPartial(data.text)
        } else if (data.type === 'final' && this.onFinal) {
          this.onFinal(data.text)
        }
      } catch (e) {
        console.error('解析WebSocket消息失败:', e)
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket 错误:', error)
      if (this.onError) this.onError(error)
    }

    this.ws.onclose = () => {
      this._isConnected = false
      console.log('WebSocket 已断开')
    }
  }

  sendAudio(base64Data: string, isFinal: boolean = false) {
    if (this.ws && this._isConnected) {
      this.ws.send(JSON.stringify({
        type: 'audio',
        data: base64Data,
        is_final: isFinal
      }))
    }
  }

  reset() {
    if (this.ws && this._isConnected) {
      this.ws.send(JSON.stringify({ type: 'reset' }))
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  get isConnected() {
    return this._isConnected
  }
}
