# -*- coding: utf-8 -*-
"""Render the CampusMarket report cover with Times New Roman for all English text."""
import sys
from pathlib import Path

PDF_SKILL_DIR = r"C:\Users\李积佳\.zcode\cli\plugins\cache\zcode-plugins-official\pdf\0.2.3\skills\pdf"
sys.path.insert(0, str(Path(PDF_SKILL_DIR) / "scripts"))

import cover_render  # noqa: E402

BASE = Path(r"D:\作业\master 1\5003\project\CampusMarket_Final")

content = {
    "institution": "Database Systems",
    "doc_type": "FINAL REPORT · TRACK 1",
    "title": "CampusMarket: A Campus Second-hand Trading Platform",
    "fields": [
        ["Member A", "Wang Fangcheng  72640065"],
        ["Member B", "Cai Haoneng  72640692"],
        ["Member C", "Li Jijia  72640201"],
    ],
    "date": "2026-11-22",
}

# 英文全部使用 Times New Roman（封面无中文，字体可整体替换）：
#   serif -> Times New Roman Bold（机构名 / 标题）
#   sans  -> Times New Roman（文件类型行 / 字段 / 日期）
overrides = {
    "serif": ("CoverSerifTNR", r"C:\Windows\Fonts\timesbd.ttf", 0),
    "sans": ("CoverSansTNR", r"C:\Windows\Fonts\times.ttf", 0),
    "kai": ("CoverSerifTNR", r"C:\Windows\Fonts\timesbd.ttf", 0),
    "latin": ("CoverSansTNR", r"C:\Windows\Fonts\times.ttf", 0),
}

out = BASE / "build" / "cover.pdf"
cover_render.render_cover("09", content, str(out), font_overrides=overrides)
print("cover rendered:", out)
