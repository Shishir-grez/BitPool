# Deployment / infrastructure guide (PARKED)

Notes carried over from the design discussion. Not final.

## Target A — company laptop (preferred: real data)
- Constraints: CPU only (Intel Core Ultra i5, NPU), 16 GB RAM, ~8–10 GB usable, pip only (no uv,
  no Ollama, no arbitrary installers), Hugging Face blocked, no internet for the model, no cloud LLM APIs.
- Leading runtime: **onnxruntime-genai** (pip, prebuilt wheels). Alternatives: transformers+torch
  (heavy, slow on CPU), openvino-genai (pip, can use the NPU).
- Leading model: **Phi-4-mini-instruct, int4 ONNX** (official `microsoft/Phi-4-mini-instruct-onnx`,
  folder `cpu_and_mobile/cpu-int4-rtn-block-32-acc-level-4`, MIT). ~3 GB weights, ~24–40k context fits.
  Alternatives to bake off: Qwen3.5 4B, Gemma 4 E2B/E4B (ONNX conversion unconfirmed).
- Embeddings: small ONNX embedder (e5-small / bge-small class, or EmbeddingGemma 2 if available).
- Avoid: llama-cpp-python via unvetted wheels, anything that pulls `litellm` (compromised 1.82.7/1.82.8, Mar 2026),
  unofficial model re-uploads.
- Practical per-decision prompt budget: 4–8k tokens (CPU prefill speed + quality).

### Open questions for IT
- [ ] Can model folders be supplied via an internal HF mirror (Artifactory/Nexus) or approved transfer, with SHA-256 checks?
- [ ] Approved pip packages: onnxruntime-genai (incl. `--pre`?), onnxruntime, numpy, pandas, pydantic, streamlit, etc.
- [ ] Which Core Ultra series (NPU support in OpenVINO)?
- [ ] Leadership approval for running a local LLM on ticket data.

## Target B — personal laptop / cloud POC (fallback)
- Synthetic or public data only. Never real company tickets.
- Same codebase; swap the LLM adapter (local ONNX ↔ hosted API) by config.
- To fill in: hosting choice, API provider, cost, auth.
