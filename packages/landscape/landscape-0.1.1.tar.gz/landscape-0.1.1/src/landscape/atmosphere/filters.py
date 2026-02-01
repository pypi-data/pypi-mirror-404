from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Callable, TypedDict

from landscape.utils import RGB, Colormap, lerp_color, noise_2d, rand_choice


class FilterContext(TypedDict):
    x: int
    y: int
    z: float
    ny: float
    depth_fraction: float
    seed: int


Cell = tuple[str, RGB, RGB]


class CellFilter(ABC):
    @abstractmethod
    def apply(self, cell: Cell, ctx: FilterContext) -> Cell: ...


@dataclass
class HazeFilter(CellFilter):
    color_map: Colormap
    power: float
    intensity: float

    def apply(self, cell: Cell, ctx: FilterContext) -> Cell:
        char, fg, bg = cell
        hf = (ctx["depth_fraction"] ** self.power) * self.intensity
        if hf > 0:
            haze_color = self.color_map.val(ctx["ny"])
            fg = lerp_color(fg, haze_color, hf)
            bg = lerp_color(bg, haze_color, hf)
        return char, fg, bg


@dataclass
class ColorGradeFilter(CellFilter):
    """Post-process colors: brightness, warmth, blue shift, season tint."""

    processor: Callable[[float, float, float, RGB], RGB]

    def apply(self, cell: Cell, ctx: FilterContext) -> Cell:
        char, fg, bg = cell
        fg = self.processor(ctx["x"], ctx["z"], ctx["ny"], fg)
        bg = self.processor(ctx["x"], ctx["z"], ctx["ny"], bg)
        return char, fg, bg


@dataclass
class PrecipitationFilter(CellFilter):
    chars: str
    color: RGB
    density: float

    def apply(self, cell: Cell, ctx: FilterContext) -> Cell:
        char, fg, bg = cell
        x, y, z, ny, seed = ctx["x"], ctx["y"], ctx["z"], ctx["ny"], ctx["seed"]

        pc = noise_2d(x * 500, z * 500 + ny * 500, seed)
        density = self.density
        replace_char = pc <= (0.5 * density if char == " " else density)
        if not replace_char:
            return char, fg, bg

        p = noise_2d(z + x * 0.1, z + ny, seed)
        new_char = rand_choice(self.chars, seed + x + y * 57)
        return new_char, lerp_color(self.color, fg, p), bg


@dataclass
class FilterPipeline:
    filters: list[CellFilter]

    def apply(self, cell: Cell, ctx: FilterContext) -> Cell:
        for f in self.filters:
            cell = f.apply(cell, ctx)
        return cell
