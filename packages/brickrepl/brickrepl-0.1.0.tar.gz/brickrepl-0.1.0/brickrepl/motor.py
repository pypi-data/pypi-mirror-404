class Motor:
    def __init__(self, hub, port):
        self.hub = hub
        self.port = port

    def pwm(self, power):
        self.hub.pwm(self.port, power)

    def stop(self):
        self.hub.stop(self.port)
