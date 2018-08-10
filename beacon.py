import binascii
import argparse
import sys
import os
import cmd
import string
import socket
import logging

from server import Server
from tbmanager import TensorBoardManager


def generate_token():
    return binascii.hexlify(os.urandom(24)).decode('ascii')


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--port", type=int, default=6006)

    return parser.parse_args()


class MyCMD(cmd.Cmd):
    def __init__(self, mgr):
        self.mgr = mgr
        super(MyCMD, self).__init__()

    def do_set_token(self, line):
        token = ''.join(ch for ch in line if ch.isalnum())
        self.mgr.token = token
        print(f"Set token to {token}")

    def do_token(self, line):
        print(f"Current token: {self.mgr.token}")

    def do_list(self, line):
        info = self.mgr.get_list()
        for i_name, i_instance in info.items():
            print(f"{i_name}")
            for j_name, j_path in i_instance.items():
                print(f"    {j_name}  ->  {j_path}")

    def do_start(self, line):
        name = ''.join(ch for ch in line if ch.isalnum())
        self.mgr.start_instance(name)
        print(f"Started {name}")

    def do_stop(self, line):
        name = ''.join(ch for ch in line if ch.isalnum())
        self.mgr.stop_instance(name)
        print(f"Stopped {name}")

    def do_add(self, line):
        line = line.split(' ')
        if len(line) != 2:
            print("Syntax: add [instance name] [base folder])")
            return

        instance, path = line
        self.mgr.add_logdir(instance, path)
        print("Done.")

    def do_remove(self, line):
        line = line.split(' ')
        if len(line) != 2:
            print("Syntax: remove [instance name] [name])")
            return

        instance, name = line
        self.mgr.remove_logdir(instance, name)
        print("Done.")

    def do_q(self, line):
        return True

    def do_exit(self, line):
        return True

    def do_quit(self, line):
        return True

    def do_EOF(self, line):
        return True


def main():
    args = parse_args()

    if not args.token:
        args.token = generate_token()

    # lol, tensorboard
    sys.argv = ['tensorboard']

    mgr = TensorBoardManager()
    mgr.token = args.token

    mgr.start_instance("test")
    mgr.add_logdir("test", "test")

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log = logging.getLogger('tensorboard')
    log.setLevel(logging.ERROR)

    if args.host:
        server = Server(args.host, args.port, mgr)
        hostname = args.host
    else:
        # https://github.com/tensorflow/tensorboard/blob/d586c7454fb1bf0bcf2a6866e09d6f6a9774f666/tensorboard/program.py#L248
        try:
            # First try passing in a blank host (meaning all interfaces). This,
            # unfortunately, defaults to IPv4 even if no IPv4 interface is available
            # (yielding a socket.error).
            server = Server('', args.port, mgr)
        except socket.error:
            # If a blank host didn't work, we explicitly request IPv6 interfaces.
            server = Server('::', args.port, mgr)
        hostname = socket.gethostname()

    print(f"Serving on http://{hostname}:{args.port}/{args.token}")

    c = MyCMD(mgr)
    c.cmdloop()

    server.stop()


if __name__ == "__main__":
    main()
