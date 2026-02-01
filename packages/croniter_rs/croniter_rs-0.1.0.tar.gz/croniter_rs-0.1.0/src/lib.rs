use pyo3::prelude::*;
use pyo3::types::{PyDateTime, PyType};
use pyo3::exceptions::PyValueError;
use chrono::{DateTime, Datelike, Duration, NaiveDateTime, Timelike, Utc, Weekday, Local};

mod parser;
mod schedule;

use schedule::CronSchedule;

// Custom exception types
pyo3::create_exception!(croniter_rs, CroniterBadCronError, PyValueError);
pyo3::create_exception!(croniter_rs, CroniterBadDateError, PyValueError);
pyo3::create_exception!(croniter_rs, CroniterNotAlphaError, PyValueError);
pyo3::create_exception!(croniter_rs, CroniterUnsupportedSyntaxError, PyValueError);

/// Convert Python datetime to chrono NaiveDateTime
fn py_datetime_to_naive(py: Python<'_>, dt: &Bound<'_, PyAny>) -> PyResult<NaiveDateTime> {
    // Handle None - use current time
    if dt.is_none() {
        let now = Local::now().naive_local();
        return Ok(now);
    }

    // Try to extract datetime components
    let year: i32 = dt.getattr("year")?.extract()?;
    let month: u32 = dt.getattr("month")?.extract()?;
    let day: u32 = dt.getattr("day")?.extract()?;
    let hour: u32 = dt.getattr("hour").map(|h| h.extract().unwrap_or(0)).unwrap_or(0);
    let minute: u32 = dt.getattr("minute").map(|m| m.extract().unwrap_or(0)).unwrap_or(0);
    let second: u32 = dt.getattr("second").map(|s| s.extract().unwrap_or(0)).unwrap_or(0);
    let microsecond: u32 = dt.getattr("microsecond").map(|m| m.extract().unwrap_or(0)).unwrap_or(0);

    Ok(NaiveDateTime::new(
        chrono::NaiveDate::from_ymd_opt(year, month, day)
            .ok_or_else(|| PyValueError::new_err("Invalid date"))?,
        chrono::NaiveTime::from_hms_micro_opt(hour, minute, second, microsecond)
            .ok_or_else(|| PyValueError::new_err("Invalid time"))?,
    ))
}

/// Convert chrono NaiveDateTime to Python datetime
fn naive_to_py_datetime<'py>(py: Python<'py>, dt: NaiveDateTime) -> PyResult<Bound<'py, PyDateTime>> {
    PyDateTime::new(
        py,
        dt.year(),
        dt.month() as u8,
        dt.day() as u8,
        dt.hour() as u8,
        dt.minute() as u8,
        dt.second() as u8,
        dt.and_utc().timestamp_subsec_micros(),
        None,
    )
}

/// Convert NaiveDateTime to timestamp (float)
fn naive_to_timestamp(dt: NaiveDateTime) -> f64 {
    dt.and_utc().timestamp() as f64 + (dt.and_utc().timestamp_subsec_micros() as f64 / 1_000_000.0)
}

/// Convert timestamp to NaiveDateTime
fn timestamp_to_naive(ts: f64) -> NaiveDateTime {
    let secs = ts.trunc() as i64;
    let nsecs = ((ts.fract()) * 1_000_000_000.0) as u32;
    DateTime::from_timestamp(secs, nsecs)
        .map(|dt| dt.naive_utc())
        .unwrap_or_else(|| Utc::now().naive_utc())
}

#[pyclass(name = "croniter")]
pub struct Croniter {
    schedule: CronSchedule,
    current_time: NaiveDateTime,
    start_time: NaiveDateTime,
    ret_type_is_float: bool,
    day_or: bool,
    is_prev: bool,
}

#[pymethods]
impl Croniter {
    #[new]
    #[pyo3(signature = (expr, start_time=None, ret_type=None, day_or=true, max_years_between_matches=50, hash_id=None, implement_cron_bug=false, second_at_beginning=false, expand_from_start_time=false, is_prev=false))]
    fn new(
        py: Python<'_>,
        expr: &str,
        start_time: Option<&Bound<'_, PyAny>>,
        ret_type: Option<&Bound<'_, PyAny>>,
        day_or: bool,
        max_years_between_matches: i32,
        hash_id: Option<&str>,
        implement_cron_bug: bool,
        second_at_beginning: bool,
        expand_from_start_time: bool,
        is_prev: bool,
    ) -> PyResult<Self> {
        // Parse start_time
        let start_dt = if let Some(st) = start_time {
            if st.is_none() {
                Local::now().naive_local()
            } else {
                // Check if it's a float (timestamp)
                if let Ok(ts) = st.extract::<f64>() {
                    timestamp_to_naive(ts)
                } else {
                    py_datetime_to_naive(py, st)?
                }
            }
        } else {
            Local::now().naive_local()
        };

        // Determine return type
        let ret_type_is_float = if let Some(rt) = ret_type {
            if rt.is_none() {
                false
            } else {
                // Check if it's the float type itself
                if let Ok(name) = rt.getattr("__name__") {
                    let name_str: String = name.extract().unwrap_or_default();
                    name_str == "float"
                } else {
                    // Check if it's a float instance
                    rt.extract::<f64>().is_ok()
                }
            }
        } else {
            false
        };

        // Parse the cron expression
        let schedule = CronSchedule::parse(expr, hash_id, second_at_beginning, day_or, implement_cron_bug)
            .map_err(|e| CroniterBadCronError::new_err(e))?;

        Ok(Croniter {
            schedule,
            current_time: start_dt,
            start_time: start_dt,
            ret_type_is_float,
            day_or,
            is_prev,
        })
    }

    fn __iter__(slf: PyRef<'_, Self>) -> PyRef<'_, Self> {
        slf
    }

    fn __next__(&mut self, py: Python<'_>) -> PyResult<Option<PyObject>> {
        if self.is_prev {
            let prev_time = self.schedule.prev_from(self.current_time);
            match prev_time {
                Some(t) => {
                    self.current_time = t;
                    Ok(Some(self.return_value_internal(py, t)?))
                }
                None => Ok(None),
            }
        } else {
            let next_time = self.schedule.next_from(self.current_time);
            match next_time {
                Some(t) => {
                    self.current_time = t;
                    Ok(Some(self.return_value_internal(py, t)?))
                }
                None => Ok(None),
            }
        }
    }

    /// Return self as iterator for forward iteration (Python croniter compatibility)
    /// Usage: for t in cron.all_next(datetime): ...
    #[pyo3(signature = (ret_type=None))]
    fn all_next(slf: PyRef<'_, Self>, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<Py<Self>> {
        let mut new_cron = Croniter {
            schedule: slf.schedule.clone(),
            current_time: slf.current_time,
            start_time: slf.start_time,
            ret_type_is_float: slf.ret_type_is_float,
            day_or: slf.day_or,
            is_prev: false,
        };
        // Update ret_type if provided
        if let Some(rt) = ret_type {
            if !rt.is_none() {
                if let Ok(name) = rt.getattr("__name__") {
                    let name_str: String = name.extract().unwrap_or_default();
                    new_cron.ret_type_is_float = name_str == "float";
                }
            }
        }
        Py::new(py, new_cron)
    }

    /// Return self as iterator for backward iteration (Python croniter compatibility)
    /// Usage: for t in cron.all_prev(datetime): ...
    #[pyo3(signature = (ret_type=None))]
    fn all_prev(slf: PyRef<'_, Self>, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<Py<Self>> {
        let mut new_cron = Croniter {
            schedule: slf.schedule.clone(),
            current_time: slf.current_time,
            start_time: slf.start_time,
            ret_type_is_float: slf.ret_type_is_float,
            day_or: slf.day_or,
            is_prev: true,
        };
        // Update ret_type if provided
        if let Some(rt) = ret_type {
            if !rt.is_none() {
                if let Ok(name) = rt.getattr("__name__") {
                    let name_str: String = name.extract().unwrap_or_default();
                    new_cron.ret_type_is_float = name_str == "float";
                }
            }
        }
        Py::new(py, new_cron)
    }

    /// Alias for get_next (Python croniter compatibility)
    #[pyo3(signature = (ret_type=None))]
    fn next(&mut self, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        self.get_next(py, ret_type)
    }

    /// Return iterator (Python croniter compatibility)
    /// Usage: for t in cron.iter(datetime): ...
    #[pyo3(signature = (ret_type=None))]
    fn iter(slf: PyRef<'_, Self>, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<Py<Self>> {
        let mut new_cron = Croniter {
            schedule: slf.schedule.clone(),
            current_time: slf.current_time,
            start_time: slf.start_time,
            ret_type_is_float: slf.ret_type_is_float,
            day_or: slf.day_or,
            is_prev: slf.is_prev,
        };
        // Update ret_type if provided
        if let Some(rt) = ret_type {
            if !rt.is_none() {
                if let Ok(name) = rt.getattr("__name__") {
                    let name_str: String = name.extract().unwrap_or_default();
                    new_cron.ret_type_is_float = name_str == "float";
                }
            }
        }
        Py::new(py, new_cron)
    }

    #[pyo3(signature = (ret_type=None))]
    fn get_next(&mut self, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        let next_time = self.schedule.next_from(self.current_time)
            .ok_or_else(|| CroniterBadDateError::new_err("No next date found"))?;

        self.current_time = next_time;

        self.return_value(py, next_time, ret_type)
    }

    #[pyo3(signature = (ret_type=None))]
    fn get_prev(&mut self, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        let prev_time = self.schedule.prev_from(self.current_time)
            .ok_or_else(|| CroniterBadDateError::new_err("No previous date found"))?;

        self.current_time = prev_time;

        self.return_value(py, prev_time, ret_type)
    }

    #[pyo3(signature = (ret_type=None))]
    fn get_current(&self, py: Python<'_>, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        self.return_value(py, self.current_time, ret_type)
    }

    fn set_current(&mut self, py: Python<'_>, start_time: &Bound<'_, PyAny>, force: Option<bool>) -> PyResult<f64> {
        let dt = if let Ok(ts) = start_time.extract::<f64>() {
            timestamp_to_naive(ts)
        } else {
            py_datetime_to_naive(py, start_time)?
        };
        self.current_time = dt;
        Ok(naive_to_timestamp(dt))
    }

    #[getter]
    fn expanded(&self, py: Python<'_>) -> PyResult<PyObject> {
        let expanded = self.schedule.get_expanded();
        Ok(expanded.into_pyobject(py)?.unbind())
    }

    #[classmethod]
    #[pyo3(signature = (expr, hash_id=None))]
    fn is_valid(_cls: &Bound<'_, PyType>, expr: &str, hash_id: Option<&str>) -> bool {
        CronSchedule::parse(expr, hash_id, false, true, false).is_ok()
    }

    /// Expand a cron expression into its component values (class method)
    /// Returns a tuple of (expanded_fields, extra_info)
    #[classmethod]
    #[pyo3(signature = (expr, hash_id=None, second_at_beginning=false))]
    fn expand(_cls: &Bound<'_, PyType>, py: Python<'_>, expr: &str, hash_id: Option<&str>, second_at_beginning: bool) -> PyResult<PyObject> {
        let schedule = CronSchedule::parse(expr, hash_id, second_at_beginning, true, false)
            .map_err(|e| CroniterBadCronError::new_err(e))?;
        let expanded = schedule.get_expanded();

        // Return format matching Python croniter: (expanded_list, extra_dict)
        // Python croniter returns wildcards as ['*'] but we expand them
        // For better compatibility, we return the expanded values
        let empty_dict = pyo3::types::PyDict::new(py);
        let result = (expanded, empty_dict);
        Ok(result.into_pyobject(py)?.unbind().into())
    }

    #[classmethod]
    #[pyo3(signature = (expr, dt, day_or=true))]
    fn match_(_cls: &Bound<'_, PyType>, py: Python<'_>, expr: &str, dt: &Bound<'_, PyAny>, day_or: Option<bool>) -> PyResult<bool> {
        let naive_dt = py_datetime_to_naive(py, dt)?;
        let schedule = CronSchedule::parse(expr, None, false, day_or.unwrap_or(true), false)
            .map_err(|e| CroniterBadCronError::new_err(e))?;
        Ok(schedule.matches(naive_dt))
    }

    #[staticmethod]
    #[pyo3(name = "match")]
    #[pyo3(signature = (expr, dt, day_or=true))]
    fn match_static(py: Python<'_>, expr: &str, dt: &Bound<'_, PyAny>, day_or: Option<bool>) -> PyResult<bool> {
        let naive_dt = py_datetime_to_naive(py, dt)?;
        let schedule = CronSchedule::parse(expr, None, false, day_or.unwrap_or(true), false)
            .map_err(|e| CroniterBadCronError::new_err(e))?;
        Ok(schedule.matches(naive_dt))
    }

    /// Check if there's a match within a time range
    #[staticmethod]
    #[pyo3(signature = (expr, start, end, day_or=true))]
    fn match_range(py: Python<'_>, expr: &str, start: &Bound<'_, PyAny>, end: &Bound<'_, PyAny>, day_or: Option<bool>) -> PyResult<bool> {
        let start_dt = py_datetime_to_naive(py, start)?;
        let end_dt = py_datetime_to_naive(py, end)?;

        let schedule = CronSchedule::parse(expr, None, false, day_or.unwrap_or(true), false)
            .map_err(|e| CroniterBadCronError::new_err(e))?;

        // Check if there's any match between start and end
        // Start from one second before start_dt to include start_dt itself
        let check_start = start_dt - Duration::seconds(1);
        if let Some(next_match) = schedule.next_from(check_start) {
            Ok(next_match >= start_dt && next_match <= end_dt)
        } else {
            Ok(false)
        }
    }

    /// Get the nth weekday of a month
    /// weekday: 0=Monday, 6=Sunday (Python weekday convention)
    /// nth: 1-5 for first through fifth occurrence
    #[classmethod]
    #[pyo3(signature = (year, month, weekday, nth))]
    fn _get_nth_weekday_of_month(_cls: &Bound<'_, PyType>, py: Python<'_>, year: i32, month: u32, weekday: u32, nth: u32) -> PyResult<PyObject> {
        // Convert Python weekday (0=Mon) to chrono weekday
        let target_weekday = match weekday {
            0 => Weekday::Mon,
            1 => Weekday::Tue,
            2 => Weekday::Wed,
            3 => Weekday::Thu,
            4 => Weekday::Fri,
            5 => Weekday::Sat,
            6 => Weekday::Sun,
            _ => return Err(PyValueError::new_err("Invalid weekday")),
        };

        // Find the first day of the month
        let first_day = chrono::NaiveDate::from_ymd_opt(year, month, 1)
            .ok_or_else(|| PyValueError::new_err("Invalid date"))?;

        // Find the first occurrence of the target weekday
        let mut current = first_day;
        while current.weekday() != target_weekday {
            current = current.succ_opt().ok_or_else(|| PyValueError::new_err("Date overflow"))?;
        }

        // Move to the nth occurrence
        if nth > 1 {
            current = current + Duration::days(((nth - 1) * 7) as i64);
        }

        // Check if we're still in the same month
        if current.month() != month {
            return Ok(py.None());
        }

        Ok(current.day().into_pyobject(py)?.unbind().into())
    }

    /// Get multiple next occurrences
    #[pyo3(signature = (n, ret_type=None))]
    fn get_next_n(&mut self, py: Python<'_>, n: usize, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        let mut results = Vec::new();
        for _ in 0..n {
            let next_time = self.schedule.next_from(self.current_time)
                .ok_or_else(|| CroniterBadDateError::new_err("No next date found"))?;
            self.current_time = next_time;
            results.push(self.return_value(py, next_time, ret_type)?);
        }
        Ok(results.into_pyobject(py)?.unbind())
    }

    /// Get multiple previous occurrences
    #[pyo3(signature = (n, ret_type=None))]
    fn get_prev_n(&mut self, py: Python<'_>, n: usize, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        let mut results = Vec::new();
        for _ in 0..n {
            let prev_time = self.schedule.prev_from(self.current_time)
                .ok_or_else(|| CroniterBadDateError::new_err("No previous date found"))?;
            self.current_time = prev_time;
            results.push(self.return_value(py, prev_time, ret_type)?);
        }
        Ok(results.into_pyobject(py)?.unbind())
    }
}

impl Croniter {
    fn return_value(&self, py: Python<'_>, dt: NaiveDateTime, ret_type: Option<&Bound<'_, PyAny>>) -> PyResult<PyObject> {
        // Determine if we should return float or datetime
        let return_float = if let Some(rt) = ret_type {
            if rt.is_none() {
                self.ret_type_is_float
            } else {
                let type_name = rt.get_type().name()?;
                let type_name_str = type_name.to_string();
                if type_name_str.contains("float") || type_name_str == "type" {
                    // Check if it's the float type itself
                    if let Ok(name) = rt.getattr("__name__") {
                        let name_str: String = name.extract()?;
                        name_str == "float"
                    } else {
                        type_name_str.contains("float")
                    }
                } else {
                    false
                }
            }
        } else {
            self.ret_type_is_float
        };

        if return_float {
            Ok(naive_to_timestamp(dt).into_pyobject(py)?.unbind().into())
        } else {
            Ok(naive_to_py_datetime(py, dt)?.into_any().unbind())
        }
    }

    fn return_value_internal(&self, py: Python<'_>, dt: NaiveDateTime) -> PyResult<PyObject> {
        if self.ret_type_is_float {
            Ok(naive_to_timestamp(dt).into_pyobject(py)?.unbind().into())
        } else {
            Ok(naive_to_py_datetime(py, dt)?.into_any().unbind())
        }
    }
}

/// Helper function to convert datetime to timestamp
#[pyfunction]
fn datetime_to_timestamp(py: Python<'_>, dt: &Bound<'_, PyAny>) -> PyResult<f64> {
    let naive = py_datetime_to_naive(py, dt)?;
    Ok(naive_to_timestamp(naive))
}

/// A Python module implemented in Rust.
#[pymodule]
fn croniter_rs(py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<Croniter>()?;
    m.add_function(wrap_pyfunction!(datetime_to_timestamp, m)?)?;
    m.add("CroniterBadCronError", py.get_type::<CroniterBadCronError>())?;
    m.add("CroniterBadDateError", py.get_type::<CroniterBadDateError>())?;
    m.add("CroniterNotAlphaError", py.get_type::<CroniterNotAlphaError>())?;
    m.add("CroniterUnsupportedSyntaxError", py.get_type::<CroniterUnsupportedSyntaxError>())?;
    Ok(())
}
