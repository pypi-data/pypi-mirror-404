//! 入玉ルール設定

/// 入玉ルール文字列（YaneuraOu互換）
pub const EKR_STRINGS: [&str; 6] =
    ["NoEnteringKing", "CSARule24", "CSARule24H", "CSARule27", "CSARule27H", "TryRule"];

/// 入玉ルール
#[derive(Copy, Clone, Debug, PartialEq, Eq)]
pub enum EnteringKingRule {
    /// 入玉ルールなし
    None,
    /// 24点法（31点以上で宣言勝ち）
    Point24,
    /// 24点法（駒落ち対応）
    Point24Handicap,
    /// 27点法（CSAルール）
    Point27,
    /// 27点法（駒落ち対応）
    Point27Handicap,
    /// トライルール
    TryRule,
    /// 未設定
    Unset,
}

impl EnteringKingRule {
    /// YaneuraOu互換の文字列に変換
    #[must_use]
    pub const fn as_str(self) -> &'static str {
        match self {
            Self::None => EKR_STRINGS[0],
            Self::Point24 => EKR_STRINGS[1],
            Self::Point24Handicap => EKR_STRINGS[2],
            Self::Point27 => EKR_STRINGS[3],
            Self::Point27Handicap => EKR_STRINGS[4],
            Self::TryRule => EKR_STRINGS[5],
            Self::Unset => "EKR_NULL",
        }
    }
}

/// 文字列に対応するEnteringKingRuleを取得する。
#[must_use]
pub fn to_entering_king_rule(rule: &str) -> Option<EnteringKingRule> {
    for (idx, &name) in EKR_STRINGS.iter().enumerate() {
        if rule == name {
            return Some(match idx {
                0 => EnteringKingRule::None,
                1 => EnteringKingRule::Point24,
                2 => EnteringKingRule::Point24Handicap,
                3 => EnteringKingRule::Point27,
                4 => EnteringKingRule::Point27Handicap,
                5 => EnteringKingRule::TryRule,
                _ => return None,
            });
        }
    }
    None
}

impl Default for EnteringKingRule {
    fn default() -> Self {
        Self::Unset
    }
}
