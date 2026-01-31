from .rfcomm import connect_rfcomm
from time import sleep_ms

class RemoteREPL:
    def __init__(self, mac, channel=1, debug=False):
        self.debug = debug
        self.sock = connect_rfcomm(mac, channel)
        self._enter_raw_repl()

    def _enter_raw_repl(self):
        # Send ctrl-C twice to stop any running program
        self.sock.send(b'\x03')
        sleep_ms(50)
        self.sock.send(b'\x03')
        sleep_ms(50)
        # Enter raw REPL
        self.sock.send(b'\x01')
        sleep_ms(50)
        self.sock.recv(1024)

    def run(self, code):
        if self.debug:
            print(">>>", code)
        self.sock.send(bytes(code, "utf-8")+b'\x04')
        sleep_ms(10)
        result = b""
        while True:
            chunk = self.sock.recv(1024)
            result += chunk
            if b'\x04' in chunk:
                break
        return result.decode(errors="ignore")

    def close(self):
        self.sock.send(b'\x02')  # exit raw REPL
