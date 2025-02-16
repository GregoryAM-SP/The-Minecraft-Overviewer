import unittest
from unittest.mock import patch
import overviewer

class OverviewerTest(unittest.TestCase):

    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_resolve_local_only(self, mock_exists, *args):
        mock_exists.side_effect = lambda path: {
            "foo": True,
            "/home/user/.minecraft/saves/foo": False
        }[path]

        self.assertEqual(overviewer.resolve_world_path("foo"), "foo")


    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_resolve_local_and_saves(self, mock_exists, *args):
        """If the world directory exists in the current directory, that should be preferred"""
        mock_exists.side_effect = lambda path: {
            "foo": True,
            "/home/user/.minecraft/saves/foo": True
        }[path]

        self.assertEqual(overviewer.resolve_world_path("foo"), "foo")


    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_resolve_saves_only(self, mock_exists, *args):
        mock_exists.side_effect = lambda path: {
            "foo": False,
            "/home/user/.minecraft/saves/foo": True
        }[path]

        self.assertEqual(overviewer.resolve_world_path("foo"), "/home/user/.minecraft/saves/foo")

    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_resolve_local_only_with_sep(self, mock_exists, *args):
        mock_exists.side_effect = lambda path: {
            "foo/bar": True,
            "/home/user/.minecraft/saves/foo/bar": False
        }[path]

        self.assertEqual(overviewer.resolve_world_path("foo/bar"), "foo/bar")

    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_fail_resolve_no_local(self, mock_exists, *args):
        mock_exists.side_effect = lambda path: {
            "foo/bar": False,
            "/home/user/.minecraft/saves/foo/bar": False
        }[path]

        self.assertEqual(overviewer.resolve_world_path("foo/bar"), None)


    @patch('os.path.sep', new='/')
    @patch('os.path.expanduser', return_value='/home/user')
    @patch('platform.system', return_value='Linux')
    @patch('os.path.exists')
    def test_fail_resolve(self, mock_exists, *args):
        mock_exists.side_effect = lambda path: {
            "missing": False,
            "/home/user/.minecraft/saves/missing": False
        }[path]

        self.assertEqual(overviewer.resolve_world_path("missing"), None)