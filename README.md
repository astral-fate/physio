.
# PG-XFormer: Home-Based Physiotherapy Monitoring
## Overview
PG-XFormer is a pose-guided cross-modal transformer system designed to automatically monitor and correct home-based physical therapy exercises.
## The Problem
 * Roughly half of all physical therapy episodes are partly or wholly home-based.
 * Adherence to prescribed exercises improves recovery outcomes, but unsupervised patients frequently commit form errors that reduce rehabilitative benefits and risk re-injury.
 * Current computational solutions suffer from a severe "sim-to-real" gap because they are heavily reliant on synthetic or laboratory data, masking clinical failure rates.
 * Existing systems typically stop at basic exercise classification or quality scoring rather than generating the actionable, natural-language feedback that a home-based patient actually needs.
## The Solution
 * We built PG-XFormer, a system that couples a CTR-GCN skeleton encoder with a VideoMAE-base video encoder using bottleneck cross-attention fusion.
 * To overcome the lack of diverse real-patient visual data, the system uses Pose-Retrieved Synthetic Appearance (PRSA) to map clinical patient clips to the nearest synthetic recordings using Dynamic Time Warping (DTW) on normalized poses.
 * The model extracts kinematic features (like joint angles, range of motion, symmetry, and trunk lean) and processes them through a per-class skeleton Variational Autoencoder (VAE) to score anomalies.
 * A safety-guarded Large Language Model generates natural-language corrective cues based entirely on a structured kinematic report.
 * The AI agent is programmed to escalate warnings or halt sessions entirely if critical form errors occur across consecutive repetitions.
## Study & Validation
 * We conducted a reproducible sim-to-real evaluation protocol utilizing the clinical KIMORE dataset alongside the massive synthetic InfiniteRep corpus.
 * In a clinical study involving five licensed physiotherapists, the system's generated cues received a mean clinical accuracy rating of 4.4 out of 5 and a safety rating of 4.7 out of 5.
 * The LLM agent proved highly reliable, exhibiting a hallucination rate of only 2% and successfully halting sessions when simulated critical flags (such as trunk flexion exceeding 45 degrees) were triggered.
### Model Performance on KIMORE Benchmark
| Model Architecture | Macro-F1 Score | Accuracy |
|---|---|---|
| PG-XFormer (Multimodal Concat) | 89.1±1.7% | 89.2±1.9% |
| CTR-GCN-only (Skeleton Stream) | 86.8±3.5% | 87.1±3.4% |
| CNN+LSTM Concat (M0 Baseline) | 80.6±6.0% | 81.5±6.0% |
| 2-layer BiLSTM | 65.0±4.7% | 69.3±4.8% |
## System Architecture
The total training objective of the system utilizes cross-entropy, InfoNCE alignment, and Maximum Mean Discrepancy (MMD) to align synthetic and real video features during fine-tuning. The loss function is defined as:
In this formulation, \overline{s} and \overline{v} represent the unit-normalised pooled skeleton and video features.
## Codebase & Tech Stack
 * **Deep Learning Framework:** PyTorch 2.4.
 * **Transformer Ecosystem:** Hugging Face transformers 4.44.2 and peft 0.13.0.
 * **Vision & Pose Models:** VideoMAE-base (Kinetics-400 pretrained) and CTR-GCN.
 * **LLM Agent:** Claude Sonnet via the Anthropic API.
 * **Hardware Compute:** Training conducted on NVIDIA A100/H100 GPUs utilizing mixed-precision (bfloat16) and TF32 matmul.
