"""Color configuration for game rendering."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ColorConfig:
    """RGB color definitions for game elements."""

    background: tuple[int, int, int] = (25, 28, 26)
    border: tuple[int, int, int] = (113, 121, 113)
    invalid: tuple[int, int, int] = (186, 26, 26)
    asteroid: tuple[int, int, int] = (50, 56, 52)
    food: tuple[int, int, int] = (251, 253, 248)
    snek_options: list[tuple[int, int, int]] = field(
        default_factory=lambda: [
            (222, 97, 116),
            (221, 65, 82),
            (223, 83, 51),
            (215, 117, 85),
            (231, 131, 31),
            (192, 123, 49),
            (194, 141, 80),
            (203, 149, 43),
            (223, 187, 36),
            (212, 189, 95),
            (150, 135, 41),
            (134, 124, 51),
            (186, 182, 59),
            (190, 190, 111),
            (174, 202, 41),
            (21, 149, 43),
            (54, 198, 76),
            (15, 145, 62),
            (124, 197, 56),
            (141, 197, 105),
            (63, 146, 47),
            (83, 188, 69),
            (128, 194, 121),
            (79, 201, 101),
            (60, 139, 73),
            (72, 208, 129),
            (78, 187, 130),
            (67, 194, 158),
            (54, 222, 230),
            (102, 161, 229),
            (92, 138, 228),
            (87, 127, 240),
            (121, 130, 206),
            (131, 106, 238),
            (159, 121, 219),
            (194, 134, 210),
            (192, 100, 217),
            (217, 69, 194),
            (212, 91, 184),
            (215, 122, 182),
            (222, 85, 144),
        ]
    )
