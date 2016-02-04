import os
import unittest

from PyHardLinkBackup.phlb.pathlib2 import Path2, PosixPath2, WindowsPath2


class TestPath2(unittest.TestCase):
    def test_callable(self):
        self.assertTrue(callable(Path2(".").makedirs))


@unittest.skipIf(os.name != 'nt', 'test requires a Windows-compatible system')
class TestWindowsPath2(unittest.TestCase):
    def test_instances(self):
        self.assertIsInstance(Path2(), WindowsPath2)
        self.assertIsInstance(Path2("."), WindowsPath2)
        self.assertIsInstance(Path2(".").resolve(), WindowsPath2)
        self.assertIsInstance(Path2.home(), WindowsPath2)

    def test_callable(self):
        self.assertTrue(callable(WindowsPath2(".").link))

    def test_extended_path_hack(self):
        abs_path = Path2("c:/foo/bar/")
        self.assertEqual(str(abs_path), "\\\\?\\c:\\foo\\bar")

        rel_path = Path2("../foo/bar/")
        self.assertEqual(str(rel_path), "..\\foo\\bar")

        with self.assertRaises(FileNotFoundError) as err:
            rel_path.resolve()
        self.assertEqual(err.exception.filename, "..\\foo\\bar")
        self.assertEqual(err.exception.winerror, 3) # Win32 exception code

        with self.assertRaises(FileNotFoundError) as err:
            abs_path.resolve()
        self.assertEqual(err.exception.filename, "\\\\?\\c:\\foo\\bar")
        self.assertEqual(err.exception.winerror, 3) # Win32 exception code

    def test_home(self):
        self.assertEqual(
            Path2("~/foo").expanduser().path,
            "\\\\?\\%s" % os.path.expanduser("~\\foo")
        )

        existing_path = Path2("~").expanduser()
        ref_path = os.path.expanduser("~")
        self.assertEqual(str(existing_path), "\\\\?\\%s" % ref_path)
        self.assertTrue(existing_path.is_dir())
        self.assertTrue(existing_path.exists())

        self.assertEqual(str(existing_path), str(existing_path.resolve()))



@unittest.skipIf(os.name == 'nt', 'test requires a POSIX-compatible system')
class TestPosixPath2(unittest.TestCase):
    def test(self):
        self.assertEqual(PosixPath2("foo/bar").path, "foo/bar")

    def test_instances(self):
        self.assertIsInstance(Path2(), PosixPath2)
        self.assertIsInstance(Path2("."), PosixPath2)
        self.assertIsInstance(Path2(".").resolve(), PosixPath2)
        self.assertIsInstance(Path2.home(), PosixPath2)

    def test_callable(self):
        self.assertTrue(callable(PosixPath2(".").utime))

    def test_home(self):
        self.assertEqual(
            str(Path2("~").expanduser()),
            os.path.expanduser("~")
        )
        self.assertEqual(
            Path2("~/foo").expanduser().path,
            os.path.expanduser("~/foo")
        )
