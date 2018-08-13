import werkzeug.serving
import threading
import ssl


class Server(object):
    def __init__(self, app):
        self.app = app
        self.ssl_ctx = None
        self.ssl = False

    def add_ssl_cert(self, cert, key):
        self.ssl_ctx = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
        self.ssl_ctx.load_cert_chain(cert, key)
        self.ssl = True

    def start(self, host, port):
        self.server = werkzeug.serving.make_server(
            host, port, self.app, ssl_context=self.ssl_ctx)
        self.thread = threading.Thread(
            target=self.server.serve_forever, name='Server')
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        self.server.shutdown()
        self.thread.join()
