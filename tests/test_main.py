from main import Main  # type: ignore
import datetime as dt
import unittest


class TestGameSaveManager(unittest.TestCase):
    def test_readable_time_since(self):
        """
        readable_time_since
        """
        main = Main()
        checked_date = dt.datetime.strptime("2021/01/01 01:00:00", "%Y/%m/%d %H:%M:%S")
        dates = {
            "2019/01/01 01:00:00": "2.0 years ago",
            "2020/01/01 01:00:00": "1.0 year ago",
            "2020/11/30 01:00:00": "1.1 months ago",
            "2020/12/28 01:00:00": "4.0 days ago",
            "2020/12/31 01:00:00": "1.0 day ago",
            "2021/01/01 00:00:00": "1.0 hour ago",
            "2020/12/31 12:00:00": "13.0 hours ago",
            "2021/01/01 00:59:00": "1.0 minute ago",
            "2021/01/01 00:59:55": "5.0 seconds ago",
        }
        for date, answer in dates.items():
            self.assertIn(main.readable_time_since(date, checked_date), answer)
