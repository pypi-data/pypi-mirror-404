# hallu-assess

Measure how much an LLM’s answers drift to detect hallucination risk and improve prompts for more reliable outputs.

## What it does

`hallu-assess` evaluates hallucination risk by:
- running the same prompt multiple times
- embedding each response
- measuring semantic deviation across outputs

High deviation → higher hallucination risk.

## Installation

```bash
pip install hallu-assess
```
## Detailed Documentation - WIP