#!/usr/bin/env python3
"""把修改版 PDF 中的真实手写电压数据贴回原始扫描页。

原始 PDF 和修改版 PDF 都不会被覆盖。
"""

from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parent
ORIGINAL = ROOT / "直流电桥的应用数据.pdf"
REVISED = ROOT / "直流电桥的应用数据修改版.pdf"
OUT_PNG = ROOT / "直流电桥的应用数据-手写校正更正版.png"
OUT_PDF = ROOT / "直流电桥的应用数据-手写校正更正版.pdf"


def render_first_page(pdf: Path, out_prefix: Path) -> Image.Image:
    subprocess.run(
        ["pdftoppm", "-f", "1", "-singlefile", "-r", "180", "-png", str(pdf), str(out_prefix)],
        check=True,
    )
    return Image.open(out_prefix.with_suffix(".png")).convert("RGB")


def ink_alpha(crop: Image.Image) -> Image.Image:
    """以扫描灰度生成透明度，保留真实笔画边缘和浓淡。"""
    gray = np.asarray(crop.convert("L"), dtype=np.int16)
    alpha = np.clip((242 - gray) * 1.28, 0, 255).astype(np.uint8)
    alpha[alpha < 10] = 0
    return Image.fromarray(alpha, mode="L")


def tight_ink_crop(source: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, Image.Image]:
    crop = source.crop(box)
    alpha = ink_alpha(crop)
    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError(f"在区域 {box} 中未找到手写笔画")
    pad = 7
    x0 = max(0, bbox[0] - pad)
    y0 = max(0, bbox[1] - pad)
    x1 = min(crop.width, bbox[2] + pad)
    y1 = min(crop.height, bbox[3] + pad)
    return crop.crop((x0, y0, x1, y1)), alpha.crop((x0, y0, x1, y1))


def join_ink_pieces(
    source: Image.Image, boxes: list[tuple[int, int, int, int]], gap: int = 7
) -> tuple[Image.Image, Image.Image]:
    """将同一份修改版中的真实手写笔画按基线拼合。"""
    pieces = [tight_ink_crop(source, box) for box in boxes]
    width = sum(piece.width for piece, _ in pieces) + gap * (len(pieces) - 1)
    height = max(piece.height for piece, _ in pieces)
    rgb = Image.new("RGB", (width, height), (255, 255, 255))
    alpha = Image.new("L", (width, height), 0)
    x = 0
    for piece, piece_alpha in pieces:
        y = height - piece.height
        rgb.paste(piece, (x, y), piece_alpha)
        alpha.paste(piece_alpha, (x, y), piece_alpha)
        x += piece.width + gap
    return rgb, alpha


def erase_old_ink(page: Image.Image, box: tuple[int, int, int, int]) -> None:
    """只清除旧数字的笔画，尽量保留周围扫描底色。"""
    crop = page.crop(box)
    gray = np.asarray(crop.convert("L"), dtype=np.int16)
    mask = np.clip((225 - gray) * 2.4, 0, 255).astype(np.uint8)
    mask[mask < 8] = 0
    mask_img = Image.fromarray(mask, mode="L").filter(ImageFilter.MaxFilter(11)).filter(
        ImageFilter.GaussianBlur(2.2)
    )

    arr = np.asarray(crop)
    light = arr[arr.mean(axis=2) > 238]
    paper = tuple(np.median(light, axis=0).astype(np.uint8)) if len(light) else (252, 252, 252)
    clean = Image.new("RGB", crop.size, paper)
    page.paste(clean, box[:2], mask_img)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bridge-handwriting-") as tmp:
        tmpdir = Path(tmp)
        original = render_first_page(ORIGINAL, tmpdir / "original")
        revised = render_first_page(REVISED, tmpdir / "revised")

        # 修改版为竖向存储，顺时针旋转后与原扫描页方向一致。
        revised = revised.transpose(Image.Transpose.ROTATE_90)

        # 每个区域只包含修改版中下排的新手写值。后三组顶边下移，
        # 用于避开上排旧数字较长的 7 笔画。
        source_boxes = [
            (1510, 4275, 1810, 4410),  # 33.5
            (2215, 4265, 2510, 4440),  # 39.6
            (2940, 4270, 3245, 4440),  # 45.3
            (3720, 4280, 4020, 4430),  # 51.1
            (4280, 4290, 4645, 4470),  # 56.8
            (4800, 4320, 5095, 4480),  # 62.7
            (5220, 4325, 5520, 4490),  # 68.3
            (5760, 4335, 6070, 4525),  # 74.2
        ]

        # 原页旧数字的紧包围区域。
        old_boxes = [
            (1538, 4185, 1810, 4475),
            (2225, 4205, 2570, 4440),
            (2928, 4235, 3350, 4475),
            (3785, 4240, 4120, 4410),
            (4430, 4250, 4710, 4430),
            (4880, 4230, 5210, 4485),
            (5325, 4235, 5635, 4455),
            (5880, 4235, 6195, 4460),
        ]
        centers_x = [1675, 2399, 3139, 3951, 4569, 5044, 5481, 6038]
        baselines_y = [4445, 4445, 4445, 4445, 4445, 4450, 4450, 4455]

        for old_box in old_boxes:
            erase_old_ink(original, old_box)

        # 根据各组在修改版中的实际书写大小分别调整，使它们与原页 U/mV 行匹配。
        scales = [1.35, 1.15, 1.15, 1.25, 1.12, 1.15, 1.15, 1.05]
        for index, (source_box, center_x, baseline_y, scale) in enumerate(
            zip(source_boxes, centers_x, baselines_y, scales)
        ):
            if index == 5:
                # 修改版的“62.7”与上排“67.0”的长竖笔相接。“6”和“2”
                # 分别从同一修改行的“39.6”和“74.2”直接取得，再与原“.7”拼合。
                ink, alpha = join_ink_pieces(
                    revised,
                    [
                        (2410, 4268, 2495, 4405),
                        (5960, 4350, 6055, 4475),
                        (4975, 4330, 5085, 4480),
                    ],
                    gap=5,
                )
            else:
                ink, alpha = tight_ink_crop(revised, source_box)
            new_size = (round(ink.width * scale), round(ink.height * scale))
            ink = ink.resize(new_size, Image.Resampling.LANCZOS)
            alpha = alpha.resize(new_size, Image.Resampling.LANCZOS)
            x = round(center_x - ink.width / 2)
            y = baseline_y - ink.height
            original.paste(ink, (x, y), alpha)

        original.save(OUT_PNG, quality=96)
        original.save(OUT_PDF, "PDF", resolution=180.0)
        print(OUT_PNG)
        print(OUT_PDF)


if __name__ == "__main__":
    main()
