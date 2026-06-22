#!/usr/bin/env python3
"""Shared front/back body SVG for FitKG muscle highlighting."""
from __future__ import annotations

from typing import Iterable, List

# Matches fitkg_graph_ui/body_viewer.js regions
BODY_SVG_TEMPLATE = """
<svg viewBox="0 0 420 440" xmlns="http://www.w3.org/2000/svg" style="width:100%;max-width:420px;">
  <defs>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a3544"/>
      <stop offset="100%" stop-color="#1e2836"/>
    </linearGradient>
  </defs>
  <style>
    .bv-title {{ fill:#8b9cb3; font:600 11px system-ui,sans-serif; }}
    .bv-r {{ fill:url(#skinGrad); stroke:#4a5568; stroke-width:1; transition:fill .18s, stroke .18s, opacity .18s; }}
    .bv-on {{ fill:rgba(61,139,253,0.55) !important; stroke:#7eb6ff !important; stroke-width:2; }}
    .bv-on-strong {{ fill:rgba(61,139,253,0.85) !important; stroke:#fff !important; stroke-width:2.5; }}
    .bv-dim {{ opacity:0.35; }}
  </style>
  <text class="bv-title" x="95" y="16" text-anchor="middle">Front</text>
  <g transform="translate(0,22)">
    <ellipse id="head" class="bv-r" cx="95" cy="26" rx="20" ry="24"/>
    <rect id="neck" class="bv-r" x="84" y="48" width="22" height="16" rx="4"/>
    <path id="shoulder_l" class="bv-r" d="M52 64 L84 62 L81 88 L49 86 Z"/>
    <path id="shoulder_r" class="bv-r" d="M138 64 L106 62 L109 88 L141 86 Z"/>
    <path id="chest" class="bv-r" d="M68 64 L122 64 L118 118 L72 118 Z"/>
    <path id="biceps_l" class="bv-r" d="M38 88 L54 88 L48 158 L34 158 Z"/>
    <path id="biceps_r" class="bv-r" d="M152 88 L136 88 L142 158 L156 158 Z"/>
    <path id="forearm_l" class="bv-r" d="M32 158 L50 158 L46 228 L30 228 Z"/>
    <path id="forearm_r" class="bv-r" d="M158 158 L140 158 L144 228 L160 228 Z"/>
    <path id="abs" class="bv-r" d="M78 116 L112 116 L110 168 L80 168 Z"/>
    <path id="obliques" class="bv-r" d="M68 118 L78 118 L80 168 L70 168 Z M122 118 L112 118 L110 168 L120 168 Z"/>
    <path id="hip_flexor" class="bv-r" d="M72 166 L118 166 L116 198 L74 198 Z"/>
    <path id="thigh_l" class="bv-r" d="M68 196 L94 196 L92 288 L66 288 Z"/>
    <path id="thigh_r" class="bv-r" d="M122 196 L96 196 L98 288 L124 288 Z"/>
    <path id="calf_l" class="bv-r" d="M70 288 L90 288 L88 368 L68 368 Z"/>
    <path id="calf_r" class="bv-r" d="M120 288 L100 288 L102 368 L122 368 Z"/>
  </g>
  <text class="bv-title" x="325" y="16" text-anchor="middle">Back</text>
  <g transform="translate(210,22)">
    <ellipse id="head_back" class="bv-r" cx="95" cy="26" rx="20" ry="24"/>
    <rect id="neck_back" class="bv-r" x="84" y="48" width="22" height="16" rx="4"/>
    <path id="shoulder_l_back" class="bv-r" d="M52 64 L84 62 L81 88 L49 86 Z"/>
    <path id="shoulder_r_back" class="bv-r" d="M138 64 L106 62 L109 88 L141 86 Z"/>
    <path id="upper_back" class="bv-r" d="M68 62 L122 62 L118 108 L72 108 Z"/>
    <path id="mid_back" class="bv-r" d="M72 106 L118 106 L114 148 L76 148 Z"/>
    <path id="lower_back" class="bv-r" d="M76 146 L114 146 L110 188 L80 188 Z"/>
    <path id="triceps_l" class="bv-r" d="M38 88 L54 88 L48 158 L34 158 Z"/>
    <path id="triceps_r" class="bv-r" d="M152 88 L136 88 L142 158 L156 158 Z"/>
    <path id="forearm_l_back" class="bv-r" d="M32 158 L50 158 L46 228 L30 228 Z"/>
    <path id="forearm_r_back" class="bv-r" d="M158 158 L140 158 L144 228 L160 228 Z"/>
    <path id="glutes" class="bv-r" d="M74 186 L118 186 L114 222 L78 222 Z"/>
    <path id="thigh_l_back" class="bv-r" d="M68 220 L94 220 L92 288 L66 288 Z"/>
    <path id="thigh_r_back" class="bv-r" d="M122 220 L96 220 L98 288 L124 288 Z"/>
    <path id="calf_l_back" class="bv-r" d="M70 288 L90 288 L88 368 L68 368 Z"/>
    <path id="calf_r_back" class="bv-r" d="M120 288 L100 288 L102 368 L122 368 Z"/>
  </g>
</svg>
"""

# Map canonical region id → SVG element ids (front + back duplicates)
REGION_TO_SVG_IDS = {
    "head": ["head", "head_back"],
    "neck": ["neck", "neck_back"],
    "shoulder_l": ["shoulder_l", "shoulder_l_back"],
    "shoulder_r": ["shoulder_r", "shoulder_r_back"],
    "chest": ["chest"],
    "biceps_l": ["biceps_l"],
    "biceps_r": ["biceps_r"],
    "triceps_l": ["triceps_l"],
    "triceps_r": ["triceps_r"],
    "forearm_l": ["forearm_l", "forearm_l_back"],
    "forearm_r": ["forearm_r", "forearm_r_back"],
    "abs": ["abs"],
    "obliques": ["obliques"],
    "hip_flexor": ["hip_flexor"],
    "upper_back": ["upper_back"],
    "mid_back": ["mid_back"],
    "lower_back": ["lower_back"],
    "glutes": ["glutes"],
    "thigh_l": ["thigh_l", "thigh_l_back"],
    "thigh_r": ["thigh_r", "thigh_r_back"],
    "calf_l": ["calf_l", "calf_l_back"],
    "calf_r": ["calf_r", "calf_r_back"],
    "arm_l": ["biceps_l", "triceps_l"],
    "arm_r": ["biceps_r", "triceps_r"],
}

REGION_QUERIES = {
    "head": "head neck",
    "neck": "neck cervical",
    "chest": "chest pectoral",
    "shoulder_l": "shoulder deltoid",
    "shoulder_r": "shoulder deltoid",
    "biceps_l": "biceps brachii",
    "biceps_r": "biceps brachii",
    "triceps_l": "triceps brachii",
    "triceps_r": "triceps brachii",
    "forearm_l": "forearm wrist",
    "forearm_r": "forearm wrist",
    "abs": "abdominal core",
    "obliques": "oblique abdominal",
    "hip_flexor": "hip flexor psoas",
    "upper_back": "trapezius upper back",
    "mid_back": "latissimus dorsi",
    "lower_back": "lower back erector",
    "glutes": "gluteus hip",
    "thigh_l": "quadriceps thigh hamstring",
    "thigh_r": "quadriceps thigh hamstring",
    "calf_l": "calf gastrocnemius",
    "calf_r": "calf gastrocnemius",
}


def expand_regions(active: Iterable[str]) -> List[str]:
    out: List[str] = []
    for rid in active:
        out.append(rid)
        if rid.endswith("_l"):
            pair = rid.replace("_l", "_r")
            if pair in REGION_TO_SVG_IDS and pair not in active:
                out.append(pair)
    return list(dict.fromkeys(out))


def render_body_svg(active: Iterable[str]) -> str:
    active_set = set(expand_regions(active))
    svg = BODY_SVG_TEMPLATE
    has_any = bool(active_set)
    for rid, svg_ids in REGION_TO_SVG_IDS.items():
        for sid in svg_ids:
            if rid in active_set:
                svg = svg.replace(f'id="{sid}" class="bv-r"', f'id="{sid}" class="bv-r bv-on"', 1)
            elif has_any:
                svg = svg.replace(f'id="{sid}" class="bv-r"', f'id="{sid}" class="bv-r bv-dim"', 1)
    return svg
