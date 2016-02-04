import os
import unittest

from PyHardLinkBackup.phlb.pathlib2 import Path2


@unittest.skipIf(os.name != 'nt', 'test requires a Windows-compatible system')
class TestWindowsPath2(unittest.TestCase):
    def test_extended_path_hack(self):
        abs_path = Path2("c:/foo/bar/")
        self.assertEqual(str(abs_path), "\\\\?\\c:\\foo\\bar")

        rel_path = Path2("../foo/bar/")
        self.assertEqual(str(rel_path), "..\\foo\\bar")

