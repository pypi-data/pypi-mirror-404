use std::convert::TryFrom;
use std::fmt;
use std::str::FromStr;

use super::Color;

/// 段を表す型（1段～9段、内部的には0～8）
#[repr(transparent)]
#[derive(Debug, Copy, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct Rank(pub i8);

impl Rank {
    // 関連定数（YaneuraOu互換）
    /// ゼロ値（`Rank::RANK_1` と同じ）
    pub const RANK_ZERO: Self = Self(0);
    /// 1段
    pub const RANK_1: Self = Self(0);
    /// 2段
    pub const RANK_2: Self = Self(1);
    /// 3段
    pub const RANK_3: Self = Self(2);
    /// 4段
    pub const RANK_4: Self = Self(3);
    /// 5段
    pub const RANK_5: Self = Self(4);
    /// 6段
    pub const RANK_6: Self = Self(5);
    /// 7段
    pub const RANK_7: Self = Self(6);
    /// 8段
    pub const RANK_8: Self = Self(7);
    /// 9段
    pub const RANK_9: Self = Self(8);
    /// 段の総数
    pub const RANK_NB: usize = 9;

    /// USI文字（'a'～'i'）からRankを生成する
    #[inline]
    #[must_use]
    pub const fn from_usi(c: char) -> Option<Self> {
        match c {
            'a' => Some(Self::RANK_1),
            'b' => Some(Self::RANK_2),
            'c' => Some(Self::RANK_3),
            'd' => Some(Self::RANK_4),
            'e' => Some(Self::RANK_5),
            'f' => Some(Self::RANK_6),
            'g' => Some(Self::RANK_7),
            'h' => Some(Self::RANK_8),
            'i' => Some(Self::RANK_9),
            _ => None,
        }
    }

    /// USI文字（'a'～'i'）に変換する
    #[inline]
    #[must_use]
    pub fn to_usi(self) -> char {
        debug_assert!(self.is_ok(), "Invalid rank: {self:?}");
        let offset = u8::try_from(self.0).expect("rank index should be non-negative");
        char::from(b'a' + offset)
    }

    /// 有効な値かどうかを判定する
    #[inline]
    #[must_use]
    pub const fn is_ok(self) -> bool {
        self.0 >= Self::RANK_1.raw() && self.0 <= Self::RANK_9.raw()
    }

    /// 内部値からRankを生成する（クレート内部用）
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

/// 移動元/移動先が成りゾーンかを判定（YaneuraOu互換）
#[inline]
#[must_use]
pub const fn can_promote(color: Color, rank: Rank) -> bool {
    let color_raw = match color.raw() {
        0 => 0u32,
        1 => 1u32,
        _ => return false,
    };
    let rank_raw = match rank.raw() {
        0 => 0u32,
        1 => 1u32,
        2 => 2u32,
        3 => 3u32,
        4 => 4u32,
        5 => 5u32,
        6 => 6u32,
        7 => 7u32,
        8 => 8u32,
        _ => return false,
    };
    (0x01c0_0007u32 & (1u32 << ((color_raw << 4) + rank_raw))) != 0
}

impl fmt::Display for Rank {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        if self.is_ok() {
            write!(f, "{}", self.to_usi())
        } else {
            write!(f, "Invalid({})", self.0)
        }
    }
}

impl FromStr for Rank {
    type Err = String;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        if s.len() != 1 {
            return Err(format!("Invalid rank string: {s}"));
        }
        Self::from_usi(s.chars().next().unwrap()).ok_or_else(|| format!("Invalid rank string: {s}"))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_rank_constants() {
        // 定数値検証（Rank::RANK_1=0, Rank::RANK_9=8, Rank::RANK_NB=9）
        assert_eq!(Rank::RANK_ZERO.raw(), 0);
        assert_eq!(Rank::RANK_1.raw(), 0);
        assert_eq!(Rank::RANK_2.raw(), 1);
        assert_eq!(Rank::RANK_3.raw(), 2);
        assert_eq!(Rank::RANK_4.raw(), 3);
        assert_eq!(Rank::RANK_5.raw(), 4);
        assert_eq!(Rank::RANK_6.raw(), 5);
        assert_eq!(Rank::RANK_7.raw(), 6);
        assert_eq!(Rank::RANK_8.raw(), 7);
        assert_eq!(Rank::RANK_9.raw(), 8);
        assert_eq!(Rank::RANK_NB, 9);
    }

    #[test]
    fn test_rank_usi_conversion() {
        // USI文字変換のround-trip検証（'a'～'i'）
        assert_eq!(Rank::from_usi('a'), Some(Rank::RANK_1));
        assert_eq!(Rank::from_usi('b'), Some(Rank::RANK_2));
        assert_eq!(Rank::from_usi('c'), Some(Rank::RANK_3));
        assert_eq!(Rank::from_usi('d'), Some(Rank::RANK_4));
        assert_eq!(Rank::from_usi('e'), Some(Rank::RANK_5));
        assert_eq!(Rank::from_usi('f'), Some(Rank::RANK_6));
        assert_eq!(Rank::from_usi('g'), Some(Rank::RANK_7));
        assert_eq!(Rank::from_usi('h'), Some(Rank::RANK_8));
        assert_eq!(Rank::from_usi('i'), Some(Rank::RANK_9));

        assert_eq!(Rank::from_usi('j'), None);
        assert_eq!(Rank::from_usi('1'), None);
        assert_eq!(Rank::from_usi(' '), None);
    }

    #[test]
    fn test_rank_to_usi() {
        assert_eq!(Rank::RANK_1.to_usi(), 'a');
        assert_eq!(Rank::RANK_2.to_usi(), 'b');
        assert_eq!(Rank::RANK_3.to_usi(), 'c');
        assert_eq!(Rank::RANK_4.to_usi(), 'd');
        assert_eq!(Rank::RANK_5.to_usi(), 'e');
        assert_eq!(Rank::RANK_6.to_usi(), 'f');
        assert_eq!(Rank::RANK_7.to_usi(), 'g');
        assert_eq!(Rank::RANK_8.to_usi(), 'h');
        assert_eq!(Rank::RANK_9.to_usi(), 'i');
    }

    #[test]
    fn test_rank_usi_roundtrip() {
        for i in 0..9 {
            let c = (b'a' + i) as char;
            let rank = Rank::from_usi(c).unwrap();
            assert_eq!(rank.to_usi(), c);
        }
    }

    #[test]
    fn test_rank_display() {
        assert_eq!(Rank::RANK_1.to_string(), "a");
        assert_eq!(Rank::RANK_5.to_string(), "e");
        assert_eq!(Rank::RANK_9.to_string(), "i");
        assert_eq!(Rank(-1).to_string(), "Invalid(-1)");
        assert_eq!(Rank(9).to_string(), "Invalid(9)");
    }

    #[test]
    fn test_rank_from_str() {
        assert_eq!(Rank::from_str("a").unwrap(), Rank::RANK_1);
        assert_eq!(Rank::from_str("e").unwrap(), Rank::RANK_5);
        assert_eq!(Rank::from_str("i").unwrap(), Rank::RANK_9);

        assert!(Rank::from_str("j").is_err());
        assert!(Rank::from_str("1").is_err());
        assert!(Rank::from_str("").is_err());
        assert!(Rank::from_str("ab").is_err());
    }

    #[test]
    fn test_rank_display_from_str_roundtrip() {
        // Display/FromStrのround-trip検証
        for i in 0..9 {
            let rank = Rank::new(i);
            let str = rank.to_string();
            assert_eq!(Rank::from_str(&str).unwrap(), rank);
        }
    }

    #[test]
    fn test_rank_is_ok() {
        // 境界値テスト（-1, 0, 8, 9でis_ok()を検証）
        assert!(!Rank(-1).is_ok());
        assert!(Rank(0).is_ok());
        assert!(Rank(4).is_ok());
        assert!(Rank(8).is_ok());
        assert!(!Rank(9).is_ok());
        assert!(!Rank(10).is_ok());
    }

    #[test]
    fn test_rank_copy_clone() {
        let r = Rank::RANK_5;
        let r2 = r; // Copy
        assert_eq!(r, r2);

        #[allow(clippy::clone_on_copy)]
        let r3 = r.clone(); // Clone
        assert_eq!(r, r3);
    }

    #[test]
    fn test_can_promote() {
        for rank in [
            Rank::RANK_1,
            Rank::RANK_2,
            Rank::RANK_3,
            Rank::RANK_4,
            Rank::RANK_5,
            Rank::RANK_6,
            Rank::RANK_7,
            Rank::RANK_8,
            Rank::RANK_9,
        ] {
            let black = can_promote(Color::BLACK, rank);
            let white = can_promote(Color::WHITE, rank);
            assert_eq!(black, rank <= Rank::RANK_3);
            assert_eq!(white, rank >= Rank::RANK_7);
        }
        assert!(!can_promote(Color::new(-1), Rank::RANK_1));
        assert!(!can_promote(Color::BLACK, Rank::new(-1)));
        assert!(!can_promote(Color::BLACK, Rank::new(9)));
    }
}
