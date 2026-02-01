import unittest

from bdpan.client import BaiduPanClient, BaiduPanConfig


class TestPaths(unittest.TestCase):
    def test_normalize_remote_path_relative(self):
        client = BaiduPanClient(BaiduPanConfig(cookies={"BDUSS": "x"}, remote_root="/apps/bdpan"))
        self.assertEqual(client.normalize_remote_path("abc/def"), "/apps/bdpan/abc/def")

    def test_normalize_remote_path_absolute(self):
        client = BaiduPanClient(BaiduPanConfig(cookies={"BDUSS": "x"}, remote_root="/apps/bdpan"))
        self.assertEqual(client.normalize_remote_path("/apps/bdpan/abc"), "/apps/bdpan/abc")
