from enum import Enum

# Paper Page Property
class PageSize(Enum):
    LETTER_PAGE_SIZE = (8.5, 11)
    LEGAL_PAGE_SIZE = (8.5, 14)
    TABLOID_PAGE_SIZE = (11, 17)
    LEDGER_PAGE_SIZE = (17, 11)
    A0_PAGE_SIZE = (33.1, 46.8)
    A1_PAGE_SIZE = (23.4, 33.1)
    A2_PAGE_SIZE = (16.5, 23.4)
    A3_PAGE_SIZE = (11.7, 16.5)
    A4_PAGE_SIZE = (8.27, 11.69)
    A5_PAGE_SIZE = (5.83, 8.27)
    A6_PAGE_SIZE = (4.13, 5.83)
    A7_PAGE_SIZE = (2.91, 4.13)
    A8_PAGE_SIZE = (2.07, 2.91)
    A9_PAGE_SIZE = (1.46, 2.07)
    A10_PAGE_SIZE = (1.02, 1.46)


# Margin Property
class Margin(Enum):
    TOP_MARGIN = 0
    BOTTOM_MARGIN = 0
    LEFT_MARGIN = 0
    RIGHT_MARGIN = 0