import numpy as np


class Result(object):
    """
    wraps a scope result with some meta data
    """

    def __init__(self, name, value):
        self.name = name
        self.value = value
        self._iter_body = ["raw"]
        self._iter_count = 0

    def __getattr__(self, name):
        if name == "tarray":
            start_hz = self.value.value.start_hz
            bucket_width_hz = self.value.value.bucket_width_hz
            return np.arange(len(self.value.value.data)) * bucket_width_hz + start_hz
        return getattr(self.value, name)

    def __iter__(self):
        self._iter_count = 0
        return self

    def __next__(self):
        if self._iter_count >= len(self._iter_body):
            raise StopIteration
        self._iter_count += 1
        return self._iter_body[self._iter_count - 1]

    def __getitem__(self, key):
        a = np.array(self.value.value.data)
        return a
        # return np.array(np.arange(len(self.value.value.data))*0.5)
