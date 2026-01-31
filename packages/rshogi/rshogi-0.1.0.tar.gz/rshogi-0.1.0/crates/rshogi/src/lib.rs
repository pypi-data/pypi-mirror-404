use pyo3::exceptions::{PyIndexError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::PyType;

use rshogi_core::board::{self, Position};
use rshogi_core::types::{Move, Move16};

#[pyclass(name = "Move16")]
#[derive(Clone, Copy)]
struct PyMove16 {
    inner: Move16,
}

#[pymethods]
impl PyMove16 {
    #[new]
    fn new(value: u16) -> Self {
        Self { inner: Move16(value) }
    }

    #[classmethod]
    fn from_usi(_cls: &Bound<'_, PyType>, s: &str) -> PyResult<Self> {
        Move16::from_usi(s)
            .map(|mv| Self { inner: mv })
            .ok_or_else(|| PyValueError::new_err("invalid USI move"))
    }

    fn to_usi(&self) -> String {
        self.inner.to_usi()
    }

    fn is_drop(&self) -> bool {
        self.inner.is_drop()
    }

    fn is_promote(&self) -> bool {
        self.inner.is_promote()
    }

    fn is_ok(&self) -> bool {
        self.inner.is_ok()
    }

    #[getter]
    fn value(&self) -> u16 {
        self.inner.0
    }

    fn __int__(&self) -> u16 {
        self.inner.0
    }

    fn __repr__(&self) -> String {
        format!("Move16({})", self.inner.to_usi())
    }

    fn __str__(&self) -> String {
        self.inner.to_usi()
    }
}

#[pyclass(name = "Move")]
#[derive(Clone, Copy)]
struct PyMove {
    inner: Move,
}

#[pymethods]
impl PyMove {
    #[new]
    fn new(value: u32) -> Self {
        Self { inner: Move(value) }
    }

    fn to_usi(&self) -> String {
        self.inner.to_usi()
    }

    fn is_drop(&self) -> bool {
        self.inner.is_drop()
    }

    fn is_promote(&self) -> bool {
        self.inner.is_promote()
    }

    fn is_ok(&self) -> bool {
        self.inner.is_ok()
    }

    #[getter]
    fn value(&self) -> u32 {
        self.inner.0
    }

    fn __int__(&self) -> u32 {
        self.inner.0
    }

    fn __repr__(&self) -> String {
        format!("Move({})", self.inner.to_usi())
    }

    fn __str__(&self) -> String {
        self.inner.to_usi()
    }
}

#[pyclass(unsendable, name = "Board")]
struct PyBoard {
    position: Position,
    history: Vec<Move>,
}

#[pymethods]
impl PyBoard {
    #[new]
    #[pyo3(signature = (sfen=None))]
    fn new(sfen: Option<&str>) -> PyResult<Self> {
        board::init();
        let mut position = Position::new();
        if let Some(sfen) = sfen {
            position
                .set(sfen)
                .map_err(|err| PyValueError::new_err(err.to_string()))?;
        } else {
            position.set_hirate();
        }
        position.init_stack();
        Ok(Self {
            position,
            history: Vec::new(),
        })
    }

    fn sfen(&self) -> String {
        self.position.sfen(None)
    }

    fn set_sfen(&mut self, sfen: &str) -> PyResult<()> {
        self.position
            .set(sfen)
            .map_err(|err| PyValueError::new_err(err.to_string()))?;
        self.position.init_stack();
        self.history.clear();
        Ok(())
    }

    fn push(&mut self, mv: &Bound<'_, PyAny>) -> PyResult<()> {
        let move_value = parse_move(mv, &self.position)?;
        if !self.position.is_legal(move_value) {
            return Err(PyValueError::new_err("illegal move"));
        }
        self.position.do_move(move_value);
        self.history.push(move_value);
        Ok(())
    }

    fn pop(&mut self) -> PyResult<PyMove> {
        let mv = self.history.pop().ok_or_else(|| PyIndexError::new_err("no moves to pop"))?;
        self.position
            .undo_move(mv)
            .map_err(|err| PyValueError::new_err(format!("{err:?}")))?;
        Ok(PyMove { inner: mv })
    }

    fn is_legal(&self, mv: &Bound<'_, PyAny>) -> PyResult<bool> {
        let move_value = parse_move(mv, &self.position)?;
        Ok(self.position.is_legal(move_value))
    }
}

#[pymodule]
fn rshogi(_py: Python<'_>, m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<PyBoard>()?;
    m.add_class::<PyMove>()?;
    m.add_class::<PyMove16>()?;
    Ok(())
}

fn parse_move(mv: &Bound<'_, PyAny>, position: &Position) -> PyResult<Move> {
    let move_value = if let Ok(usi) = mv.extract::<&str>() {
        let move16 = Move16::from_usi(usi)
            .ok_or_else(|| PyValueError::new_err("invalid USI move"))?;
        position.to_move(move16)
    } else if let Ok(mv16) = mv.extract::<PyRef<'_, PyMove16>>() {
        position.to_move(mv16.inner)
    } else if let Ok(mv32) = mv.extract::<PyRef<'_, PyMove>>() {
        mv32.inner
    } else if let Ok(raw) = mv.extract::<u32>() {
        Move(raw)
    } else {
        return Err(PyTypeError::new_err(
            "move must be Move, Move16, USI string, or int",
        ));
    };

    if !move_value.is_ok() {
        return Err(PyValueError::new_err("invalid move value"));
    }

    Ok(move_value)
}
