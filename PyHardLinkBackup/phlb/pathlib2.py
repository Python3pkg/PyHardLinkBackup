import os
import pathlib
import shutil


class SharedPathMethods:
    @property
    def path(self):
        # Path2().path is new in 3.4.5 and 3.5.2
        return str(self)

    def makedirs(self, *args, **kwargs):
        os.makedirs(self.path, *args, **kwargs)

    def link(self, other):
        os.link(self.path, other.path)

    def utime(self, *args, **kwargs):
        os.utime(self.path, *args, **kwargs)

    def copyfile(self, other, *args, **kwargs):
        shutil.copyfile(self.path, other.path, *args, **kwargs)

    def expanduser(self):
        return Path2(os.path.expanduser(self.path))


class WindowsPath2(SharedPathMethods, pathlib.WindowsPath):
    @property
    def extended_path(self):
        """
        Add prefix \\?\ to every absolute path, so that it's a "extended-length"
        path, that should be longer than 259 characters (called: "MAX_PATH")
        see:
        https://msdn.microsoft.com/en-us/library/aa365247.aspx#maxpath
        """
        if self.is_absolute():
            return "\\\\?\\%s" % self
        return self.path


class PosixPath2(SharedPathMethods, pathlib.PosixPath):
    @property
    def extended_path(self):
        return self.path


class Path2(pathlib.Path):
    """
    https://github.com/python/cpython/blob/master/Lib/pathlib.py
    """
    def __new__(cls, *args, **kwargs):
        if cls is Path2 or cls is pathlib.Path:
            cls = WindowsPath2 if os.name == 'nt' else PosixPath2
        self = cls._from_parts(args, init=False)
        if not self._flavour.is_supported:
            raise NotImplementedError("cannot instantiate %r on your system"
                                      % (cls.__name__,))
        self._init()
        return self

    @classmethod
    def home(cls):
        """
        Return a new path pointing to the user's home directory (as
        returned by os.path.expanduser('~'))
        """
        # Note: pathlib.Path.home() exist since in Python 3.5
        return cls(os.path.expanduser("~"))



