#!/usr/bin/env python3
"""Validate the equal-thickness interference report against its raw record."""

from __future__ import annotations

import math
import re
import statistics
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REPORT_DIR = ROOT / "等厚干涉"
MARKDOWN = REPORT_DIR / "等厚干涉实验报告.md"
DATA_TEX = REPORT_DIR / "latex-report" / "sections" / "02-operation-data.tex"
RESULTS_TEX = REPORT_DIR / "latex-report" / "sections" / "03-results.tex"

LAMBDA_MM = 5.893e-4
NEWTON_K = list(range(17, 5, -1))
NEWTON_XR = [
    21.539, 21.633, 21.729, 21.831, 21.930, 22.033,
    22.141, 22.261, 22.398, 22.526, 22.664, 22.815,
]
NEWTON_XL = [
    27.893, 27.804, 27.719, 27.629, 27.509, 27.401,
    27.287, 27.169, 27.050, 26.913, 26.767, 26.620,
]
WEDGE_S = [
    13.895, 13.624, 13.347, 13.064, 12.812,
    12.535, 12.280, 12.010, 11.710, 11.475,
    11.160, 10.899, 10.769, 10.338, 10.075,
    9.802, 9.547, 9.284, 9.016, 8.753,
]
L_LEFT_MM = 6.208
L_RIGHT_MM = 48.966


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def close(actual: float, expected: float, tolerance: float = 5e-7) -> bool:
    return math.isclose(actual, expected, rel_tol=0.0, abs_tol=tolerance)


def parse_markdown_tables(text: str) -> tuple[list[list[float]], list[list[float]]]:
    newton_block = text.split("## 3. 牛顿环原始数据转录", 1)[1].split("## 4. 劈尖原始数据转录", 1)[0]
    wedge_block = text.split("## 4. 劈尖原始数据转录", 1)[1].split("# 三、结果与分析", 1)[0]

    newton_rows = []
    for line in newton_block.splitlines():
        match = re.match(
            r"^\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|$",
            line,
        )
        if match:
            newton_rows.append([float(value) for value in match.groups()])

    wedge_rows = []
    for line in wedge_block.splitlines():
        match = re.match(
            r"^\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*(\d+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|$",
            line,
        )
        if match:
            wedge_rows.append([float(value) for value in match.groups()])
    return newton_rows, wedge_rows


def calculate() -> dict[str, float | list[float]]:
    diameters = [left - right for right, left in zip(NEWTON_XR, NEWTON_XL)]
    radius_values = [
        (diameters[i] ** 2 - diameters[i + 6] ** 2) / (24 * LAMBDA_MM) / 1000
        for i in range(6)
    ]
    radius_mean = statistics.mean(radius_values)
    radius_s = statistics.stdev(radius_values)
    radius_ua = radius_s / math.sqrt(6)

    ai = [(WEDGE_S[i] - WEDGE_S[i + 10]) / 10 for i in range(10)]
    length = L_RIGHT_MM - L_LEFT_MM
    thickness_values = [5 * length * LAMBDA_MM / (10 * value) for value in ai]
    thickness = statistics.mean(thickness_values)
    thickness_s = statistics.stdev(thickness_values)
    thickness_ua = thickness_s / math.sqrt(10)

    return {
        "diameters": diameters,
        "radius_values": radius_values,
        "radius_mean": radius_mean,
        "radius_s": radius_s,
        "radius_ua": radius_ua,
        "ai": ai,
        "length": length,
        "thickness_values": thickness_values,
        "thickness": thickness,
        "thickness_s": thickness_s,
        "thickness_ua": thickness_ua,
    }


def main() -> int:
    errors: list[str] = []
    markdown = MARKDOWN.read_text(encoding="utf-8")
    data_tex = DATA_TEX.read_text(encoding="utf-8")
    results_tex = RESULTS_TEX.read_text(encoding="utf-8")
    newton_rows, wedge_rows = parse_markdown_tables(markdown)
    values = calculate()

    require(len(newton_rows) == 12, "Markdown 牛顿环表必须有 12 行数据。", errors)
    require(len(wedge_rows) == 10, "Markdown 劈尖表必须有 10 行逐差数据。", errors)

    if len(newton_rows) == 12:
        for index, row in enumerate(newton_rows):
            k, xr, xl, diameter, diameter_sq = row
            expected_d = values["diameters"][index]
            require(int(k) == NEWTON_K[index], f"牛顿环第 {index + 1} 行级次错误。", errors)
            require(close(xr, NEWTON_XR[index]), f"k={int(k)} 的右侧读数错误。", errors)
            require(close(xl, NEWTON_XL[index]), f"k={int(k)} 的左侧读数错误。", errors)
            require(close(diameter, expected_d), f"k={int(k)} 的直径计算错误。", errors)
            require(close(diameter_sq, expected_d ** 2, 5.1e-6), f"k={int(k)} 的直径平方错误。", errors)

    if len(wedge_rows) == 10:
        for index, row in enumerate(wedge_rows):
            i, s_i, i10, s_i10, span, a_i = row
            expected_span = WEDGE_S[index] - WEDGE_S[index + 10]
            require(int(i) == index + 1 and int(i10) == index + 11, f"劈尖第 {index + 1} 行编号错误。", errors)
            require(close(s_i, WEDGE_S[index]), f"s_{index + 1} 转录错误。", errors)
            require(close(s_i10, WEDGE_S[index + 10]), f"s_{index + 11} 转录错误。", errors)
            require(close(span, expected_span), f"第 {index + 1} 组逐差错误。", errors)
            require(close(a_i, expected_span / 10), f"第 {index + 1} 组条纹间距错误。", errors)

    required_markdown = [
        r"\bar R=\frac{1}{6}\sum_{i=1}^{6}R_i=1.003107",
        r"u_A(\bar R)=\frac{s_R}{\sqrt 6}=0.005696",
        r"\boxed{R=(1.003\pm0.006)",
        r"e_i=\frac{10L\lambda}{2(s_i-s_{i+10})}",
        r"u_A(\bar e)=\frac{s_e}{\sqrt{10}}=0.27276",
        r"\boxed{e=(46.49\pm0.27)",
    ]
    required_tex = [
        "8 & 22.526 & 26.913 & 4.387 & 19.24577",
        "10 & 11.475 & 20 &  8.753 & 2.722 & 0.2722",
        r"u_A(\bar R)=\frac{s_R}{\sqrt 6}=0.005696",
        r"\ResultBox{R=(1.003\pm0.006)",
        r"e_i=\frac{10L\lambda}{2(s_i-s_{i+10})}",
        r"\ResultBox{e=(46.49\pm0.27)",
    ]
    for snippet in required_markdown:
        require(snippet in markdown, f"Markdown 缺少或未更新：{snippet}", errors)
    combined_tex = data_tex + results_tex
    for snippet in required_tex:
        require(snippet in combined_tex, f"LaTeX 缺少或未更新：{snippet}", errors)

    forbidden = [
        "22.520", "8.763", "1.002\\pm0.005", "46.47\\pm0.26",
        "u_B(R_i)", "u_B(e)", "u_c(\\bar R)", "u_c(e)",
    ]
    for stale in forbidden:
        require(stale not in markdown and stale not in combined_tex, f"仍存在旧值：{stale}", errors)

    if errors:
        print("校验失败：")
        for error in errors:
            print(f"- {error}")
        return 1

    print("等厚干涉报告校验通过。")
    print(f"R = {values['radius_mean']:.6f} m, uA(R) = {values['radius_ua']:.6f} m")
    print(f"e = {values['thickness'] * 1000:.6f} um, uA(e) = {values['thickness_ua'] * 1000:.6f} um")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
