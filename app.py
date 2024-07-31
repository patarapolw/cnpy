import webview


class Api:
    def log(self, value):
        print(value)


webview.create_window(
    "Test",
    html="<button onclick='pywebview.api.log(\"Woah dude!\")'>Click me</button>",
    js_api=Api(),
)
webview.start()
