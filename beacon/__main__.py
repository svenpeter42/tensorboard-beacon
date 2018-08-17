import binascii
import argparse
import sys
import os
import cmd
import string
import socket
import logging
import glob
import readline

from .server import Server
from .tbmanager import TensorBoardManager


def generate_token():
    return binascii.hexlify(os.urandom(24)).decode('ascii')


def parse_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--token", type=str, default=None)
    parser.add_argument("--host", type=str, default=None)
    parser.add_argument("--port", type=int, default=6006)

    parser.add_argument("--ssl-certbot", type=str, default=None)
    parser.add_argument('--ssl-cert', type=str, default=None)
    parser.add_argument('--ssl-key', type=str, default=None)

    args = parser.parse_args()

    if args.ssl_certbot and (args.ssl_cert or args.ssl_key):
        parser.print_usage(file=sys.stderr)
        sys.stderr.write(
            "error: argument --ssl-certbot not allowed with --ssl-cert/--ssl-key\n")
        sys.exit(1)

    if (args.ssl_cert and not args.ssl_key) or (args.ssl_key and not args.ssl_cert):
        parser.print_usage(file=sys.stderr)
        sys.stderr.write("error: need both --ssl-cert and --ssl-key\n")
        sys.exit(1)

    return args


class BeaconCMD(cmd.Cmd):
    prompt = '(tensorboard-beacon) '

    def __init__(self, mgr):
        readline.set_completer_delims(' \t\n')
        self.mgr = mgr
        super(BeaconCMD, self).__init__()

    def _filter(self, ch):
        return ''.join(ch for ch in ch if ch.isalnum() or ch in ['-'])

    def _complete_instance_name(self, text):
        suggestions = []
        for name in self.mgr.get_list().keys():
            if name.startswith(text):
                suggestions.append(name)
        return suggestions

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
        name = self._filter(line)
        self.mgr.start_instance(name)
        print(f"Started {name}")

    def do_stop(self, line):
        name = self._filter(line)
        self.mgr.stop_instance(name)
        print(f"Stopped {name}")

    def complete_stop(self, text, line, begidx, endidx):
        return self._complete_instance_name(text)

    def do_add(self, line):
        line = line.split(' ')
        if len(line) != 2:
            print("Syntax: add [instance name] [base folder])")
            return

        instance, path = line
        self.mgr.add_logdir(instance, path)
        print(f"Added {path} to {instance}.")

    def complete_add(self, text, line, begidx, endidx):
        splitline = line.split(' ')
        if len(splitline) <= 2:
            return self._complete_instance_name(text)

        info = self.mgr.get_list()
        instance_name = splitline[1]
        if instance_name not in info.keys():
            return []

        return glob.glob(f'{text}*')

    def do_remove(self, line):
        line = line.split(' ')
        if len(line) != 2:
            print("Syntax: remove [instance name] [name])")
            return

        instance, name = line
        self.mgr.remove_logdir(instance, name)
        print("Done.")

    def complete_remove(self, text, line, begidx, endidx):
        splitline = line.split(' ')
        if len(splitline) <= 2:
            return self._complete_instance_name(text)

        info = self.mgr.get_list()
        instance_name = splitline[1]
        if instance_name not in info.keys():
            return []

        suggestions = []
        info = info[instance_name]
        for name in info.keys():
            if name.startswith(text):
                suggestions.append(name)
        return suggestions

    def do_q(self, line):
        return True

    def do_exit(self, line):
        return True

    def do_quit(self, line):
        return True

    def do_EOF(self, line):
        return True

    def cmdloop(self, intro=None):
        if intro:
            print(intro)
        elif self.intro:
            print(self.intro)

        done = False
        while not done:
            try:
                super(BeaconCMD, self).cmdloop(intro='')
                done = True
            except KeyboardInterrupt:
                self.handle_ctrl_c()

    def handle_ctrl_c(self):
        print("Please use CTRL+D, exit, quit or q to quit.")


def main():
    args = parse_args()

    if not args.token:
        args.token = generate_token()

    # lol, tensorboard
    sys.argv = ['tensorboard']

    mgr = TensorBoardManager()
    mgr.token = args.token

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    log = logging.getLogger('tensorboard')
    log.setLevel(logging.ERROR)
    log = logging.getLogger('tensorboard-beacon')
    log.setLevel(logging.ERROR)

    server = Server(mgr)

    if args.ssl_certbot:
        basedir = f"/etc/letsencrypt/live/{args.ssl_certbot}/"
        server.add_ssl_cert(basedir + "fullchain.pem", basedir + "privkey.pem")
    elif args.ssl_cert and args.ssl_key:
        server.add_ssl_cert(args.ssl_cert, args.ssl_key)

    if args.host:
        server.start(args.host, args.port)
        hostname = args.host
    else:
        # https://github.com/tensorflow/tensorboard/blob/d586c7454fb1bf0bcf2a6866e09d6f6a9774f666/tensorboard/program.py#L248
        try:
            # First try passing in a blank host (meaning all interfaces). This,
            # unfortunately, defaults to IPv4 even if no IPv4 interface is available
            # (yielding a socket.error).
            server.start('', args.port)
        except socket.error:
            # If a blank host didn't work, we explicitly request IPv6 interfaces.
            server.start('::', args.port)
        hostname = socket.getfqdn()

    if server.ssl:
        proto = 'https'
    else:
        proto = 'http'

    c = BeaconCMD(mgr)
    c.cmdloop(f"Serving on {proto}://{hostname}:{args.port}/{args.token}")

    server.stop()


if __name__ == "__main__":
    main()
