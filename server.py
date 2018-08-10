import werkzeug.serving
import threading


class Server(object):
    def __init__(self, host, port, app):
        self.server = werkzeug.serving.make_server(host, port, app)
        self.thread = threading.Thread(
            target=self.server.serve_forever, name='Server')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()
