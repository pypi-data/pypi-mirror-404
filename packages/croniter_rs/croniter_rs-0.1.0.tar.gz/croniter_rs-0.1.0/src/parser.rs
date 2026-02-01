use std::collections::HashSet;

/// Represents a parsed cron expression
#[derive(Debug, Clone)]
pub struct CronExpr {
    pub seconds: Vec<u32>,
    pub minutes: Vec<u32>,
    pub hours: Vec<u32>,
    pub days: Vec<u32>,
    pub months: Vec<u32>,
    pub weekdays: Vec<u32>,
    pub nth_weekdays: Vec<(u32, u32)>, // (weekday, nth)
    pub last_day: bool,
    pub has_seconds: bool,
}

// Day name mappings
const DAY_NAMES: &[(&str, u32)] = &[
    ("sun", 0), ("mon", 1), ("tue", 2), ("wed", 3),
    ("thu", 4), ("fri", 5), ("sat", 6),
    ("sunday", 0), ("monday", 1), ("tuesday", 2), ("wednesday", 3),
    ("thursday", 4), ("friday", 5), ("saturday", 6),
];

// Month name mappings
const MONTH_NAMES: &[(&str, u32)] = &[
    ("jan", 1), ("feb", 2), ("mar", 3), ("apr", 4),
    ("may", 5), ("jun", 6), ("jul", 7), ("aug", 8),
    ("sep", 9), ("oct", 10), ("nov", 11), ("dec", 12),
    ("january", 1), ("february", 2), ("march", 3), ("april", 4),
    ("june", 6), ("july", 7), ("august", 8),
    ("september", 9), ("october", 10), ("november", 11), ("december", 12),
];

impl CronExpr {
    pub fn parse(expr: &str, hash_id: Option<&str>, second_at_beginning: bool) -> Result<Self, String> {
        let parts: Vec<&str> = expr.split_whitespace().collect();

        let (seconds, minutes, hours, days, months, weekdays, has_seconds) = match parts.len() {
            5 => {
                // Standard 5-field cron: minute hour day month weekday
                let minutes = parse_field(parts[0], 0, 59, None, hash_id)?;
                let hours = parse_field(parts[1], 0, 23, None, hash_id)?;
                let (days, last_day) = parse_day_field(parts[2])?;
                let months = parse_field(parts[3], 1, 12, Some(&MONTH_NAMES), hash_id)?;
                let weekdays = parse_weekday_field(parts[4])?;
                (vec![0], minutes, hours, days, months, weekdays, false)
            }
            6 => {
                if second_at_beginning {
                    // 6-field with second at beginning: second minute hour day month weekday
                    let seconds = parse_field(parts[0], 0, 59, None, hash_id)?;
                    let minutes = parse_field(parts[1], 0, 59, None, hash_id)?;
                    let hours = parse_field(parts[2], 0, 23, None, hash_id)?;
                    let (days, _) = parse_day_field(parts[3])?;
                    let months = parse_field(parts[4], 1, 12, Some(&MONTH_NAMES), hash_id)?;
                    let weekdays = parse_weekday_field(parts[5])?;
                    (seconds, minutes, hours, days, months, weekdays, true)
                } else {
                    // 6-field with second at end: minute hour day month weekday second
                    let minutes = parse_field(parts[0], 0, 59, None, hash_id)?;
                    let hours = parse_field(parts[1], 0, 23, None, hash_id)?;
                    let (days, _) = parse_day_field(parts[2])?;
                    let months = parse_field(parts[3], 1, 12, Some(&MONTH_NAMES), hash_id)?;
                    let weekdays = parse_weekday_field(parts[4])?;
                    let seconds = parse_field(parts[5], 0, 59, None, hash_id)?;
                    (seconds, minutes, hours, days, months, weekdays, true)
                }
            }
            _ => return Err(format!("Invalid cron expression: expected 5 or 6 fields, got {}", parts.len())),
        };

        // Re-parse to get last_day and nth_weekdays
        let day_part = if parts.len() == 5 { parts[2] } else if second_at_beginning { parts[3] } else { parts[2] };
        let weekday_part = if parts.len() == 5 { parts[4] } else if second_at_beginning { parts[5] } else { parts[4] };

        let (_, last_day) = parse_day_field(day_part)?;
        let nth_weekdays = parse_nth_weekdays(weekday_part)?;

        Ok(CronExpr {
            seconds,
            minutes,
            hours,
            days,
            months,
            weekdays,
            nth_weekdays,
            last_day,
            has_seconds,
        })
    }
}

/// Parse a standard cron field (minute, hour, month, etc.)
fn parse_field(
    field: &str,
    min: u32,
    max: u32,
    name_map: Option<&[(&str, u32)]>,
    hash_id: Option<&str>,
) -> Result<Vec<u32>, String> {
    let mut values: HashSet<u32> = HashSet::new();

    for part in field.split(',') {
        let part = part.trim();
        if part.is_empty() {
            continue;
        }

        // Handle hash expressions like H or H(0-30)
        if part.starts_with('H') || part.starts_with('h') {
            let hash_values = parse_hash_field(part, min, max, hash_id)?;
            values.extend(hash_values);
            continue;
        }

        // Handle step expressions like */5 or 1-10/2
        if part.contains('/') {
            let step_values = parse_step(part, min, max, name_map)?;
            values.extend(step_values);
            continue;
        }

        // Handle range expressions like 1-5
        if part.contains('-') {
            let range_values = parse_range(part, min, max, name_map)?;
            values.extend(range_values);
            continue;
        }

        // Handle wildcard
        if part == "*" {
            for v in min..=max {
                values.insert(v);
            }
            continue;
        }

        // Handle single value (possibly with name)
        let value = parse_single_value(part, min, max, name_map)?;
        values.insert(value);
    }

    let mut result: Vec<u32> = values.into_iter().collect();
    result.sort();
    Ok(result)
}

/// Parse a hash field like H or H(0-30)
fn parse_hash_field(field: &str, min: u32, max: u32, hash_id: Option<&str>) -> Result<Vec<u32>, String> {
    let hash_value = if let Some(id) = hash_id {
        // Simple hash based on string
        let mut hash: u32 = 0;
        for b in id.bytes() {
            hash = hash.wrapping_mul(31).wrapping_add(b as u32);
        }
        hash
    } else {
        0
    };

    // Check for H(min-max) syntax
    if field.contains('(') && field.contains(')') {
        let start = field.find('(').unwrap();
        let end = field.find(')').unwrap();
        let range_str = &field[start+1..end];

        if range_str.contains('-') {
            let parts: Vec<&str> = range_str.split('-').collect();
            if parts.len() == 2 {
                let range_min: u32 = parts[0].parse().map_err(|_| format!("Invalid hash range: {}", field))?;
                let range_max: u32 = parts[1].parse().map_err(|_| format!("Invalid hash range: {}", field))?;
                let value = range_min + (hash_value % (range_max - range_min + 1));
                return Ok(vec![value]);
            }
        }
    }

    // Check for H/step syntax
    if field.contains('/') {
        let parts: Vec<&str> = field.split('/').collect();
        if parts.len() == 2 {
            let step: u32 = parts[1].parse().map_err(|_| format!("Invalid step: {}", parts[1]))?;
            let start = hash_value % step;
            let mut values = Vec::new();
            let mut v = start;
            while v <= max {
                if v >= min {
                    values.push(v);
                }
                v += step;
            }
            return Ok(values);
        }
    }

    // Simple H - pick a value in range
    let value = min + (hash_value % (max - min + 1));
    Ok(vec![value])
}

/// Parse a step expression like */5 or 1-10/2
fn parse_step(field: &str, min: u32, max: u32, name_map: Option<&[(&str, u32)]>) -> Result<Vec<u32>, String> {
    let parts: Vec<&str> = field.split('/').collect();
    if parts.len() != 2 {
        return Err(format!("Invalid step expression: {}", field));
    }

    let step_str = parts[1].trim();
    if step_str.is_empty() {
        return Err(format!("Invalid step expression: {}", field));
    }
    let step: u32 = step_str.parse().map_err(|_| format!("Invalid step value: {}", parts[1]))?;
    if step == 0 {
        return Err(format!("Step cannot be zero: {}", field));
    }

    let (start, end) = if parts[0] == "*" {
        (min, max)
    } else if parts[0].contains('-') {
        let range_parts: Vec<&str> = parts[0].split('-').collect();
        if range_parts.len() != 2 {
            return Err(format!("Invalid range in step: {}", field));
        }
        let start = parse_single_value(range_parts[0], min, max, name_map)?;
        let end = parse_single_value(range_parts[1], min, max, name_map)?;
        (start, end)
    } else {
        // Single value with step like 4/6 means start at 4, step by 6
        let start = parse_single_value(parts[0], min, max, name_map)?;
        (start, max)
    };

    let mut values = Vec::new();
    let mut v = start;
    while v <= end {
        values.push(v);
        v += step;
    }

    Ok(values)
}

/// Parse a range expression like 1-5
fn parse_range(field: &str, min: u32, max: u32, name_map: Option<&[(&str, u32)]>) -> Result<Vec<u32>, String> {
    let parts: Vec<&str> = field.split('-').collect();
    if parts.len() != 2 {
        return Err(format!("Invalid range: {}", field));
    }

    let start = parse_single_value(parts[0], min, max, name_map)?;
    let end = parse_single_value(parts[1], min, max, name_map)?;

    if start > end {
        // Wrap around (e.g., sun-thu = 0-4 for weekdays)
        let mut values: Vec<u32> = (start..=max).collect();
        values.extend(min..=end);
        Ok(values)
    } else {
        Ok((start..=end).collect())
    }
}

/// Parse a single value, possibly a name
fn parse_single_value(value: &str, min: u32, max: u32, name_map: Option<&[(&str, u32)]>) -> Result<u32, String> {
    let value = value.trim().to_lowercase();

    // Check for L (last day)
    if value == "l" {
        return Ok(max);
    }

    // Try name lookup first
    if let Some(names) = name_map {
        for (name, num) in names {
            if value == *name {
                return Ok(*num);
            }
        }
    }

    // Try parsing as number
    let num: u32 = value.parse().map_err(|_| format!("Invalid value: {}", value))?;

    if num < min || num > max {
        return Err(format!("Value {} out of range [{}, {}]", num, min, max));
    }

    Ok(num)
}

/// Parse day field, handling L for last day
fn parse_day_field(field: &str) -> Result<(Vec<u32>, bool), String> {
    let field_lower = field.to_lowercase();
    let mut last_day = false;
    let mut values: HashSet<u32> = HashSet::new();

    for part in field.split(',') {
        let part = part.trim().to_lowercase();
        if part.is_empty() {
            continue;
        }

        if part == "l" {
            last_day = true;
            continue;
        }

        // Handle range with L like 29-L
        if part.contains('-') && part.contains('l') {
            let range_parts: Vec<&str> = part.split('-').collect();
            if range_parts.len() == 2 {
                let start: u32 = if range_parts[0] == "l" {
                    last_day = true;
                    31
                } else {
                    range_parts[0].parse().map_err(|_| format!("Invalid day: {}", range_parts[0]))?
                };
                let end: u32 = if range_parts[1] == "l" {
                    last_day = true;
                    31
                } else {
                    range_parts[1].parse().map_err(|_| format!("Invalid day: {}", range_parts[1]))?
                };
                for v in start..=end {
                    values.insert(v);
                }
                continue;
            }
        }

        // Handle step expressions
        if part.contains('/') {
            let step_values = parse_step(&part, 1, 31, None)?;
            values.extend(step_values);
            continue;
        }

        // Handle range expressions
        if part.contains('-') {
            let range_values = parse_range(&part, 1, 31, None)?;
            values.extend(range_values);
            continue;
        }

        // Handle wildcard
        if part == "*" {
            for v in 1..=31 {
                values.insert(v);
            }
            continue;
        }

        // Handle single value
        let num: u32 = part.parse().map_err(|_| format!("Invalid day: {}", part))?;
        if num < 1 || num > 31 {
            return Err(format!("Day {} out of range [1, 31]", num));
        }
        values.insert(num);
    }

    let mut result: Vec<u32> = values.into_iter().collect();
    result.sort();

    // If only L was specified, return empty days list
    if result.is_empty() && last_day {
        return Ok((vec![], true));
    }

    Ok((result, last_day))
}

/// Parse weekday field, handling names and nth weekday syntax
fn parse_weekday_field(field: &str) -> Result<Vec<u32>, String> {
    let mut values: HashSet<u32> = HashSet::new();

    for part in field.split(',') {
        let part = part.trim().to_lowercase();
        if part.is_empty() {
            continue;
        }

        // Skip nth weekday syntax (handled separately)
        if part.contains('#') {
            // Still need to include the weekday in the list
            let weekday_part = part.split('#').next().unwrap();
            let weekday = parse_weekday_value(weekday_part)?;
            values.insert(weekday);
            continue;
        }

        // Handle step expressions
        if part.contains('/') {
            let step_values = parse_step(&part, 0, 6, Some(&DAY_NAMES))?;
            values.extend(step_values);
            continue;
        }

        // Handle range expressions
        if part.contains('-') {
            let range_values = parse_weekday_range(&part)?;
            values.extend(range_values);
            continue;
        }

        // Handle wildcard
        if part == "*" {
            for v in 0..=6 {
                values.insert(v);
            }
            continue;
        }

        // Handle single value
        let weekday = parse_weekday_value(&part)?;
        values.insert(weekday);
    }

    let mut result: Vec<u32> = values.into_iter().collect();
    result.sort();
    Ok(result)
}

/// Parse a single weekday value (name or number)
fn parse_weekday_value(value: &str) -> Result<u32, String> {
    let value = value.trim().to_lowercase();

    // Try name lookup
    for (name, num) in DAY_NAMES {
        if value == *name {
            return Ok(*num);
        }
    }

    // Try parsing as number
    let num: u32 = value.parse().map_err(|_| format!("Invalid weekday: {}", value))?;

    // Handle 7 as Sunday (some cron implementations)
    if num == 7 {
        return Ok(0);
    }

    if num > 6 {
        return Err(format!("Weekday {} out of range [0, 6]", num));
    }

    Ok(num)
}

/// Parse weekday range like sun-thu
fn parse_weekday_range(field: &str) -> Result<Vec<u32>, String> {
    let parts: Vec<&str> = field.split('-').collect();
    if parts.len() != 2 {
        return Err(format!("Invalid weekday range: {}", field));
    }

    let start = parse_weekday_value(parts[0])?;
    let end = parse_weekday_value(parts[1])?;

    if start <= end {
        Ok((start..=end).collect())
    } else {
        // Wrap around (e.g., fri-mon = 5,6,0,1)
        let mut values: Vec<u32> = (start..=6).collect();
        values.extend(0..=end);
        Ok(values)
    }
}

/// Parse nth weekday expressions like sat#1, wed#5
fn parse_nth_weekdays(field: &str) -> Result<Vec<(u32, u32)>, String> {
    let mut result = Vec::new();

    for part in field.split(',') {
        let part = part.trim().to_lowercase();
        if !part.contains('#') {
            continue;
        }

        let parts: Vec<&str> = part.split('#').collect();
        if parts.len() != 2 {
            return Err(format!("Invalid nth weekday: {}", part));
        }

        let weekday = parse_weekday_value(parts[0])?;
        let nth: u32 = parts[1].parse().map_err(|_| format!("Invalid nth value: {}", parts[1]))?;

        if nth < 1 || nth > 5 {
            return Err(format!("Nth value {} out of range [1, 5]", nth));
        }

        result.push((weekday, nth));
    }

    Ok(result)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_simple() {
        let expr = CronExpr::parse("*/5 * * * *", None, false).unwrap();
        assert_eq!(expr.minutes, vec![0, 5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]);
    }

    #[test]
    fn test_parse_range() {
        let expr = CronExpr::parse("1-5 * * * *", None, false).unwrap();
        assert_eq!(expr.minutes, vec![1, 2, 3, 4, 5]);
    }

    #[test]
    fn test_parse_weekday_names() {
        let expr = CronExpr::parse("0 0 * * sun-thu", None, false).unwrap();
        assert_eq!(expr.weekdays, vec![0, 1, 2, 3, 4]);
    }
}
