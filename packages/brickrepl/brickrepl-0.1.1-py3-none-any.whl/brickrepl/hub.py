from .repl import RemoteREPL

class InventorHub:
    def __init__(self, mac):
        self.repl = RemoteREPL(mac)
        # preload ports
        self.repl.run("from hub import port")

    def pwm(self, port_letter, power):
        self.repl.run("port.{0}.pwm({1})".format(port_letter, power))

    def stop(self, port_letter):
        self.pwm(port_letter, 0)

    def exec(self, code):
        return self.repl.run(code)
