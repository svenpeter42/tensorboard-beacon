import os
import sys
import threading
import tempfile
from collections import namedtuple


from tensorboard.backend import application
from tensorboard.default import get_plugins

from werkzeug.exceptions import NotFound

TBLogDir = namedtuple('TBLogDir', ['name', 'path', 'symlink'])



class TensorBoardInstance(object):
    def __init__(self, name):
        self.name = name
        self.tmpdir = tempfile.TemporaryDirectory()
        self.logdirs = {}
        self.app = application.standard_tensorboard_wsgi(self.tmpdir.name, True, 10, get_plugins())

    def _name_exists(self, name):
        for i in self.logdirs:
            if i.name == name:
                return True
        return False

    def add_logdir(self, path):
        if path in self.logdirs:
            return True
        if not os.path.isdir(path):
            return False
        if path[-1] == "/":
            path = path[:-1]

        name = os.path.split(path)[1]
        if name in self.logdirs:
            return False

        dst = os.path.join(self.tmpdir.name, name)
        os.symlink(path, dst)

        self.logdirs[name] = TBLogDir(name, path, dst)

    def remove_logdir(self, name):
        if name not in self.logdirs:
            return False

        logdir = self.logdirs[name]
        os.remove(logdir.symlink)
        del self.logdirs[name]

        self.restart()

        return True

    def restart(self):
        pass

    def stop(self):
        pass

    def __call__(self, environ, start_response):
        return self.app(environ, start_response)

class TensorBoardManager(object):
    def __init__(self, initial_port=20000):
        self._instances = {}
        self.start_instance('font-roboto')

    def start_instance(self, name):
        self._instances[name] = TensorBoardInstance(name)

    def stop_instance(self, name):
        if name not in self._instances:
            return False
        
        stopped = self._instances[name].stop()
        if stopped:
            del self._instances[name]

        return stopped

    def restart_instance(self, name):
        if name not in self._instances:
            return False

        return self._instances[name].restart()

    def add_logdir(self, instance, path):
        if instance not in self._instances:
            return False

        return self._instances[instance].add_logdir(path)

    def __call__(self, environ, start_response):
        path = environ.get('PATH_INFO', '')
        path = path[1:].split('/')

        if len(path) < 2:
            return NotFound().get_response(environ)(environ, start_response)

        token, target = path[:2]
        tb_path = "/".join(path[2:])

        if token == 'font-roboto':
            environ['PATH_INFO'] = os.path.join('font-roboto', target)
            return self._instances['font-roboto'](environ, start_response) 

        if target not in self._instances:
            return NotFound().get_response(environ)(environ, start_response)

        environ['PATH_INFO'] = tb_path
        return self._instances[target](environ, start_response)


if __name__ == "__main__":
    mgr = TensorBoardManager()
    mgr.start_instance("test")
    mgr.add_logdir("test", ".")

    import werkzeug.serving
    werkzeug.serving.run_simple('127.0.0.1', 31337, mgr)
