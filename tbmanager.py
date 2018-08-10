import os
import sys
import threading
import tempfile
from collections import namedtuple


from tensorboard.backend import application
from tensorboard.default import get_plugins

from werkzeug.exceptions import NotFound

TBLogDir = namedtuple('TBLogDir', ['name', 'path', 'symlink'])


def my_start_reloading_multiplexer(multiplexer, path_to_run, load_interval):
    """Starts a thread to automatically reload the given multiplexer.
    If `load_interval` is positive, the thread will reload the multiplexer
    by calling `ReloadMultiplexer` every `load_interval` seconds, starting
    immediately. Otherwise, reloads the multiplexer once and never again.
    Args:
      multiplexer: The `EventMultiplexer` to add runs to and reload.
      path_to_run: A dict mapping from paths to run names, where `None` as the run
        name is interpreted as a run name equal to the path.
      load_interval: An integer greater than or equal to 0. If positive, how many
        seconds to wait after one load before starting the next load. Otherwise,
        reloads the multiplexer once and never again (no continuous reloading).
    Returns:
      A started `threading.Thread` that reloads the multiplexer.
    Raises:
      ValueError: If `load_interval` is negative.
    """
    if load_interval < 0:
        raise ValueError('load_interval is negative: %d' % load_interval)

    # We don't call multiplexer.Reload() here because that would make
    # AddRunsFromDirectory block until the runs have all loaded.
    def _reload(e):
        while not e.isSet():
            application.reload_multiplexer(multiplexer, path_to_run)
            if load_interval == 0:
                # Only load the multiplexer once. Do not continuously reload.
                break
            e.wait(load_interval)

    e = threading.Event()
    thread = threading.Thread(target=_reload, args=(e,), name='Reloader')
    thread.daemon = True
    thread.stop_event = e
    thread.start()
    return thread


def MyTensorBoardWSGIApp(logdir, plugins, multiplexer, reload_interval,
                         path_prefix=''):
    path_to_run = application.parse_event_files_spec(logdir)
    if reload_interval >= 0:
        # We either reload the multiplexer once when TensorBoard starts up, or we
        # continuously reload the multiplexer.
        thread = my_start_reloading_multiplexer(
            multiplexer, path_to_run, reload_interval)
    else:
        thread = None
    app = application.TensorBoardWSGI(plugins, path_prefix)
    app.multiplexer_thread = thread
    return app


# less work than essentially copying standard_tensorboard_wsgi in this file...
application.TensorBoardWSGIApp = MyTensorBoardWSGIApp


class TensorBoardInstance(object):
    def __init__(self, name):
        self.name = name
        self.tmpdir = tempfile.TemporaryDirectory()
        self.logdirs = {}
        self.app = None
        self.start()

    def _name_exists(self, name):
        for i in self.logdirs:
            if i.name == name:
                return True
        return False

    def add_logdir(self, path):
        if not os.path.isdir(path):
            return False
        path = os.path.abspath(path)
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

    def start(self):
        self.app = application.standard_tensorboard_wsgi(
            self.tmpdir.name, True, 3000, get_plugins())
        return True

    def restart(self):
        self.stop()
        return self.start()

    def stop(self):
        if self.app.multiplexer_thread:
            self.app.multiplexer_thread.stop_event.set()
            self.app.multiplexer_thread.join()
        self.app = None
        return True

    def get_list(self):
        out = {}
        for name, logdir in self.logdirs.items():
            out[name] = logdir.path
        return out

    def __call__(self, environ, start_response):
        if not self.app:
            NotFound().get_response(environ)(environ, start_response)
        return self.app(environ, start_response)


class TensorBoardManager(object):
    def __init__(self):
        self.token = 'dummy'
        self._instances = {}
        self.start_instance('font-roboto')

    def start_instance(self, name):
        if name in self._instances:
            return False
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
        if instance == 'font-roboto':
            return False

        return self._instances[instance].add_logdir(path)

    def remove_logdir(self, instance, name):
        if instance not in self._instances:
            return False
        if instance == 'font-roboto':
            return False

        return self._instances[instance].remove_logdir(name)

    def get_list(self):
        out = {}
        for name, instance in self._instances.items():
            if name == 'font-roboto':
                continue
            out[name] = instance.get_list()
        return out

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

        if token != self.token:
            return NotFound().get_response(environ)(environ, start_response)
        if target not in self._instances:
            return NotFound().get_response(environ)(environ, start_response)

        environ['PATH_INFO'] = tb_path
        return self._instances[target](environ, start_response)


if __name__ == "__main__":
    mgr = TensorBoardManager()
    mgr.start_instance("test")
    mgr.add_logdir("test", "test")

    print(mgr.get_list())
    #import werkzeug.serving
    #werkzeug.serving.run_simple('127.0.0.1', 31337, mgr)
