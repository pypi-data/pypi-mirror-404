/// 合法手生成の種類を定義するトレイト
pub trait MoveGenType {
    const CAPTURES: bool;
    const QUIETS: bool;
    const EVASIONS: bool;
    const QUIET_CHECKS: bool;
    const GENERATE_ALL_LEGAL: bool;
    const IS_CHECKS: bool;
    const IS_QUIETS_PRO_MINUS: bool;
    const IS_LEGAL: bool;
    const IS_CAPTURE_PLUS_PRO: bool;
    const IS_RECAPTURES: bool;

    #[inline]
    #[must_use]
    fn generate_all_legal() -> bool {
        Self::GENERATE_ALL_LEGAL || super::generate_all_legal_moves_enabled()
    }
}

/// 取る手のみ生成
pub struct Captures;
impl MoveGenType for Captures {
    const CAPTURES: bool = true;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 取る手のみ生成（歩・大駒の不成も含む）
pub struct CapturesAll;
impl MoveGenType for CapturesAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 取る手 + 歩の成る手（YaneuraOu CAPTURES_PRO_PLUS相当）
///
/// qsearch（静止探索）で使用するモード。
/// - 捕獲手（相手の駒を取る手）
/// - 歩が敵陣に成る手（捕獲でなくてもよい）
pub struct CapturePlusPro;
impl MoveGenType for CapturePlusPro {
    const CAPTURES: bool = true;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = true;
    const IS_RECAPTURES: bool = false;
}

/// 取る手 + 歩成り（歩/大駒の不成も含む）
pub struct CapturePlusProAll;
impl MoveGenType for CapturePlusProAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = true;
    const IS_RECAPTURES: bool = false;
}

/// 静かな手のみ生成
pub struct Quiets;
impl MoveGenType for Quiets {
    const CAPTURES: bool = false;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 静かな手のみ生成（歩・大駒の不成も含む）
pub struct QuietsAll;
impl MoveGenType for QuietsAll {
    const CAPTURES: bool = false;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 静かな手のみ生成（歩の成る手を除外）
pub struct QuietsProMinus;
impl MoveGenType for QuietsProMinus {
    const CAPTURES: bool = false;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = true;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 静かな手のみ生成（歩の成る手を除外、歩・大駒の不成を含む）
pub struct QuietsProMinusAll;
impl MoveGenType for QuietsProMinusAll {
    const CAPTURES: bool = false;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = true;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手回避手のみ生成
pub struct Evasions;
impl MoveGenType for Evasions {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = true;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手回避手のみ生成（歩・大駒の不成も含む）
pub struct EvasionsAll;
impl MoveGenType for EvasionsAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = true;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 非王手回避手のみ生成
pub struct NonEvasions;
impl MoveGenType for NonEvasions {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 非王手回避手のみ生成（歩・大駒の不成を含む）
pub struct NonEvasionsAll;
impl MoveGenType for NonEvasionsAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 合法手すべて（歩・香・大駒の不成は生成しない）
pub struct Legal;
impl MoveGenType for Legal {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = true;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 合法手すべて（歩・大駒の不成を含む）
pub struct LegalAll;
impl MoveGenType for LegalAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = true;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手となる指し手を生成
pub struct Checks;
impl MoveGenType for Checks {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = true;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手となる指し手を生成（歩・大駒の不成を含む）
pub struct ChecksAll;
impl MoveGenType for ChecksAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = true;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手となる静かな手のみ生成
pub struct QuietChecks;
impl MoveGenType for QuietChecks {
    const CAPTURES: bool = false;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = true;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 王手となる静かな手のみ生成（歩・大駒の不成も含む）
pub struct QuietChecksAll;
impl MoveGenType for QuietChecksAll {
    const CAPTURES: bool = false;
    const QUIETS: bool = false;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = true;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = false;
}

/// 指定マスへの移動手（Recaptures）
pub struct Recaptures;
impl MoveGenType for Recaptures {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = false;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = true;
}

/// 指定マスへの移動手（Recaptures, 歩の不成なども含む）
pub struct RecapturesAll;
impl MoveGenType for RecapturesAll {
    const CAPTURES: bool = true;
    const QUIETS: bool = true;
    const EVASIONS: bool = false;
    const QUIET_CHECKS: bool = false;
    const GENERATE_ALL_LEGAL: bool = true;
    const IS_CHECKS: bool = false;
    const IS_QUIETS_PRO_MINUS: bool = false;
    const IS_LEGAL: bool = false;
    const IS_CAPTURE_PLUS_PRO: bool = false;
    const IS_RECAPTURES: bool = true;
}
