use std::convert::TryFrom;
use std::fmt;
use std::str::FromStr;

/// 筋を表す型（1筋～9筋、内部的には0～8）
#[repr(transparent)]
#[derive(Copy, Clone, PartialEq, Eq, Debug)]
pub struct File(pub i8);

impl File {
    // 関連定数（YaneuraOu互換）
    /// ゼロ値（`File::FILE_1` と同じ）
    pub const FILE_ZERO: Self = Self(0);
    /// 1筋
    pub const FILE_1: Self = Self(0);
    /// 2筋
    pub const FILE_2: Self = Self(1);
    /// 3筋
    pub const FILE_3: Self = Self(2);
    /// 4筋
    pub const FILE_4: Self = Self(3);
    /// 5筋
    pub const FILE_5: Self = Self(4);
    /// 6筋
    pub const FILE_6: Self = Self(5);
    /// 7筋
    pub const FILE_7: Self = Self(6);
    /// 8筋
    pub const FILE_8: Self = Self(7);
    /// 9筋
    pub const FILE_9: Self = Self(8);
    /// 筋の総数
    pub const FILE_NB: usize = 9;

    /// USI文字（'1'～'9'）からFileを生成する
    #[inline]
    #[must_use]
    pub const fn from_usi(c: char) -> Option<Self> {
        match c {
            '1' => Some(Self::FILE_1),
            '2' => Some(Self::FILE_2),
            '3' => Some(Self::FILE_3),
            '4' => Some(Self::FILE_4),
            '5' => Some(Self::FILE_5),
            '6' => Some(Self::FILE_6),
            '7' => Some(Self::FILE_7),
            '8' => Some(Self::FILE_8),
            '9' => Some(Self::FILE_9),
            _ => None,
        }
    }

    /// USI文字（'1'～'9'）に変換する
    #[inline]
    #[must_use]
    pub fn to_usi(self) -> char {
        debug_assert!(self.is_ok(), "Invalid file: {self:?}");
        let offset = u8::try_from(self.0).expect("file index should be non-negative");
        char::from(b'1' + offset)
    }

    /// 有効な値かどうかを判定する
    #[inline]
    #[must_use]
    pub const fn is_ok(self) -> bool {
        self.0 >= Self::FILE_1.raw() && self.0 <= Self::FILE_9.raw()
    }

    /// 内部値からFileを生成する（クレート内部用）
    #[inline]
    pub(crate) const fn new(val: i8) -> Self {
        Self(val)
    }

    /// 内部値を取得する
    #[inline]
    #[must_use]
    pub const fn raw(self) -> i8 {
        self.0
    }
}

impl fmt::Display for File {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_ok() {
            write!(f, "{}", self.to_usi())
        } else {
            write!(f, "Invalid({})", self.0)
        }
    }
}

impl FromStr for File {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 1 {
            return Err(format!("Invalid file string: {s}"));
        }
        Self::from_usi(s.chars().next().unwrap()).ok_or_else(|| format!("Invalid file string: {s}"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_file_constants() {
        // 定数値検証（File::FILE_1=0, File::FILE_9=8, File::FILE_NB=9）
        assert_eq!(File::FILE_ZERO.raw(), 0);
        assert_eq!(File::FILE_1.raw(), 0);
        assert_eq!(File::FILE_2.raw(), 1);
        assert_eq!(File::FILE_3.raw(), 2);
        assert_eq!(File::FILE_4.raw(), 3);
        assert_eq!(File::FILE_5.raw(), 4);
        assert_eq!(File::FILE_6.raw(), 5);
        assert_eq!(File::FILE_7.raw(), 6);
        assert_eq!(File::FILE_8.raw(), 7);
        assert_eq!(File::FILE_9.raw(), 8);
        assert_eq!(File::FILE_NB, 9);
    }

    #[test]
    fn test_file_usi_conversion() {
        // USI文字変換のround-trip検証（'1'～'9'）
        assert_eq!(File::from_usi('1'), Some(File::FILE_1));
        assert_eq!(File::from_usi('2'), Some(File::FILE_2));
        assert_eq!(File::from_usi('3'), Some(File::FILE_3));
        assert_eq!(File::from_usi('4'), Some(File::FILE_4));
        assert_eq!(File::from_usi('5'), Some(File::FILE_5));
        assert_eq!(File::from_usi('6'), Some(File::FILE_6));
        assert_eq!(File::from_usi('7'), Some(File::FILE_7));
        assert_eq!(File::from_usi('8'), Some(File::FILE_8));
        assert_eq!(File::from_usi('9'), Some(File::FILE_9));

        assert_eq!(File::from_usi('0'), None);
        assert_eq!(File::from_usi('a'), None);
        assert_eq!(File::from_usi(' '), None);
    }

    #[test]
    fn test_file_to_usi() {
        assert_eq!(File::FILE_1.to_usi(), '1');
        assert_eq!(File::FILE_2.to_usi(), '2');
        assert_eq!(File::FILE_3.to_usi(), '3');
        assert_eq!(File::FILE_4.to_usi(), '4');
        assert_eq!(File::FILE_5.to_usi(), '5');
        assert_eq!(File::FILE_6.to_usi(), '6');
        assert_eq!(File::FILE_7.to_usi(), '7');
        assert_eq!(File::FILE_8.to_usi(), '8');
        assert_eq!(File::FILE_9.to_usi(), '9');
    }

    #[test]
    fn test_file_usi_roundtrip() {
        for i in 1..=9 {
            let c = (b'0' + i) as char;
            let file = File::from_usi(c).unwrap();
            assert_eq!(file.to_usi(), c);
        }
    }

    #[test]
    fn test_file_display() {
        assert_eq!(File::FILE_1.to_string(), "1");
        assert_eq!(File::FILE_5.to_string(), "5");
        assert_eq!(File::FILE_9.to_string(), "9");
        assert_eq!(File(-1).to_string(), "Invalid(-1)");
        assert_eq!(File(9).to_string(), "Invalid(9)");
    }

    #[test]
    fn test_file_from_str() {
        assert_eq!(File::from_str("1").unwrap(), File::FILE_1);
        assert_eq!(File::from_str("5").unwrap(), File::FILE_5);
        assert_eq!(File::from_str("9").unwrap(), File::FILE_9);

        assert!(File::from_str("0").is_err());
        assert!(File::from_str("10").is_err());
        assert!(File::from_str("a").is_err());
        assert!(File::from_str("").is_err());
    }

    #[test]
    fn test_file_display_from_str_roundtrip() {
        // Display/FromStrのround-trip検証
        for i in 0..9 {
            let file = File::new(i);
            let str = file.to_string();
            assert_eq!(File::from_str(&str).unwrap(), file);
        }
    }

    #[test]
    fn test_file_is_ok() {
        // 境界値テスト（-1, 0, 8, 9でis_ok()を検証）
        assert!(!File(-1).is_ok());
        assert!(File(0).is_ok());
        assert!(File(4).is_ok());
        assert!(File(8).is_ok());
        assert!(!File(9).is_ok());
        assert!(!File(10).is_ok());
    }

    #[test]
    fn test_file_copy_clone() {
        let f = File::FILE_5;
        let f2 = f; // Copy
        assert_eq!(f, f2);

        #[allow(clippy::clone_on_copy)]
        let f3 = f.clone(); // Clone
        assert_eq!(f, f3);
    }
}
