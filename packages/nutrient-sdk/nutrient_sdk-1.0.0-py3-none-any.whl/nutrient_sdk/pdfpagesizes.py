"""
Specifies page sizes.
"""

from enum import Enum, auto
import ctypes

class PdfPageSizes(Enum):
    """Specifies page sizes.."""
    
    PDF_PAGE_SIZE_LETTER = 1
    # US Letter 8 1/2 x 11 in
    
    PDF_PAGE_SIZE_LETTER_SMALL = 2
    # US Letter Small 8 1/2 x 11 in
    
    PDF_PAGE_SIZE_TABLOID = 3
    # Tabloid 11 x 17 in
    
    PDF_PAGE_SIZE_LEDGER = 4
    # US Ledger 17 x 11 in
    
    PDF_PAGE_SIZE_LEGAL = 5
    # US Legal 8 1/2 x 14 in
    
    PDF_PAGE_SIZE_STATEMENT = 6
    # US Statement 5 1/2 x 8 1/2 in
    
    PDF_PAGE_SIZE_EXECUTIVE = 7
    # US Executive 7 1/4 x 10 1/2 in
    
    PDF_PAGE_SIZE_A3 = 8
    # A3 297 x 420 mm
    
    PDF_PAGE_SIZE_A4 = 9
    # A4 210 x 297 mm
    
    PDF_PAGE_SIZE_A4_SMALL = 10
    # A4 Small 210 x 297 mm
    
    PDF_PAGE_SIZE_A5 = 11
    # A5 148 x 210 mm
    
    PDF_PAGE_SIZE_B4 = 12
    # B4 (JIS) 257 x 364 mm
    
    PDF_PAGE_SIZE_B5 = 13
    # B5 (JIS) 182 x 257 mm
    
    PDF_PAGE_SIZE_FOLIO = 14
    # Folio 8 1/2 x 13 in
    
    PDF_PAGE_SIZE_QUARTO = 15
    # Quarto 215 x 275 mm
    
    PDF_PAGE_SIZE10_X14 = 16
    # 10 x 14 in
    
    PDF_PAGE_SIZE11_X17 = 17
    # 11 x 17 in
    
    PDF_PAGE_SIZE_NOTE = 18
    # US Note 8 1/2 x 11 in
    
    PDF_PAGE_SIZE_ENV_9 = 19
    # US Envelope #9 3 7/8 x 8 7/8
    
    PDF_PAGE_SIZE_ENV_10 = 20
    # US Envelope #10 4 1/8 x 9 1/2
    
    PDF_PAGE_SIZE_ENV_11 = 21
    # US Envelope #11 4 1/2 x 10 3/8
    
    PDF_PAGE_SIZE_ENV_12 = 22
    # US Envelope #12 4 3/4 x 11 in
    
    PDF_PAGE_SIZE_ENV_14 = 23
    # US Envelope #14 5 x 11 1/2
    
    PDF_PAGE_SIZE_CSHEET = 24
    # C size sheet 43.18 x 55.88 cm
    
    PDF_PAGE_SIZE_DSHEET = 25
    # D size sheet 55.88 x 86.36
    
    PDF_PAGE_SIZE_ESHEET = 26
    # E size sheet 86.36 x 111.76
    
    PDF_PAGE_SIZE_ENV_DL = 27
    # Envelope DL 110 x 220mm
    
    PDF_PAGE_SIZE_ENV_C5 = 28
    # Envelope C5 162 x 229 mm
    
    PDF_PAGE_SIZE_ENV_C3 = 29
    # Envelope C3 324 x 458 mm
    
    PDF_PAGE_SIZE_ENV_C4 = 30
    # Envelope C4 229 x 324 mm
    
    PDF_PAGE_SIZE_ENV_C6 = 31
    # Envelope C6 114 x 162 mm
    
    PDF_PAGE_SIZE_ENV_C65 = 32
    # Envelope C65 114 x 229 mm
    
    PDF_PAGE_SIZE_ENV_B4 = 33
    # Envelope B4 250 x 353 mm
    
    PDF_PAGE_SIZE_ENV_B5 = 34
    # Envelope B5 176 x 250 mm
    
    PDF_PAGE_SIZE_ENV_B6 = 35
    # Envelope B6 176 x 125 mm
    
    PDF_PAGE_SIZE_ENV_ITALY = 36
    # Envelope 110 x 230 mm
    
    PDF_PAGE_SIZE_ENV_MONARCH = 37
    # US Envelope Monarch 3.875 x 7.5 in
    
    PDF_PAGE_SIZE_ENV_PERSONAL = 38
    # 6 3/4 US Envelope 3 5/8 x 6 1/2 in
    
    PDF_PAGE_SIZE_FAN_FOLD_US = 39
    # US Std Fanfold 14 7/8 x 11 in
    
    PDF_PAGE_SIZE_FAN_FOLD_STD_GERMAN = 40
    # German Std Fanfold 8 1/2 x 12 in
    
    PDF_PAGE_SIZE_FAN_FOLD_LGL_GERMAN = 41
    # German Legal Fanfold 8 1/2 x 13 in
    
    PDF_PAGE_SIZE_ISO_B4 = 42
    # B4 (ISO) 250 x 353 mm
    
    PDF_PAGE_SIZE_JAPANESE_POSTCARD = 43
    # Japanese Postcard 100 x 148 mm
    
    PDF_PAGE_SIZE9_X11 = 44
    # 9 x 11 in
    
    PDF_PAGE_SIZE10_X11 = 45
    # 10 x 11 in
    
    PDF_PAGE_SIZE15_X11 = 46
    # 15 x 11 in
    
    PDF_PAGE_SIZE_ENV_INVITE = 47
    # Envelope Invite 220 x 220 mm
    
    PDF_PAGE_SIZE_LETTER_EXTRA = 50
    # US Letter Extra 9 1/2 x 12 in
    
    PDF_PAGE_SIZE_LEGAL_EXTRA = 51
    # US Legal Extra 9 1/2 x 15 in
    
    PDF_PAGE_SIZE_TABLOID_EXTRA = 52
    # US Tabloid Extra 11.69 x 18 in
    
    PDF_PAGE_SIZE_A4_EXTRA = 53
    # A4 Extra 9.27 x 12.69 in
    
    PDF_PAGE_SIZE_LETTER_TRANSVERSE = 54
    # Letter Transverse 8 1/2 x 11 in
    
    PDF_PAGE_SIZE_A4_TRANSVERSE = 55
    # A4 Transverse 210 x 297 mm
    
    PDF_PAGE_SIZE_LETTER_EXTRA_TRANSVERSE = 56
    # Letter Extra Transverse 9 1/2 x 12 in
    
    PDF_PAGE_SIZE_A_PLUS = 57
    # SuperA/SuperA/A4 227 x 356 mm
    
    PDF_PAGE_SIZE_B_PLUS = 58
    # SuperB/SuperB/A3 305 x 487 mm
    
    PDF_PAGE_SIZE_LETTER_PLUS = 59
    # US Letter Plus 8.5 x 12.69 in
    
    PDF_PAGE_SIZE_A4_PLUS = 60
    # A4 Plus 210 x 330 mm
    
    PDF_PAGE_SIZE_A5_TRANSVERSE = 61
    # A5 Transverse 148 x 210 mm
    
    PDF_PAGE_SIZE_B5_TRANSVERSE = 62
    # B5 (JIS) Transverse 182 x 257 mm
    
    PDF_PAGE_SIZE_A3_EXTRA = 63
    # A3 Extra 322 x 445 mm
    
    PDF_PAGE_SIZE_A5_EXTRA = 64
    # A5 Extra 174 x 235 mm
    
    PDF_PAGE_SIZE_B5_EXTRA = 65
    # B5 (ISO) Extra 201 x 276 mm
    
    PDF_PAGE_SIZE_A2 = 66
    # A2 420 x 594 mm
    
    PDF_PAGE_SIZE_A3_TRANSVERSE = 67
    # A3 Transverse 297 x 420 mm
    
    PDF_PAGE_SIZE_A3_EXTRA_TRANSVERSE = 68
    # A3 Extra Transverse 322 x 445 mm
    
    PDF_PAGE_SIZE_DBL_JAPANESE_POSTCARD = 69
    # Japanese Double Postcard 200 x 148 mm
    
    PDF_PAGE_SIZE_A6 = 70
    # A6 105 x 148 mm
    
    PDF_PAGE_SIZE_JENV_KAKU2 = 71
    # Japanese Envelope Kaku #2 240 x 332 mm
    
    PDF_PAGE_SIZE_JENV_KAKU3 = 72
    # Japanese Envelope Kaku #3 9 x 324 mm
    
    PDF_PAGE_SIZE_JENV_CHOU3 = 73
    # Japanese Envelope Chou #3 120 x 235 mm
    
    PDF_PAGE_SIZE_JENV_CHOU4 = 74
    # Japanese Envelope Chou #4 90 x 205 mm
    
    PDF_PAGE_SIZE_LETTER_ROTATED = 75
    # Letter Rotated 11 x 8 1/2 11 in
    
    PDF_PAGE_SIZE_A3_ROTATED = 76
    # A3 Rotated 420 x 297 mm
    
    PDF_PAGE_SIZE_A4_ROTATED = 77
    # A4 Rotated 297 x 210 mm
    
    PDF_PAGE_SIZE_A5_ROTATED = 78
    # A5 Rotated 210 x 148 mm
    
    PDF_PAGE_SIZE_B4_JIS_ROTATED = 79
    # B4 (JIS) Rotated 364 x 257 mm
    
    PDF_PAGE_SIZE_B5_JIS_ROTATED = 80
    # B5 (JIS) Rotated 257 x 182 mm
    
    PDF_PAGE_SIZE_JAPANESE_POSTCARD_ROTATED = 81
    # Japanese Postcard Rotated 148 x 100 mm
    
    PDF_PAGE_SIZE_DBL_JAPANESE_POSTCARD_ROTATED = 82
    # Double Japanese Postcard Rotated 148 x 200 mm
    
    PDF_PAGE_SIZE_A6_ROTATED = 83
    # A6 Rotated 148 x 105 mm
    
    PDF_PAGE_SIZE_JENV_KAKU2_ROTATED = 84
    # Japanese Envelope Kaku #2 Rotated 332 x 240 mm
    
    PDF_PAGE_SIZE_JENV_KAKU3_ROTATED = 85
    # Japanese Envelope Kaku #3 Rotated 277 x 216 mm
    
    PDF_PAGE_SIZE_JENV_CHOU3_ROTATED = 86
    # Japanese Envelope Chou #3 Rotated 235 x 120 mm
    
    PDF_PAGE_SIZE_JENV_CHOU4_ROTATED = 87
    # Japanese Envelope Chou #4 Rotated 205 x 90 mm
    
    PDF_PAGE_SIZE_B6_JIS = 88
    # B6 (JIS) 128 x 182 mm
    
    PDF_PAGE_SIZE_B6_JIS_ROTATED = 89
    # B6 (JIS) Rotated 182 x 128 mm
    
    PDF_PAGE_SIZE12_X11 = 90
    # 12 x 11 in
    
    PDF_PAGE_SIZE_JENV_YOU4 = 91
    # Japanese Envelope You #4 235 x 105 mm
    
    PDF_PAGE_SIZE_JENV_YOU4_ROTATED = 92
    # Japanese Envelope You #4 Rotated 105 x 235 mm
    
    PDF_PAGE_SIZE_P16_K = 93
    # PRC 16K 146 x 215 mm
    
    PDF_PAGE_SIZE_P32_K = 94
    # PRC 32K 97 x 151 mm
    
    PDF_PAGE_SIZE_P32_KBIG = 95
    # PRC 32K(Big) 97 x 151 mm
    
    PDF_PAGE_SIZE_PENV_1 = 96
    # PRC Envelope #1 102 x 165 mm
    
    PDF_PAGE_SIZE_PENV_2 = 97
    # PRC Envelope #2 102 x 176 mm
    
    PDF_PAGE_SIZE_PENV_3 = 98
    # PRC Envelope #3 125 x 176 mm
    
    PDF_PAGE_SIZE_PENV_4 = 99
    # PRC Envelope #4 110 x 208 mm
    
    PDF_PAGE_SIZE_PENV_5 = 100
    # PRC Envelope #5 110 x 220 mm
    
    PDF_PAGE_SIZE_PENV_6 = 101
    # PRC Envelope #6 120 x 230 mm
    
    PDF_PAGE_SIZE_PENV_7 = 102
    # PRC Envelope #7 160 x 230 mm
    
    PDF_PAGE_SIZE_PENV_8 = 103
    # PRC Envelope #8 120 x 309 mm
    
    PDF_PAGE_SIZE_PENV_9 = 104
    # PRC Envelope #9 229 x 324 mm
    
    PDF_PAGE_SIZE_PENV_10 = 105
    # PRC Envelope #10 324 x 458 mm
    
    PDF_PAGE_SIZE_P16_K_ROTATED = 106
    # PRC 16K Rotated
    
    PDF_PAGE_SIZE_P32_K_ROTATED = 107
    # PRC 32K Rotated
    
    PDF_PAGE_SIZE_P32_KBIG_ROTATED = 108
    # PRC 32K(Big) Rotated
    
    PDF_PAGE_SIZE_PENV_1_ROTATED = 109
    # PRC Envelope #1 Rotated 165 x 102 mm
    
    PDF_PAGE_SIZE_PENV_2_ROTATED = 110
    # PRC Envelope #2 Rotated 176 x 102 mm
    
    PDF_PAGE_SIZE_PENV_3_ROTATED = 111
    # PRC Envelope #3 Rotated 176 x 125 mm
    
    PDF_PAGE_SIZE_PENV_4_ROTATED = 112
    # PRC Envelope #4 Rotated 208 x 110 mm
    
    PDF_PAGE_SIZE_PENV_5_ROTATED = 113
    # PRC Envelope #5 Rotated 220 x 110 mm
    
    PDF_PAGE_SIZE_PENV_6_ROTATED = 114
    # PRC Envelope #6 Rotated 230 x 120 mm
    
    PDF_PAGE_SIZE_PENV_7_ROTATED = 115
    # PRC Envelope #7 Rotated 230 x 160 mm
    
    PDF_PAGE_SIZE_PENV_8_ROTATED = 116
    # PRC Envelope #8 Rotated 309 x 120 mm
    
    PDF_PAGE_SIZE_PENV_9_ROTATED = 117
    # PRC Envelope #9 Rotated 324 x 229 mm
    
    PDF_PAGE_SIZE_PENV_10_ROTATED = 118
    # PRC Envelope #10 Rotated 458 x 324 mm
    
    
    @classmethod
    def from_value(cls, value: int) -> 'PdfPageSizes':
        """
        Create an enum instance from an integer value.
        
        Args:
            value: The integer value to convert
            
        Returns:
            The corresponding PdfPageSizes instance
            
        Raises:
            ValueError: If the value doesn't correspond to a valid enum member
        """
        for member in cls:
            if member.value == value:
                return member
        raise ValueError(f"Invalid {cls.__name__} value: {value}")
    
    def to_ctype(self) -> ctypes.c_int:
        """
        Convert to ctypes representation for native calls.
        
        Returns:
            ctypes.c_int: The enum value as a ctypes integer
        """
        return ctypes.c_int(self.value)
    
    def __str__(self) -> str:
        """String representation of the enum value."""
        return f"{self.__class__.__name__}.{self.name}"
    
    def __repr__(self) -> str:
        """Detailed representation of the enum value."""
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"

__all__ = ['PdfPageSizes']

