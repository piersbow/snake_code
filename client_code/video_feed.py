import webview

server_ip = '10.42.0.1'

webview.create_window('Camera', 'http://' + server_ip + ':8889/cam1')
webview.start()