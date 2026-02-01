use pyo3::exceptions::{PyIndexError, PyTypeError, PyValueError};
use pyo3::prelude::*;
use pyo3::types::{PyBytes, PyType};

use ::rshogi::core::board::movegen::{generate_moves, Evasions, LegalAll, NonEvasions};
use ::rshogi::core::board::{self, MoveList, PackedSfen, Position};
use ::rshogi::core::types::{Move, Move16, RepetitionState, MOVE_NONE};

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

    #[allow(clippy::wrong_self_convention)]
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

    #[classmethod]
    fn from_usi(_cls: &Bound<'_, PyType>, usi: &str) -> PyResult<Self> {
        Move::from_usi(usi)
            .filter(|mv| mv.is_ok())
            .map(|mv| Self { inner: mv })
            .ok_or_else(|| PyValueError::new_err("invalid USI move"))
    }

    #[allow(clippy::wrong_self_convention)]
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
            position.set(sfen).map_err(|err| PyValueError::new_err(err.to_string()))?;
        } else {
            position.set_hirate();
        }
        position.init_stack();
        Ok(Self { position, history: Vec::new() })
    }

    fn sfen(&self) -> String {
        self.position.sfen(None)
    }

    fn psfen<'py>(&self, py: Python<'py>) -> Bound<'py, PyBytes> {
        let packed = self.position.sfen_pack();
        PyBytes::new(py, &packed.data)
    }

    fn set_sfen(&mut self, sfen: &str) -> PyResult<()> {
        self.position.set(sfen).map_err(|err| PyValueError::new_err(err.to_string()))?;
        self.position.init_stack();
        self.history.clear();
        Ok(())
    }

    fn set_psfen(&mut self, psfen: &Bound<'_, PyAny>) -> PyResult<()> {
        let data = extract_psfen_bytes(psfen)?;
        let packed = PackedSfen { data };
        self.position
            .set_from_packed_sfen(&packed, false, 1)
            .map_err(|err| PyValueError::new_err(format!("{err:?}")))?;
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
        self.position.undo_move(mv).map_err(|err| PyValueError::new_err(format!("{err:?}")))?;
        Ok(PyMove { inner: mv })
    }

    fn peek(&self) -> Option<PyMove> {
        self.history.last().copied().map(|mv| PyMove { inner: mv })
    }

    fn history(&self) -> Vec<PyMove> {
        self.history.iter().copied().map(|mv| PyMove { inner: mv }).collect()
    }

    fn is_legal(&self, mv: &Bound<'_, PyAny>) -> PyResult<bool> {
        let move_value = parse_move(mv, &self.position)?;
        Ok(self.position.is_legal(move_value))
    }

    fn legal_moves(&self) -> Vec<PyMove> {
        let mut list = MoveList::new();
        generate_moves::<LegalAll>(&self.position, &mut list);
        collect_py_moves(&list)
    }

    fn pseudo_legal_moves(&self) -> Vec<PyMove> {
        let mut list = MoveList::new();
        if self.position.in_check() {
            generate_moves::<Evasions>(&self.position, &mut list);
        } else {
            generate_moves::<NonEvasions>(&self.position, &mut list);
        }
        collect_py_moves(&list)
    }

    fn turn(&self) -> String {
        self.position.side_to_move().to_string().to_lowercase()
    }

    fn move_number(&self) -> u32 {
        self.position.game_ply() as u32
    }

    fn is_check(&self) -> bool {
        self.position.in_check()
    }

    fn is_checkmate(&self) -> bool {
        self.position.in_check() && self.position.is_mated()
    }

    fn is_gameover(&self) -> bool {
        if self.is_checkmate() {
            return true;
        }
        if self.position.get_repetition_state() != RepetitionState::None {
            return true;
        }
        self.position.declaration_win() != MOVE_NONE
    }

    fn repetition_state(&self) -> String {
        self.position.get_repetition_state().to_string()
    }

    fn is_repetition(&self) -> bool {
        self.position.get_repetition_state() != RepetitionState::None
    }

    fn is_draw(&self) -> bool {
        self.position.get_repetition_state() == RepetitionState::Draw
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
        let move16 =
            Move16::from_usi(usi).ok_or_else(|| PyValueError::new_err("invalid USI move"))?;
        position.to_move(move16)
    } else if let Ok(mv16) = mv.extract::<PyRef<'_, PyMove16>>() {
        position.to_move(mv16.inner)
    } else if let Ok(mv32) = mv.extract::<PyRef<'_, PyMove>>() {
        mv32.inner
    } else if let Ok(raw) = mv.extract::<u32>() {
        Move(raw)
    } else {
        return Err(PyTypeError::new_err("move must be Move, Move16, USI string, or int"));
    };

    if !move_value.is_ok() {
        return Err(PyValueError::new_err("invalid move value"));
    }

    Ok(move_value)
}

fn extract_psfen_bytes(psfen: &Bound<'_, PyAny>) -> PyResult<[u8; 32]> {
    let data: Vec<u8> = psfen.extract()?;
    if data.len() != 32 {
        return Err(PyValueError::new_err("psfen must be 32 bytes"));
    }
    let mut packed = [0u8; 32];
    packed.copy_from_slice(&data);
    Ok(packed)
}

fn collect_py_moves(list: &MoveList) -> Vec<PyMove> {
    list.iter().copied().map(|mv| PyMove { inner: mv }).collect()
}

#[cfg(all(test, feature = "python-tests"))]
mod tests {
    use super::*;
    use ::rshogi::core::board::movegen::{generate_moves, Evasions, NonEvasions};

    const STARTPOS_SFEN: &str = "lnsgkgsnl/1r5b1/ppppppppp/9/9/9/PPPPPPPPP/1B5R1/LNSGKGSNL b - 1";
    const DOUBLE_CHECK_SFEN: &str =
        "ln2+r1r2/5s+Pkl/3+B1p1p1/p4B2p/2P6/P6PP/1PNP1P3/2G3SK1/L4G1NL w 2GSN3Ps3p 76";

    #[test]
    fn py_move_from_usi_rejects_special_moves() {
        Python::attach(|py| {
            let cls = py.get_type::<PyMove>();
            assert!(PyMove::from_usi(&cls, "7g7f").is_ok());
            assert!(PyMove::from_usi(&cls, "none").is_err());
            assert!(PyMove::from_usi(&cls, "null").is_err());
        });
    }

    #[test]
    fn pseudo_legal_moves_in_check_uses_evasions() {
        let board = PyBoard::new(Some(DOUBLE_CHECK_SFEN)).expect("board init");
        assert!(board.position.in_check(), "position should be in check for this test");

        let mut expected = MoveList::new();
        generate_moves::<Evasions>(&board.position, &mut expected);
        let actual = board.pseudo_legal_moves();

        assert_eq!(actual.len(), expected.len());
    }

    #[test]
    fn pseudo_legal_moves_not_in_check_uses_non_evasions() {
        let board = PyBoard::new(Some(STARTPOS_SFEN)).expect("board init");
        assert!(!board.position.in_check(), "position should not be in check");

        let mut expected = MoveList::new();
        generate_moves::<NonEvasions>(&board.position, &mut expected);
        let actual = board.pseudo_legal_moves();

        assert_eq!(actual.len(), expected.len());
    }

    #[test]
    fn is_checkmate_matches_core_semantics() {
        let board = PyBoard::new(Some(STARTPOS_SFEN)).expect("board init");
        let expected = board.position.in_check() && board.position.is_mated();
        assert_eq!(board.is_checkmate(), expected);

        let board = PyBoard::new(Some(DOUBLE_CHECK_SFEN)).expect("board init");
        let expected = board.position.in_check() && board.position.is_mated();
        assert_eq!(board.is_checkmate(), expected);
    }

    #[test]
    fn is_gameover_matches_core_semantics() {
        let board = PyBoard::new(Some(STARTPOS_SFEN)).expect("board init");
        let expected = (board.position.in_check() && board.position.is_mated())
            || board.position.get_repetition_state() != RepetitionState::None
            || board.position.declaration_win() != MOVE_NONE;
        assert_eq!(board.is_gameover(), expected);

        let board = PyBoard::new(Some(DOUBLE_CHECK_SFEN)).expect("board init");
        let expected = (board.position.in_check() && board.position.is_mated())
            || board.position.get_repetition_state() != RepetitionState::None
            || board.position.declaration_win() != MOVE_NONE;
        assert_eq!(board.is_gameover(), expected);
    }

    #[test]
    fn repetition_helpers_default_to_none() {
        let board = PyBoard::new(Some(STARTPOS_SFEN)).expect("board init");
        assert_eq!(board.repetition_state(), "rep_none");
        assert!(!board.is_repetition());
        assert!(!board.is_draw());
    }
}
