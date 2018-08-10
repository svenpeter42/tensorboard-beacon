import binascii
import argparse
import sys
import os
import cmd
import string

from server import Server
from tbmanager import TensorBoardManager


def generate_token():
    return binascii.hexlify(os.urandom(24)).decode('ascii')


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--token", type=str, default=None)
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

    server = Server('127.0.0.1', args.port, mgr)

    print(f"Serving on localhost:{args.port}/{args.token}")

    c = MyCMD(mgr)
    c.cmdloop()

    server.stop()


if __name__ == "__main__":
    main()
