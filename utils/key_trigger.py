from pynput import keyboard

class KeyTrigger:
    def __init__(self, on_press=None, on_release=None, trigger_key="space"):
        self.on_press = on_press
        self.on_release = on_release
        self.trigger_key = getattr(keyboard.Key, trigger_key, keyboard.Key.space)
        self.listener = None

    def start(self):
        def _on_press(key):
            if key == self.trigger_key and self.on_press:
                self.on_press()
        def _on_release(key):
            if key == self.trigger_key and self.on_release:
                self.on_release()
        self.listener = keyboard.Listener(on_press=_on_press, on_release=_on_release)
        self.listener.start()

    def stop(self):
        if self.listener:
            self.listener.stop()