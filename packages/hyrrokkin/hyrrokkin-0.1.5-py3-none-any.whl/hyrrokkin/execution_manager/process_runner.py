#   Narvi - a simple python web application server
#
#   Copyright (C) 2022-2025 Visual Topology Ltd
#
#   Licensed under the Open Software License version 3.0

import subprocess
import os

import threading


class ProcessRunner(threading.Thread):

    def __init__(self, args, exit_callback=None, cwd=None):
        super().__init__()
        self.return_code = None
        if cwd is None:
            cwd = os.getcwd()
        self.sub = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                    cwd=cwd, text=True)
        self.exit_callback = exit_callback
        self.output_callback = None

    def set_output_callback(self, output_callback):
        self.output_callback = output_callback

    def get_pid(self):
        return self.sub.pid

    def run(self):

        while self.return_code is None:
            self.handle_output(self.sub.stdout.readline())
            self.return_code = self.sub.poll()

        self.handle_output(self.sub.stdout.read())

        if self.exit_callback:
            self.exit_callback()

        self.sub.stdin.close()
        self.sub.stdout.close()

    def send_input(self, input):
        self.sub.stdin.write(input)

    def close_input(self):
        self.sub.stdin.close()

    def handle_output(self, output):
        if output:
            if self.output_callback:
                outputs = output.split("\n")
                for output in outputs:
                    output = output.rstrip()
                    if output:
                        self.output_callback(output)

    def stop(self, hard=False):
        if hard:
            self.sub.kill()
        else:
            self.sub.terminate()

    def get_return_code(self):
        return self.return_code

    def join(self):
        pass
