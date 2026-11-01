#!/usr/bin/env python3
"""将「直流电桥的应用数据.pdf」中 R3 = 55.0 Ω 改为 50.0 Ω。

仅修改第二个手写数字 5：先用周围纸面底色清除，再从同页的
手写数字中取一个 0 贴回原位。原 PDF 保持不变。
"""

from pathlib import Path
import subprocess
import tempfile

import numpy as np
from PIL import Image, ImageFilter


ROOT = Path(__file__).resolve().parent
SOURCE_PDF = ROOT / "直流电桥的应用数据.pdf"
OUTPUT_PDF = ROOT / "直流电桥的应用数据-R3修正.pdf"
OUTPUT_JPG = ROOT / "直流电桥的应用数据-R3修正.jpg"


def extract_page_image(pdf: Path, tmpdir: Path) -> Image.Image:
    prefix = tmpdir / "page"
    subprocess.run(["pdfimages", "-f", "1", "-l", "1", "-j", str(pdf), str(prefix)], check=True)
    images = sorted(tmpdir.glob("page-*.jpg"))
    if len(images) != 1:
        raise RuntimeError(f"预期只有一张 JPEG 页图，实际为 {images}")
    return Image.open(images[0]).convert("RGB")


def ink_mask(crop: Image.Image, threshold: int = 224) -> Image.Image:
    gray = np.asarray(crop.convert("L"), dtype=np.int16)
    alpha = np.clip((threshold - gray) * 3.2, 0, 255).astype(np.uint8)
    alpha[alpha < 8] = 0
    return Image.fromarray(alpha, mode="L")


def tight_ink(source: Image.Image, box: tuple[int, int, int, int]) -> tuple[Image.Image, Image.Image]:
    crop = source.crop(box)
    alpha = ink_mask(crop)
    bbox = alpha.getbbox()
    if bbox is None:
        raise RuntimeError(f"区域 {box} 中未找到笔迹")
    pad = 3
    bbox = (
        max(0, bbox[0] - pad),
        max(0, bbox[1] - pad),
        min(crop.width, bbox[2] + pad),
        min(crop.height, bbox[3] + pad),
    )
    return crop.crop(bbox), alpha.crop(bbox)


def erase_ink(page: Image.Image, box: tuple[int, int, int, int]) -> None:
    crop = page.crop(box)
    mask = ink_mask(crop).filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(1.6))

    # 取目标四周的局部纸面中位色，不使用纯白色块。
    margin = page.crop((box[0] - 35, box[1] - 35, box[2] + 35, box[3] + 35))
    arr = np.asarray(margin)
    light = arr[arr.mean(axis=2) > 238]
    paper = tuple(np.median(light, axis=0).astype(np.uint8)) if len(light) else (251, 251, 251)
    page.paste(Image.new("RGB", crop.size, paper), box[:2], mask)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="bridge-r3-") as tmp:
        page = extract_page_image(SOURCE_PDF, Path(tmp))

        # R3 = 55.0 Ω 中第二个 5（原图像素坐标）。
        target_box = (2528, 3462, 2598, 3595)

        # 同一行 R3 数值小数点后的 0，书写工具、颜色和纸面完全一致。
        source_box = (2648, 3488, 2725, 3585)
        zero, zero_alpha = tight_ink(page, source_box)

        erase_ink(page, target_box)

        # 直接使用这个原有 0 的大小，不改变笔迹粗细。
        center_x = (target_box[0] + target_box[2]) // 2
        baseline_y = 3585
        pos = (round(center_x - zero.width / 2), baseline_y - zero.height)
        page.paste(zero, pos, zero_alpha)

        page.save(OUTPUT_JPG, "JPEG", quality=96, subsampling=0, dpi=(180, 180))
        page.save(OUTPUT_PDF, "PDF", resolution=180.0, quality=96, subsampling=0)
        print(OUTPUT_JPG)
        print(OUTPUT_PDF)


if __name__ == "__main__":
    main()
