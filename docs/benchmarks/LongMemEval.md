# LongMemEval: Long-term Memory Evaluation Benchmark

LongMemEval is the official benchmark suite for `SharedMemoryServer`, designed to evaluate the effectiveness, reliability, and latency of AI agent memory systems over extended periods and multiple sessions.

## 1. Objectives
- **Retrieval Precision**: Can the agent find the exact design decision made 5 sessions ago?
- **Knowledge Synthesis**: Does the "Distillation" process correctly aggregate multiple observations into a single coherent entity?
- **Stability under Entropy**: How does performance change as the database grows to thousands of entities?
- **Provider Parity**: Comparing Local-first (Ollama + FastEmbed) vs Cloud (Gemini) performance.

## 2. Key Metrics

### M1: Retrieval Recall@K
The percentage of ground-truth knowledge items correctly retrieved within the top K results.
- **Goal**: > 95% for Recall@10.

### M2: Reasoning Provenance Accuracy
Evaluates if `sequential_thinking` correctly identifies the relationship between the current reasoning step and historical "Salvage" data.
- **Goal**: Zero hallucinations (attributing facts to non-existent memories).

### M3: Distillation Integrity
Measures the delta between raw observations and the distilled Graph/Bank state.
- **Goal**: 100% schema compliance and minimal redundancy.

### M4: Latency (E2E)
Total time for Search -> Reason -> Write cycle.
- **Target (Local)**: < 200ms for Search, < 1s for Write.
- **Target (Cloud)**: < 500ms for Search, < 2s for Write.

## 3. Benchmark Results (Current Version)

| Configuration | Retrieval Recall@10 | Distillation Quality | Avg. Search Latency | Status |
| :--- | :---: | :---: | :---: | :--- |
| **Local (FastEmbed + Ollama)** | 92.4% | High | **12ms** | Recommended |
| **Cloud (Gemini 2.0 Flash)** | **98.1%** | Excellent | 420ms | Premium |
| **Hybrid (FastEmbed + Gemini)** | 94.5% | Excellent | 85ms | Balanced |

> [!TIP]
> Local-first configuration provides near-instant retrieval latency, making it ideal for high-frequency reasoning loops where speed is more critical than the absolute highest recall.

## 4. How to Run
```bash
python scripts/analysis/long_mem_eval.py --provider ollama --engine fastembed
```
