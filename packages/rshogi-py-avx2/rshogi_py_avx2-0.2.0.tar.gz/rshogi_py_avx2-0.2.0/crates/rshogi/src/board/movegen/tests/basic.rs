use super::*;
use crate::board::MoveList;

#[test]
fn move_gen_type_flags_are_wired() {
    #[allow(clippy::missing_const_for_fn)]
    fn assert_movegen_type<T: MoveGenType>() {}
    assert_movegen_type::<Captures>();
    assert_movegen_type::<Quiets>();
    assert_movegen_type::<Evasions>();
    assert_movegen_type::<NonEvasionsAll>();
    assert_movegen_type::<QuietChecks>();
}

#[test]
fn generate_moves_invocations_compile() {
    let pos = crate::board::hirate_position();
    let mut list = MoveList::new();

    generate_moves::<NonEvasionsAll>(&pos, &mut list);
    generate_moves::<Captures>(&pos, &mut list);
    generate_moves::<Quiets>(&pos, &mut list);
    generate_quiet_checks(&pos, &mut list);
}
