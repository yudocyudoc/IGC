# Upstream notice — University at Buffalo SD-AI

The adjacent prompt is extracted **without editing process instructions** from the MIT-licensed [UB-IAD/sd-ai](https://github.com/UB-IAD/sd-ai) quantitative engine, exact upstream commit `5199f7b45f3a7ae4a773cb0dd8542940aabe9edc` (`engines/quantitative/QuantitativeEngineBrain.js`).

It uses `generateSystemPrompt(false, false, false, false)`: professional mode, scalar models, no modules, no arrays, no discrete sub-types; these are upstream feature switches. The original engine defaults may differ. This file is a **prompt-port of Buffalo's engine methodology**, not a copy of its whole NodeJS runtime or a claim of numerical parity with its original provider. An additional request wrapper does not modify this system prompt.

Process prompt SHA256 recorded by unit tests, original MIT license in `data/buffalo-sdai/LICENSE`.
