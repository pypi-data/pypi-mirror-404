use chrono::{Datelike, NaiveDate, NaiveDateTime, NaiveTime, Timelike, Weekday};

use crate::parser::CronExpr;

/// Represents a parsed and ready-to-use cron schedule
#[derive(Debug, Clone)]
pub struct CronSchedule {
    expr: CronExpr,
    day_or: bool,
    implement_cron_bug: bool,
}

impl CronSchedule {
    /// Parse a cron expression and create a schedule
    pub fn parse(
        expr: &str,
        hash_id: Option<&str>,
        second_at_beginning: bool,
        day_or: bool,
        implement_cron_bug: bool,
    ) -> Result<Self, String> {
        let parsed = CronExpr::parse(expr, hash_id, second_at_beginning)?;
        Ok(CronSchedule {
            expr: parsed,
            day_or,
            implement_cron_bug,
        })
    }

    /// Get the next matching datetime after the given datetime
    pub fn next_from(&self, dt: NaiveDateTime) -> Option<NaiveDateTime> {
        // Start from the next second
        let mut current = dt + chrono::Duration::seconds(1);

        // Limit search to prevent infinite loops (50 years)
        let max_date = dt + chrono::Duration::days(50 * 365);

        while current < max_date {
            if let Some(next) = self.find_next_match(current) {
                return Some(next);
            }
            // Move to next month if no match found in current search
            current = self.advance_month(current)?;
        }

        None
    }

    /// Get the previous matching datetime before the given datetime
    pub fn prev_from(&self, dt: NaiveDateTime) -> Option<NaiveDateTime> {
        // Start from the previous second
        let mut current = dt - chrono::Duration::seconds(1);

        // Limit search to prevent infinite loops (50 years back)
        let min_date = dt - chrono::Duration::days(50 * 365);

        while current > min_date {
            if let Some(prev) = self.find_prev_match(current) {
                return Some(prev);
            }
            // Move to previous month if no match found
            current = self.retreat_month(current)?;
        }

        None
    }

    /// Check if a datetime matches the schedule
    pub fn matches(&self, dt: NaiveDateTime) -> bool {
        // Check seconds
        if !self.expr.seconds.contains(&(dt.second() as u32)) {
            return false;
        }

        // Check minutes
        if !self.expr.minutes.contains(&(dt.minute() as u32)) {
            return false;
        }

        // Check hours
        if !self.expr.hours.contains(&(dt.hour() as u32)) {
            return false;
        }

        // Check month
        if !self.expr.months.contains(&(dt.month() as u32)) {
            return false;
        }

        // Check day matching (day of month and/or day of week)
        self.matches_day(dt)
    }

    /// Get expanded field values for Python interface
    pub fn get_expanded(&self) -> Vec<Vec<i32>> {
        vec![
            self.expr.minutes.iter().map(|&v| v as i32).collect(),
            self.expr.hours.iter().map(|&v| v as i32).collect(),
            self.expr.days.iter().map(|&v| v as i32).collect(),
            self.expr.months.iter().map(|&v| v as i32).collect(),
            self.expr.weekdays.iter().map(|&v| v as i32).collect(),
            self.expr.seconds.iter().map(|&v| v as i32).collect(),
        ]
    }

    /// Check if the day (day-of-month and day-of-week) matches
    fn matches_day(&self, dt: NaiveDateTime) -> bool {
        let dom_matches = self.matches_day_of_month(dt);
        let dow_matches = self.matches_day_of_week(dt);

        // Check if day or weekday fields are wildcards (all values)
        let day_is_wildcard = self.expr.days.len() == 31 &&
            self.expr.days.iter().enumerate().all(|(i, &v)| v == (i + 1) as u32);
        let weekday_is_wildcard = self.expr.weekdays.len() == 7 &&
            self.expr.weekdays.iter().enumerate().all(|(i, &v)| v == i as u32);

        if self.implement_cron_bug {
            // Cron bug: use AND logic
            dom_matches && dow_matches
        } else if self.day_or {
            // Standard behavior: OR logic when both are specified
            // But if one is wildcard, only check the other
            if day_is_wildcard && !weekday_is_wildcard {
                dow_matches
            } else if weekday_is_wildcard && !day_is_wildcard {
                dom_matches
            } else if day_is_wildcard && weekday_is_wildcard {
                true
            } else {
                // Both are specified (not wildcards), use OR
                dom_matches || dow_matches
            }
        } else {
            // day_or=false: AND logic
            dom_matches && dow_matches
        }
    }

    /// Check if day of month matches
    fn matches_day_of_month(&self, dt: NaiveDateTime) -> bool {
        let day = dt.day() as u32;

        // Check for last day of month
        if self.expr.last_day {
            let last_day = last_day_of_month(dt.year(), dt.month());
            if day == last_day {
                return true;
            }
        }

        // Check regular day values
        self.expr.days.contains(&day)
    }

    /// Check if day of week matches
    fn matches_day_of_week(&self, dt: NaiveDateTime) -> bool {
        let weekday = chrono_weekday_to_cron(dt.weekday());

        // Check nth weekday constraints
        if !self.expr.nth_weekdays.is_empty() {
            let day = dt.day();
            let nth = ((day - 1) / 7 + 1) as u32;

            for &(wd, n) in &self.expr.nth_weekdays {
                if wd == weekday && n == nth {
                    return true;
                }
            }

            // If nth_weekdays are specified but none match, check if regular weekdays also specified
            if self.expr.weekdays.is_empty() ||
               (self.expr.weekdays.len() == self.expr.nth_weekdays.len()) {
                return false;
            }
        }

        self.expr.weekdays.contains(&weekday)
    }

    /// Find the next matching datetime starting from current
    fn find_next_match(&self, start: NaiveDateTime) -> Option<NaiveDateTime> {
        let mut year = start.year();
        let mut month = start.month();
        let mut day = start.day();
        let mut hour = start.hour();
        let mut minute = start.minute();
        let mut second = start.second();

        // Find next matching month
        let orig_month = month;
        month = self.find_next_in_list(&self.expr.months, month as u32)? as u32;

        if month < orig_month {
            year += 1;
            day = 1;
            hour = 0;
            minute = 0;
            second = 0;
        } else if month > orig_month {
            day = 1;
            hour = 0;
            minute = 0;
            second = 0;
        }

        // Find next matching day
        let max_iterations = 366 * 2; // Prevent infinite loops
        for _ in 0..max_iterations {
            // Validate date
            let date = NaiveDate::from_ymd_opt(year, month, day)?;
            let last_day = last_day_of_month(year, month);

            if day > last_day {
                // Move to next month
                day = 1;
                hour = 0;
                minute = 0;
                second = 0;
                month += 1;
                if month > 12 {
                    month = 1;
                    year += 1;
                }
                month = self.find_next_in_list(&self.expr.months, month as u32)? as u32;
                if month == 1 && self.expr.months[0] == 1 {
                    // Wrapped to next year
                }
                continue;
            }

            let time = NaiveTime::from_hms_opt(hour, minute, second)?;
            let dt = NaiveDateTime::new(date, time);

            // Check if this day matches
            if self.matches_day(dt) {
                // Find next matching hour
                let orig_hour = hour;
                if let Some(next_hour) = self.find_next_in_list(&self.expr.hours, hour as u32) {
                    hour = next_hour as u32;
                    if hour < orig_hour {
                        // Wrapped, move to next day
                        day += 1;
                        hour = 0;
                        minute = 0;
                        second = 0;
                        continue;
                    } else if hour > orig_hour {
                        minute = 0;
                        second = 0;
                    }
                } else {
                    day += 1;
                    hour = 0;
                    minute = 0;
                    second = 0;
                    continue;
                }

                // Find next matching minute
                let orig_minute = minute;
                if let Some(next_minute) = self.find_next_in_list(&self.expr.minutes, minute as u32) {
                    minute = next_minute as u32;
                    if minute < orig_minute {
                        // Wrapped, move to next hour
                        hour += 1;
                        minute = 0;
                        second = 0;
                        if hour > 23 {
                            day += 1;
                            hour = 0;
                        }
                        continue;
                    } else if minute > orig_minute {
                        second = 0;
                    }
                } else {
                    hour += 1;
                    minute = 0;
                    second = 0;
                    if hour > 23 {
                        day += 1;
                        hour = 0;
                    }
                    continue;
                }

                // Find next matching second
                if let Some(next_second) = self.find_next_in_list(&self.expr.seconds, second as u32) {
                    second = next_second as u32;
                    if second < start.second() && minute == start.minute() && hour == start.hour()
                        && day == start.day() && month == start.month() as u32 && year == start.year() {
                        // Wrapped on same minute, move to next minute
                        minute += 1;
                        second = 0;
                        if minute > 59 {
                            hour += 1;
                            minute = 0;
                            if hour > 23 {
                                day += 1;
                                hour = 0;
                            }
                        }
                        continue;
                    }
                } else {
                    minute += 1;
                    second = 0;
                    if minute > 59 {
                        hour += 1;
                        minute = 0;
                        if hour > 23 {
                            day += 1;
                            hour = 0;
                        }
                    }
                    continue;
                }

                // Construct and validate final datetime
                let final_date = NaiveDate::from_ymd_opt(year, month, day)?;
                let final_time = NaiveTime::from_hms_opt(hour, minute, second)?;
                let result = NaiveDateTime::new(final_date, final_time);

                // Final validation
                if self.matches(result) && result > start - chrono::Duration::seconds(1) {
                    return Some(result);
                }
            }

            // Move to next day
            day += 1;
            hour = 0;
            minute = 0;
            second = 0;
        }

        None
    }

    /// Find the previous matching datetime ending at current
    fn find_prev_match(&self, start: NaiveDateTime) -> Option<NaiveDateTime> {
        let mut year = start.year();
        let mut month = start.month();
        let mut day = start.day();
        let mut hour = start.hour();
        let mut minute = start.minute();
        let mut second = start.second();

        // Find previous matching month
        let orig_month = month;
        month = self.find_prev_in_list(&self.expr.months, month as u32)? as u32;

        if month > orig_month {
            year -= 1;
            day = last_day_of_month(year, month);
            hour = 23;
            minute = 59;
            second = 59;
        } else if month < orig_month {
            day = last_day_of_month(year, month);
            hour = 23;
            minute = 59;
            second = 59;
        }

        let max_iterations = 366 * 2;
        for _ in 0..max_iterations {
            // Validate date
            let last_day = last_day_of_month(year, month);
            if day > last_day {
                day = last_day;
            }

            if day < 1 {
                // Move to previous month
                month -= 1;
                if month < 1 {
                    month = 12;
                    year -= 1;
                }
                month = self.find_prev_in_list(&self.expr.months, month as u32)? as u32;
                day = last_day_of_month(year, month);
                hour = 23;
                minute = 59;
                second = 59;
                continue;
            }

            let date = NaiveDate::from_ymd_opt(year, month, day)?;
            let time = NaiveTime::from_hms_opt(hour, minute, second)?;
            let dt = NaiveDateTime::new(date, time);

            // Check if this day matches
            if self.matches_day(dt) {
                // Find previous matching hour
                let orig_hour = hour;
                if let Some(prev_hour) = self.find_prev_in_list(&self.expr.hours, hour as u32) {
                    hour = prev_hour as u32;
                    if hour > orig_hour {
                        // Wrapped, move to previous day
                        day -= 1;
                        hour = 23;
                        minute = 59;
                        second = 59;
                        continue;
                    } else if hour < orig_hour {
                        minute = 59;
                        second = 59;
                    }
                } else {
                    day -= 1;
                    hour = 23;
                    minute = 59;
                    second = 59;
                    continue;
                }

                // Find previous matching minute
                let orig_minute = minute;
                if let Some(prev_minute) = self.find_prev_in_list(&self.expr.minutes, minute as u32) {
                    minute = prev_minute as u32;
                    if minute > orig_minute {
                        // Wrapped, move to previous hour
                        hour = hour.saturating_sub(1);
                        if hour == 0 && orig_hour == 0 {
                            day -= 1;
                            hour = 23;
                        }
                        minute = 59;
                        second = 59;
                        continue;
                    } else if minute < orig_minute {
                        second = 59;
                    }
                } else {
                    if hour > 0 {
                        hour -= 1;
                    } else {
                        day -= 1;
                        hour = 23;
                    }
                    minute = 59;
                    second = 59;
                    continue;
                }

                // Find previous matching second
                if let Some(prev_second) = self.find_prev_in_list(&self.expr.seconds, second as u32) {
                    second = prev_second as u32;
                    if second > start.second() && minute == start.minute() && hour == start.hour()
                        && day == start.day() && month == start.month() as u32 && year == start.year() {
                        // Wrapped on same minute, move to previous minute
                        if minute > 0 {
                            minute -= 1;
                        } else {
                            if hour > 0 {
                                hour -= 1;
                            } else {
                                day -= 1;
                                hour = 23;
                            }
                            minute = 59;
                        }
                        second = 59;
                        continue;
                    }
                } else {
                    if minute > 0 {
                        minute -= 1;
                    } else {
                        if hour > 0 {
                            hour -= 1;
                        } else {
                            day -= 1;
                            hour = 23;
                        }
                        minute = 59;
                    }
                    second = 59;
                    continue;
                }

                // Construct and validate final datetime
                let final_date = NaiveDate::from_ymd_opt(year, month, day)?;
                let final_time = NaiveTime::from_hms_opt(hour, minute, second)?;
                let result = NaiveDateTime::new(final_date, final_time);

                // Final validation
                if self.matches(result) && result < start + chrono::Duration::seconds(1) {
                    return Some(result);
                }
            }

            // Move to previous day
            day -= 1;
            hour = 23;
            minute = 59;
            second = 59;
        }

        None
    }

    /// Find the next value in a sorted list >= target, wrapping if needed
    fn find_next_in_list(&self, list: &[u32], target: u32) -> Option<u32> {
        if list.is_empty() {
            return None;
        }

        // Find first value >= target
        for &val in list {
            if val >= target {
                return Some(val);
            }
        }

        // Wrap to beginning
        Some(list[0])
    }

    /// Find the previous value in a sorted list <= target, wrapping if needed
    fn find_prev_in_list(&self, list: &[u32], target: u32) -> Option<u32> {
        if list.is_empty() {
            return None;
        }

        // Find last value <= target
        let mut result = None;
        for &val in list {
            if val <= target {
                result = Some(val);
            } else {
                break;
            }
        }

        // If found, return it; otherwise wrap to end
        result.or_else(|| list.last().copied())
    }

    /// Advance to the start of the next month
    fn advance_month(&self, dt: NaiveDateTime) -> Option<NaiveDateTime> {
        let (year, month) = if dt.month() == 12 {
            (dt.year() + 1, 1)
        } else {
            (dt.year(), dt.month() + 1)
        };

        let date = NaiveDate::from_ymd_opt(year, month, 1)?;
        let time = NaiveTime::from_hms_opt(0, 0, 0)?;
        Some(NaiveDateTime::new(date, time))
    }

    /// Retreat to the end of the previous month
    fn retreat_month(&self, dt: NaiveDateTime) -> Option<NaiveDateTime> {
        let (year, month) = if dt.month() == 1 {
            (dt.year() - 1, 12)
        } else {
            (dt.year(), dt.month() - 1)
        };

        let last_day = last_day_of_month(year, month);
        let date = NaiveDate::from_ymd_opt(year, month, last_day)?;
        let time = NaiveTime::from_hms_opt(23, 59, 59)?;
        Some(NaiveDateTime::new(date, time))
    }
}

/// Convert chrono Weekday to cron weekday (0=Sunday, 6=Saturday)
fn chrono_weekday_to_cron(weekday: Weekday) -> u32 {
    match weekday {
        Weekday::Sun => 0,
        Weekday::Mon => 1,
        Weekday::Tue => 2,
        Weekday::Wed => 3,
        Weekday::Thu => 4,
        Weekday::Fri => 5,
        Weekday::Sat => 6,
    }
}

/// Get the last day of a month, handling leap years
fn last_day_of_month(year: i32, month: u32) -> u32 {
    match month {
        1 | 3 | 5 | 7 | 8 | 10 | 12 => 31,
        4 | 6 | 9 | 11 => 30,
        2 => {
            if is_leap_year(year) {
                29
            } else {
                28
            }
        }
        _ => 31, // Fallback
    }
}

/// Check if a year is a leap year
fn is_leap_year(year: i32) -> bool {
    (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_next_simple() {
        let schedule = CronSchedule::parse("0 * * * *", None, false, true, false).unwrap();
        let dt = NaiveDateTime::parse_from_str("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S").unwrap();
        let next = schedule.next_from(dt).unwrap();
        assert_eq!(next.hour(), 11);
        assert_eq!(next.minute(), 0);
    }

    #[test]
    fn test_prev_simple() {
        let schedule = CronSchedule::parse("0 * * * *", None, false, true, false).unwrap();
        let dt = NaiveDateTime::parse_from_str("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S").unwrap();
        let prev = schedule.prev_from(dt).unwrap();
        assert_eq!(prev.hour(), 10);
        assert_eq!(prev.minute(), 0);
    }

    #[test]
    fn test_matches() {
        let schedule = CronSchedule::parse("30 10 * * *", None, false, true, false).unwrap();
        let dt = NaiveDateTime::parse_from_str("2024-01-15 10:30:00", "%Y-%m-%d %H:%M:%S").unwrap();
        assert!(schedule.matches(dt));

        let dt2 = NaiveDateTime::parse_from_str("2024-01-15 10:31:00", "%Y-%m-%d %H:%M:%S").unwrap();
        assert!(!schedule.matches(dt2));
    }

    #[test]
    fn test_last_day_of_month() {
        assert_eq!(last_day_of_month(2024, 2), 29); // Leap year
        assert_eq!(last_day_of_month(2023, 2), 28); // Non-leap year
        assert_eq!(last_day_of_month(2024, 1), 31);
        assert_eq!(last_day_of_month(2024, 4), 30);
    }

    #[test]
    fn test_leap_year() {
        assert!(is_leap_year(2024));
        assert!(!is_leap_year(2023));
        assert!(is_leap_year(2000));
        assert!(!is_leap_year(1900));
    }

    #[test]
    fn test_weekday_conversion() {
        assert_eq!(chrono_weekday_to_cron(Weekday::Sun), 0);
        assert_eq!(chrono_weekday_to_cron(Weekday::Sat), 6);
    }
}
