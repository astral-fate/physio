# PG-XFormer — What We Are Building (Plain English)

This document explains the **MIUA / physiotherapy monitoring** project: the scientific goal, the three datasets, how training is supposed to work, what the code does today, and what is still missing (including the agentic AI layer).

---

## The problem we care about

Many patients do **physiotherapy exercises at home** without a therapist watching. They often perform movements incorrectly, which reduces benefit and can increase injury risk.

We want a system that can:

1. **Watch** a short video of the patient (plus their body pose).
2. **Recognize** which rehabilitation exercise they are doing.
3. **Flag** when the movement looks abnormal compared to healthy form.
4. **Give** short, safe, plain-language feedback — like a therapist would — not just a class label.

The research paper frames this as **PG-XFormer**: a pose-guided cross-modal transformer trained with a **synthetic → clinical** pipeline, then extended with an **agentic LLM** feedback layer.

---

## The core idea (one sentence)

**Learn from lots of cheap synthetic exercise data (InfiniteRep), adapt carefully to real patients (KIMORE), check that it generalizes to another lab dataset (UI-PRMD), and optionally turn mistakes into therapist-style cues via a guarded language model.**

We are **not** training one model on all three datasets mixed together. Each dataset has a **fixed role**.

---

## The three datasets and their roles

| Dataset | What it is | Role in the project |
|--------|------------|---------------------|
| **InfiniteRep** | Large **synthetic** dataset (~690 instances on your Drive: `basic fitness`) | **Pretraining only** — 10 home-fitness exercises (curl, squat, pushup, …) |
| **KIMORE** | **Clinical** Kinect recordings + quality scores (`kimore_exercise_dataset.pkl`, 378 repetitions, 5 exercises) | **Main real-world training & evaluation** — stroke, Parkinson’s, back pain, etc. |
| **UI-PRMD** | Laboratory Kinect/Vicon movements (your Drive clone has **10 demo** recordings; full dataset is larger) | **External test only** — never used to update model weights in the paper protocol |

### Important detail about class names

- InfiniteRep uses names like `curl`, `squat`, `armraise`.
- KIMORE uses clinical tasks: `sit_to_stand`, `pelvis_tilt`, `squat`, `unilateral_stance`, `trunk_flexion`.
- UI-PRMD uses rehabilitation screen names: `deep_squat`, `hurdle_step`, `sit_to_stand`, …

Only **some** names overlap between KIMORE and UI-PRMD (about five movement types in the paper). That is why EDA has a separate table for UI-PRMD movements and a **mapped** column for cross-dataset comparison.

---

## PG-XFormer — the model (what the neural network is)

The classifier combines two streams:

1. **Skeleton stream (CTR-GCN)** — graph neural network on 17 body joints over 16 frames. Pose is treated as relatively stable across synthetic vs real video.
2. **Video stream (VideoMAE)** — pretrained video transformer on 16 RGB frames (224×224).

They are fused with **bottleneck tokens** (small learnable “hub” vectors that pass information between pose and video, instead of simply concatenating everything).

**Training losses:**

- **Classification** — which exercise is this?
- **InfoNCE alignment** — skeleton and video features should agree (during pretrain / multimodal training).
- **MMD** — during KIMORE fine-tuning, pull batches from InfiniteRep so the **video** branch does not stay “synthetic-looking” (labels still come from KIMORE only).

**Sim-to-real fine-tuning (Stage B):**

- **Freeze** the skeleton encoder.
- Add **LoRA** adapters on the video encoder.
- Train on **KIMORE only** for labels; MMD uses InfiniteRep only as an extra domain-alignment signal.

---

## The full pipeline (paper protocol)

This is the intended order. Your Colab script `pgxformer_colab_standalone.py` implements most of this; agentic AI is **not** in that file yet.

```
┌─────────────────────────────────────────────────────────────────┐
│  EDA (all 3 datasets) — tables & figures only, NO training     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE A — PRETRAIN on InfiniteRep ONLY (10 classes)            │
│  • 80% train / 10% val / 10% test, subject-disjoint            │
│  • ~20 epochs, domain randomization on video                      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE B — FINETUNE on KIMORE ONLY (5 classes)                   │
│  • Frozen skeleton + LoRA on video + MMD vs InfiniteRep batches    │
│  • ~15 epochs                                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
   │ KIMORE LOSO  │   │ Ablation     │   │ UI-PRMD test │
   │ (headline)   │   │ (Table 6)    │   │ (no train)   │
   └──────────────┘   └──────────────┘   └──────────────┘
          │
          ▼
   ┌──────────────────────────────────────────┐
   │  Agentic layer (paper — separate work)    │
   │  VAE anomaly → kinematic error report →   │
   │  LLM cue (Claude) → clinician study      │
   └──────────────────────────────────────────┘
```

### What each evaluation stage means

| Stage | What you measure |
|-------|------------------|
| **LOSO on KIMORE** | Leave-one-subject-out cross-validation — main paper result (accuracy, macro-F1, Cohen’s κ, ECE, confusion matrix). Target in draft: ~86% acc, ~85% macro-F1. |
| **Baseline M0** | Simpler CNN + LSTM concat model on KIMORE LOSO — comparison point (~76% macro-F1 in draft). |
| **Ablation** | Turn off or change parts: video-only, skeleton-only, concat vs bottleneck fusion, MMD on/off. |
| **UI-PRMD external** | Load KIMORE-trained model, run on UI-PRMD test clips only. |
| **TENT** (optional) | Test-time adaptation — mentioned in paper, not fully wired in standalone script. |

---

## Agentic AI layer (paper Section — not in training script)

After the network predicts an exercise, the **full system** in the paper also does:

1. **Per-class skeleton VAE** — trained on correct (“Expert”) KIMORE repetitions; high reconstruction error → anomaly flag.
2. **Kinematic error report** — JSON with joint angles, range of motion, symmetry, z-scored vs healthy reference (no diagnosis).
3. **LLM agent** — Claude (or similar) with strict safety rules: one short cue per rep, grounded only in the report, no invented errors.
4. **Clinician study** — physiotherapists rate cue quality; hallucination audit on held-out reports.

**This requires:** API key, error-report generator, and study spreadsheets. **`pgxformer_colab_standalone.py` does not run the LLM or clinician study** — only the vision/pose classifier pipeline.

---

## What lives in your Google Drive workspace

Permanent folder: **`My Drive/pgxformer_workspace/`**

| Path | Purpose |
|------|---------|
| `manifests/` | CSV indexes: InfiniteRep zips, KIMORE pickle rows, UI-PRMD segmented files |
| `cache/` | Cached EDA scans (delete `eda_uiprmd_manifest.parquet` if it was built from bad `input.csv`) |
| `tables/` | Paper tables: dataset summary, per-class counts, LOSO, ablation, external eval |
| `figs/` | EDA plots, confusion matrix, training curves |
| `checkpoints/` | `pgxformer_synthetic_best.pt` (10 classes), `pgxformer_finetuned_best.pt` (5 classes) |
| `logs/` | Run logs |

Data roots (your setup):

- `My Drive/basic fitness` — InfiniteRep  
- `My Drive/a physio/kimore_exercise_dataset.pkl` — KIMORE  
- `My Drive/a physio/UI-PRMD/` — CSV bundle + exported `label.csv` from segmented demo  
- `My Drive/UI-PRMD-Visualize-python-port/data` — segmented skeleton files (10-movement demo)

---

## Code files in this repo (what each one is for)

| File | Role |
|------|------|
| `paper.txt` | LaTeX-style paper draft with placeholder results |
| `prepaper.py` | Full research pipeline (EDA, model, training, LOSO, ablation) |
| `pgxformer_colab_standalone.py` | **One-file Colab** version — same story, no imports from other project files |
| `pgxformer_drive_pipeline.py` | Drive manifests + stages (prepare, eda, train, …) |
| `pgxformer_paper_pipeline.py` | Paper-oriented orchestration on top of Drive pipeline |
| `uiprmd_eda.py` | Standalone UI-PRMD exploratory analysis |

---

## `quick=True` vs `quick=False` (read this before trusting numbers)

| Mode | What it does | Use for |
|------|----------------|---------|
| **`quick=True`** | Tiny fake datasets, 2 epochs, 3 LOSO folds; in older versions VideoMAE on blank video caused huge nonsense losses | **Smoke test** — “does the pipeline run end-to-end?” |
| **`quick=False`** | Real InfiniteRep zips, real KIMORE pickle, VideoMAE, full epochs | **Paper numbers** — hours on GPU |

Your log from `quick=True` with version `2026-05-16-ckpt-fix` shows:

- Pretrain on **ToyDataset**, not 690 InfiniteRep videos.
- Absurd `train_loss` (~275 million) on PG-XFormer — **not meaningful**.
- LOSO ~20% accuracy on toy subjects — **not meaningful**.
- Baseline CNN+LSTM ~60% on toy data — only shows that branch trains normally.
- UI-PRMD external on **6** mapped clips (demo subset) — not the full paper setup.

**Do not put those quick-run metrics in the paper.** Re-run with `quick=False` after uploading the latest standalone (version `2026-05-16-paper-protocol` or newer).

---

## Recommended Colab commands (real experiment)

```python
from pgxformer_colab_standalone import run, Cfg

cfg = Cfg()
cfg.uiprmd_segmented_root = "/content/drive/My Drive/UI-PRMD-Visualize-python-port/data"

run("prepare", cfg=cfg)
run("eda", cfg=cfg)
run("pretrain", quick=False, cfg=cfg)   # InfiniteRep only — long
run("finetune", quick=False, cfg=cfg)   # KIMORE only
run("loso", quick=False, cfg=cfg)       # Main result
run("baseline", quick=False, cfg=cfg)
run("ablate", quick=False, cfg=cfg)
run("eval_uiprmd", quick=False, cfg=cfg)
run("report", cfg=cfg)
```

Use **GPU** runtime (T4 or better). Expect many hours for pretrain on 690 instances.

---

## What “success” looks like for the paper

1. **EDA** — Three datasets characterized; UI-PRMD movements listed; no bogus “all unlabeled” UI-PRMD row in tables.  
2. **KIMORE LOSO** — Report accuracy, macro-F1, κ, ECE, confusion matrix (replace `\result{...}` in `paper.txt`).  
3. **Ablation** — Table showing bottleneck + MMD + InfoNCE help vs concat baseline.  
4. **UI-PRMD** — External accuracy on held-out lab data (no fine-tuning on UI-PRMD).  
5. **Agentic** (separate track) — Example cues + clinician ratings + low hallucination rate.  

---

## Known limitations in your current setup

1. **KIMORE pickle** — LOSO uses repetition-level IDs unless you have the full KIMORE folder with 78 subjects; true 78-fold LOSO needs official KIMORE layout.  
2. **UI-PRMD demo** — 10 recordings is enough for pipeline testing, not for claiming full UI-PRMD benchmark.  
3. **LoRA** — May skip if `torchao` / `peft` versions conflict on Colab; video fine-tuning still runs without LoRA.  
4. **Agentic AI** — Still to build on top of trained checkpoints.  

---

## Summary in one paragraph

We are building **PG-XFormer**, a system that watches home exercise videos and skeleton pose, classifies the movement, and (in the full paper vision) explains mistakes in safe language. We **pretrain only on synthetic InfiniteRep**, **fine-tune and evaluate on clinical KIMORE**, and **test once on UI-PRMD without training on it**. The Colab pipeline prepares manifests on Drive, runs EDA, trains the model, runs LOSO and ablations, and writes tables for the paper. The **agentic LLM feedback** is a separate layer after classification and is not part of the current training script. Your recent `quick=True` run verified wiring only; **real results require `quick=False` on GPU with the full datasets.**
