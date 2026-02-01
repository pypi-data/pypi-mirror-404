#!/usr/bin/env python
"""Test suite for croniter_rs - adapted from original croniter tests"""

import unittest
from datetime import datetime, timedelta

# Import from our Rust library
from croniter_rs import (
    croniter,
    CroniterBadCronError,
    CroniterBadDateError,
    datetime_to_timestamp,
)


class CroniterTest(unittest.TestCase):
    def test_second_sec(self):
        base = datetime(2012, 4, 6, 13, 26, 10)
        itr = croniter("* * * * * 15,25", base)
        n = itr.get_next(datetime)
        self.assertEqual(15, n.second)
        n = itr.get_next(datetime)
        self.assertEqual(25, n.second)
        n = itr.get_next(datetime)
        self.assertEqual(15, n.second)
        self.assertEqual(27, n.minute)

    def test_second(self):
        base = datetime(2012, 4, 6, 13, 26, 10)
        itr = croniter("*/1 * * * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(base.year, n1.year)
        self.assertEqual(base.month, n1.month)
        self.assertEqual(base.day, n1.day)
        self.assertEqual(base.hour, n1.hour)
        self.assertEqual(base.minute, n1.minute)
        self.assertEqual(base.second + 1, n1.second)

    def test_minute(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("*/1 * * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(base.year, n1.year)
        self.assertEqual(base.month, n1.month)
        self.assertEqual(base.day, n1.day)
        self.assertEqual(base.hour, n1.hour)
        self.assertEqual(base.minute + 1, n1.minute)

    def test_hour(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 */1 * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(base.year, n1.year)
        self.assertEqual(base.month, n1.month)
        self.assertEqual(base.day, n1.day)
        self.assertEqual(base.hour + 1, n1.hour)
        self.assertEqual(0, n1.minute)

    def test_day(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 */1 * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(base.year, n1.year)
        self.assertEqual(base.month, n1.month)
        self.assertEqual(base.day + 1, n1.day)
        self.assertEqual(0, n1.hour)
        self.assertEqual(0, n1.minute)

    def test_month(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 1 */1 *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(base.year, n1.year)
        self.assertEqual(base.month + 1, n1.month)
        self.assertEqual(1, n1.day)
        self.assertEqual(0, n1.hour)
        self.assertEqual(0, n1.minute)

    def test_weekday(self):
        base = datetime(2010, 1, 25, 4, 46)  # Monday
        itr = croniter("0 0 * * 0", base)  # Sunday
        n1 = itr.get_next(datetime)
        self.assertEqual(31, n1.day)  # Next Sunday is Jan 31
        self.assertEqual(0, n1.hour)
        self.assertEqual(0, n1.minute)

    def test_range(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * 1-5", base)  # Mon-Fri
        n1 = itr.get_next(datetime)
        self.assertEqual(26, n1.day)  # Tuesday

    def test_step(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("*/15 * * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(0, n1.minute)
        self.assertEqual(5, n1.hour)

    def test_get_prev(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * *", base)
        n1 = itr.get_prev(datetime)
        self.assertEqual(25, n1.day)
        self.assertEqual(0, n1.hour)
        self.assertEqual(0, n1.minute)

    def test_get_current(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * *", base)
        n1 = itr.get_next(datetime)
        n2 = itr.get_current(datetime)
        self.assertEqual(n1, n2)

    def test_set_current(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * *", base)
        itr.get_next(datetime)
        new_time = datetime(2015, 6, 15, 12, 30)
        itr.set_current(new_time)
        n = itr.get_current(datetime)
        self.assertEqual(new_time.year, n.year)
        self.assertEqual(new_time.month, n.month)
        self.assertEqual(new_time.day, n.day)

    def test_is_valid(self):
        self.assertTrue(croniter.is_valid("0 0 * * *"))
        self.assertTrue(croniter.is_valid("*/5 * * * *"))
        self.assertFalse(croniter.is_valid("invalid"))
        self.assertFalse(croniter.is_valid("* * * *"))  # Only 4 fields

    def test_match(self):
        dt = datetime(2010, 1, 25, 0, 0)
        self.assertTrue(croniter.match("0 0 25 1 *", dt))
        self.assertFalse(croniter.match("0 0 26 1 *", dt))

    def test_iterator(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("*/5 * * * *", base)
        count = 0
        for dt in itr:
            count += 1
            if count >= 5:
                break
        self.assertEqual(5, count)

    def test_iterator_prev(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("*/5 * * * *", base, is_prev=True)
        count = 0
        for dt in itr:
            count += 1
            if count >= 5:
                break
        self.assertEqual(5, count)

    def test_expanded(self):
        itr = croniter("*/15 * * * *", datetime(2010, 1, 1))
        expanded = itr.expanded
        self.assertIsInstance(expanded, list)
        self.assertEqual(len(expanded), 6)  # 6 fields (includes seconds)
        # Minutes should be [0, 15, 30, 45]
        self.assertEqual(expanded[0], [0, 15, 30, 45])

    def test_nth_weekday_of_month(self):
        # First Monday of January 2010
        day = croniter._get_nth_weekday_of_month(2010, 1, 0, 1)  # Monday=0
        self.assertEqual(day, 4)  # Jan 4, 2010 was first Monday

    def test_leap_year(self):
        base = datetime(2012, 2, 28, 23, 59)
        itr = croniter("0 0 * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(29, n1.day)  # Feb 29 in leap year
        n2 = itr.get_next(datetime)
        self.assertEqual(1, n2.day)
        self.assertEqual(3, n2.month)

    def test_day_of_week_names(self):
        base = datetime(2010, 1, 25, 0, 0)  # Monday
        itr = croniter("0 0 * * sun", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(31, n1.day)  # Next Sunday

    def test_month_names(self):
        base = datetime(2010, 1, 1, 0, 0)
        itr = croniter("0 0 1 feb *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(2, n1.month)

    def test_bad_cron_error(self):
        with self.assertRaises(CroniterBadCronError):
            croniter("invalid cron", datetime.now())

    def test_float_return_type(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * *", base, ret_type=float)
        n1 = itr.get_next()
        self.assertIsInstance(n1, float)

    def test_datetime_return_type(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("0 0 * * *", base)
        n1 = itr.get_next(datetime)
        self.assertIsInstance(n1, datetime)

    def test_every_5_minutes(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("*/5 * * * *", base)
        results = []
        for _ in range(5):
            results.append(itr.get_next(datetime))
        self.assertEqual(results[0].minute, 50)
        self.assertEqual(results[1].minute, 55)
        self.assertEqual(results[2].minute, 0)
        self.assertEqual(results[3].minute, 5)
        self.assertEqual(results[4].minute, 10)

    def test_specific_minutes(self):
        base = datetime(2010, 1, 25, 4, 46)
        itr = croniter("15,30,45 * * * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(5, n1.hour)
        self.assertEqual(15, n1.minute)

    def test_day_or_weekday(self):
        # Test day_or=True (default): match if day OR weekday matches
        base = datetime(2010, 1, 1, 0, 0)
        itr = croniter("0 0 15 * 0", base, day_or=True)  # 15th or Sunday
        n1 = itr.get_next(datetime)
        # Should match Jan 3 (Sunday) before Jan 15
        self.assertEqual(3, n1.day)

    def test_last_day_of_month(self):
        base = datetime(2010, 1, 25, 0, 0)
        itr = croniter("0 0 L * *", base)
        n1 = itr.get_next(datetime)
        self.assertEqual(31, n1.day)  # Last day of January

    def test_timestamp_input(self):
        ts = 1264406760.0  # 2010-01-25 04:46:00 UTC
        itr = croniter("0 0 * * *", ts)
        n1 = itr.get_next(float)
        self.assertIsInstance(n1, float)


if __name__ == "__main__":
    unittest.main()
