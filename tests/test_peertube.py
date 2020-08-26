import unittest

from plugins import json_reader


class TestPeerTube(unittest.TestCase):

    def test_peertube_url(self):
        test_url = 'https://peertube.live/videos/watch/4de251dd-f919-41c3-81a5-d5767904f6c7'
        embed_url ='https://peertube.live/videos/embed/4de251dd-f919-41c3-81a5-d5767904f6c7'
        self.assertEqual(json_reader._get_media_url(test_url, media_type='peertube'), embed_url)

        # URL is unchanged when media_type isn't specified
        self.assertEqual(json_reader._get_media_url(test_url), test_url)


if __name__ == '__main__':
    unittest.main()
