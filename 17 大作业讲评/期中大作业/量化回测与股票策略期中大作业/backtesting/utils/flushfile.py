import sys


class flushfile(object):

    def __init__(self, f):
        self.f = f

    def write(self, x):
        self.f.write(x)
        self.f.flush()

    def flush(self):
        self.f.flush()

if sys.platform == 'win32':
    sys.stdout = flushfile(sys.stdout)
    sys.stderr = flushfile(sys.stderr)


class StdOutDevNull(object):

    def __init__(self):
        self.stdout = sys.stdout
        sys.stdout = self

    def write(self, x):
        pass

    def flush(self):
        pass

    def stop(self):
        sys.stdout = self.stdout
