#!/usr/bin/env python3
"""Copy UI + KG JSON into public/ for Vercel static CDN (run at build time)."""
from __future__ import annotations

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "public"


def main() -> None:
    PUBLIC.mkdir(exist_ok=True)

    ui_src = ROOT / "fitkg_graph_ui"
    ui_dst = PUBLIC / "fitkg_graph_ui"
    if ui_src.is_dir():
        if ui_dst.exists():
            shutil.rmtree(ui_dst)
        shutil.copytree(ui_src, ui_dst)
        print(f"Copied UI -> {ui_dst}")

    kg_src = ROOT / "outputs" / "fitkg_kg"
    kg_dst = PUBLIC / "outputs" / "fitkg_kg"
    if kg_src.is_dir():
        kg_dst.parent.mkdir(parents=True, exist_ok=True)
        if kg_dst.exists():
            shutil.rmtree(kg_dst)
        shutil.copytree(kg_src, kg_dst)
        print(f"Copied KG data -> {kg_dst}")


if __name__ == "__main__":
    main()
