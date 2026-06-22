/**
 * FitKG BodyMuscleViewer — front/back anatomical SVG + live COCO-17 pose overlay.
 */
(function (global) {
  const REGION_LABELS = {};

  const BODY_SVG = `
<svg class="body-svg" viewBox="0 0 420 440" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="skinGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#2a3544"/>
      <stop offset="100%" stop-color="#1e2836"/>
    </linearGradient>
  </defs>
  <style>
    .bv-title { fill:#8b9cb3; font:600 11px system-ui,sans-serif; }
    .bv-r {
      fill:url(#skinGrad); stroke:#4a5568; stroke-width:1;
      cursor:pointer; transition:fill .18s, stroke .18s, opacity .18s;
    }
    .bv-r:hover { stroke:#7eb6ff; stroke-width:1.5; }
    .bv-on { fill:rgba(61,139,253,0.55) !important; stroke:#7eb6ff !important; stroke-width:2; }
    .bv-on-strong { fill:rgba(61,139,253,0.85) !important; stroke:#fff !important; stroke-width:2.5; }
    .bv-dim { opacity:0.35; }
    .bv-sk { fill:none; stroke:#3ecf8e; stroke-width:2.2; stroke-linecap:round; opacity:0.95; }
    .bv-j { fill:#3ecf8e; stroke:#1a3328; stroke-width:0.5; }
    .bv-pose-label { fill:#3ecf8e; font:600 9px system-ui,sans-serif; }
  </style>

  <text class="bv-title" x="95" y="16" text-anchor="middle">Front + pose</text>
  <g id="view-anterior" transform="translate(0,22)">
    <ellipse data-region="head" class="bv-r" cx="95" cy="26" rx="20" ry="24"/>
    <rect data-region="neck" class="bv-r" x="84" y="48" width="22" height="16" rx="4"/>
    <path data-region="shoulder_l" class="bv-r" d="M52 64 L84 62 L81 88 L49 86 Z"/>
    <path data-region="shoulder_r" class="bv-r" d="M138 64 L106 62 L109 88 L141 86 Z"/>
    <path data-region="chest" class="bv-r" d="M68 64 L122 64 L118 118 L72 118 Z"/>
    <path data-region="biceps_l" class="bv-r" d="M38 88 L54 88 L48 158 L34 158 Z"/>
    <path data-region="biceps_r" class="bv-r" d="M152 88 L136 88 L142 158 L156 158 Z"/>
    <path data-region="forearm_l" class="bv-r" d="M32 158 L50 158 L46 228 L30 228 Z"/>
    <path data-region="forearm_r" class="bv-r" d="M158 158 L140 158 L144 228 L160 228 Z"/>
    <path data-region="abs" class="bv-r" d="M78 116 L112 116 L110 168 L80 168 Z"/>
    <path data-region="obliques" class="bv-r" d="M68 118 L78 118 L80 168 L70 168 Z M122 118 L112 118 L110 168 L120 168 Z" opacity="0.85"/>
    <path data-region="hip_flexor" class="bv-r" d="M72 166 L118 166 L116 198 L74 198 Z"/>
    <path data-region="thigh_l" class="bv-r" d="M68 196 L94 196 L92 288 L66 288 Z"/>
    <path data-region="thigh_r" class="bv-r" d="M122 196 L96 196 L98 288 L124 288 Z"/>
    <path data-region="calf_l" class="bv-r" d="M70 288 L90 288 L88 368 L68 368 Z"/>
    <path data-region="calf_r" class="bv-r" d="M120 288 L100 288 L102 368 L128 368 Z"/>
    <g id="skel-front" class="bv-skeleton" transform="translate(95,200) scale(0.9)"></g>
    <text class="bv-pose-label" x="95" y="392" text-anchor="middle" id="poseLabelFront">COCO-17</text>
  </g>

  <text class="bv-title" x="325" y="16" text-anchor="middle">Back</text>
  <g id="view-posterior" transform="translate(210,22)">
    <ellipse data-region="head" class="bv-r" cx="95" cy="26" rx="20" ry="24"/>
    <rect data-region="neck" class="bv-r" x="84" y="48" width="22" height="16" rx="4"/>
    <path data-region="shoulder_l" class="bv-r" d="M52 64 L84 62 L81 88 L49 86 Z"/>
    <path data-region="shoulder_r" class="bv-r" d="M138 64 L106 62 L109 88 L141 86 Z"/>
    <path data-region="upper_back" class="bv-r" d="M68 62 L122 62 L118 108 L72 108 Z"/>
    <path data-region="mid_back" class="bv-r" d="M72 106 L118 106 L114 148 L76 148 Z"/>
    <path data-region="lower_back" class="bv-r" d="M76 146 L114 146 L110 188 L80 188 Z"/>
    <path data-region="triceps_l" class="bv-r" d="M38 88 L54 88 L48 158 L34 158 Z"/>
    <path data-region="triceps_r" class="bv-r" d="M152 88 L136 88 L142 158 L156 158 Z"/>
    <path data-region="forearm_l" class="bv-r" d="M32 158 L50 158 L46 228 L30 228 Z"/>
    <path data-region="forearm_r" class="bv-r" d="M158 158 L140 158 L144 228 L160 228 Z"/>
    <path data-region="glutes" class="bv-r" d="M74 186 L118 186 L114 222 L78 222 Z"/>
    <path data-region="thigh_l" class="bv-r" d="M68 220 L94 220 L92 288 L66 288 Z" opacity="0.9"/>
    <path data-region="thigh_r" class="bv-r" d="M122 220 L96 220 L98 288 L124 288 Z" opacity="0.9"/>
    <path data-region="calf_l" class="bv-r" d="M70 288 L90 288 L88 368 L68 368 Z"/>
    <path data-region="calf_r" class="bv-r" d="M120 288 L100 288 L102 368 L122 368 Z"/>
    <g id="skel-back" class="bv-skeleton" transform="translate(95,200) scale(0.9)" opacity="0.45"></g>
  </g>
</svg>`;

  const COCO_EDGES = [
    [0,1],[0,2],[1,3],[2,4],[5,6],[5,7],[7,9],[6,8],[8,10],
    [5,11],[6,12],[11,12],[11,13],[13,15],[12,14],[14,16]
  ];
  const COCO_REST = [
    [0,0.95],[0,0.82],[-0.08,-0.88],[0.08,-0.88],[-0.14,-0.78],[0.14,-0.78],
    [-0.22,-0.62],[0.22,-0.62],[-0.28,-0.38],[0.28,-0.38],[-0.32,-0.12],[0.32,-0.12],
    [-0.18,0.08],[0.18,0.08],[-0.2,0.42],[0.2,0.42],[0,0.22]
  ];

  const NS = "http://www.w3.org/2000/svg";

  function expandLegacy(ids, legacyAliases) {
    const out = new Set(ids);
    (ids || []).forEach(id => {
      (legacyAliases[id] || []).forEach(x => out.add(x));
    });
    return out;
  }

  function mapKpToSvg(kp, scale) {
    const s = scale || 55;
    return kp.map(([x, y]) => [x * s, -y * s]);
  }

  class BodyMuscleViewer {
    constructor(container, opts = {}) {
      this.container = typeof container === "string" ? document.querySelector(container) : container;
      this.onRegionClick = opts.onRegionClick || null;
      this.legacyAliases = opts.legacyAliases || { arm_l: ["biceps_l","triceps_l"], arm_r: ["biceps_r","triceps_r"] };
      this.poseScale = opts.poseScale || 55;
      this.active = new Set();
      this.weights = {};
      this._animTimer = null;
      this._poseSeq = [];
      this._render();
      this.setRestPose();
    }

    _render() {
      if (!this.container) return;
      this.container.innerHTML = BODY_SVG;
      this._skelFront = this.container.querySelector("#skel-front");
      this._skelBack = this.container.querySelector("#skel-back");
      this._poseLabel = this.container.querySelector("#poseLabelFront");
      this.container.querySelectorAll("[data-region]").forEach(el => {
        el.addEventListener("click", () => {
          const rid = el.getAttribute("data-region");
          if (this.onRegionClick) this.onRegionClick(rid, REGION_LABELS[rid]?.label_en || rid);
        });
        el.addEventListener("mouseenter", () => {
          const rid = el.getAttribute("data-region");
          const meta = REGION_LABELS[rid];
          el.setAttribute("title", meta ? `${meta.label_en} (${meta.label_zh})` : rid.replace(/_/g, " "));
        });
      });
    }

    _clearGroup(gEl) {
      if (!gEl) return;
      while (gEl.firstChild) gEl.removeChild(gEl.firstChild);
    }

    _drawPoseGroup(gEl, pts, mirror) {
      this._clearGroup(gEl);
      const mapped = pts.map(([x, y]) => {
        const mx = mirror ? -x : x;
        return [mx, y];
      });
      COCO_EDGES.forEach(([a, b]) => {
        const line = document.createElementNS(NS, "line");
        line.setAttribute("x1", mapped[a][0]); line.setAttribute("y1", mapped[a][1]);
        line.setAttribute("x2", mapped[b][0]); line.setAttribute("y2", mapped[b][1]);
        line.setAttribute("class", "bv-sk");
        gEl.appendChild(line);
      });
      mapped.forEach(([x, y]) => {
        const c = document.createElementNS(NS, "circle");
        c.setAttribute("cx", x); c.setAttribute("cy", y); c.setAttribute("r", 3);
        c.setAttribute("class", "bv-j");
        gEl.appendChild(c);
      });
    }

    setRestPose() {
      this.stopPose();
      const pts = mapKpToSvg(COCO_REST, this.poseScale);
      this._drawPoseGroup(this._skelFront, pts, false);
      this._drawPoseGroup(this._skelBack, pts, true);
      if (this._poseLabel) this._poseLabel.textContent = "COCO-17 rest";
    }

    /** keypoints: 17×2 normalised (pelvis-centric, y-up) */
    setPoseFrame(keypoints, label) {
      if (!keypoints || keypoints.length < 17) return;
      const pts = mapKpToSvg(keypoints, this.poseScale);
      this._drawPoseGroup(this._skelFront, pts, false);
      this._drawPoseGroup(this._skelBack, pts, true);
      if (this._poseLabel) this._poseLabel.textContent = label || "Live pose";
    }

    playSequence(frames, fps, label) {
      this.stopPose();
      if (!frames?.length) return;
      this._poseSeq = frames;
      let i = 0;
      const ms = 1000 / (fps || 8);
      const tick = () => {
        this.setPoseFrame(frames[i], `${label || "Pose"} · f${i + 1}/${frames.length}`);
        i = (i + 1) % frames.length;
        this._animTimer = setTimeout(tick, ms);
      };
      tick();
    }

    stopPose() {
      if (this._animTimer) {
        clearTimeout(this._animTimer);
        this._animTimer = null;
      }
    }

    setActive(regionIds, weights) {
      this.active = expandLegacy(regionIds || [], this.legacyAliases);
      this.weights = weights || {};
      this._applyHighlight();
    }

    clear() {
      this.active = new Set();
      this.weights = {};
      this._applyHighlight();
    }

    _applyHighlight() {
      if (!this.container) return;
      const hasActive = this.active.size > 0;
      this.container.querySelectorAll("[data-region]").forEach(el => {
        const rid = el.getAttribute("data-region");
        el.classList.remove("bv-on", "bv-on-strong", "bv-dim");
        if (!hasActive) return;
        if (this.active.has(rid)) {
          const w = this.weights[rid] || 1;
          el.classList.add(w >= 3 ? "bv-on-strong" : "bv-on");
        } else {
          el.classList.add("bv-dim");
        }
      });
    }
  }

  function regionsFromNode(node, adj, nodeById) {
    const BODY = new Set(["身体部位", "解剖结构"]);
    const EX = new Set(["健身动作", "运动项目"]);
    const regions = new Set();
    const muscles = [];
    if (!node) return { regions: [], muscles: [] };

    const addFromLabel = (n) => {
      const zh = n.label_zh || n.label || "";
      const en = n.label_en || n.display_label || "";
      Object.entries(REGION_LABELS).forEach(([rid, meta]) => {
        const kws = (meta.keywords || []).map(k => k.toLowerCase());
        const blob = `${zh} ${en}`.toLowerCase();
        if (kws.some(k => blob.includes(k))) regions.add(rid);
      });
    };

    if (BODY.has(node.type)) {
      addFromLabel(node);
      muscles.push(node);
    } else if (EX.has(node.type)) {
      (adj[node.id] || []).forEach(({ n: tid, e, dir }) => {
        if (e.type !== "锻炼" && e.type_en !== "Trains") return;
        if (dir !== "out") return;
        const tgt = nodeById[tid];
        if (!tgt || !BODY.has(tgt.type)) return;
        addFromLabel(tgt);
        muscles.push(tgt);
      });
    } else {
      addFromLabel(node);
    }
    return { regions: [...regions], muscles };
  }

  function loadRegionLabels(mapUrl) {
    return fetch(mapUrl)
      .then(r => r.json())
      .then(map => {
        (map.regions || []).forEach(r => {
          REGION_LABELS[r.id] = {
            label_en: r.label_en,
            label_zh: r.label_zh,
            keywords: r.fitkg_keywords || [],
          };
        });
        return map;
      })
      .catch(() => ({}));
  }

  global.BodyMuscleViewer = BodyMuscleViewer;
  global.FitKGBody = { regionsFromNode, loadRegionLabels, expandLegacy, REGION_LABELS, COCO_EDGES };
})(typeof window !== "undefined" ? window : globalThis);
