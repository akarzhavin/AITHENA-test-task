# Future Tasks and Feature Ideas (TODO)

This document tracks planned improvements, technical debt, and potential new features for the License & Code Analysis Pipeline.

## 🚀 Performance & Scaling
- [ ] 🔴 **[High] Parallel Processing**: Implement `asyncio.gather`, a **task queue**, or a worker pool in `AnalysisPipeline` to process multiple files concurrently.
- [ ] 🔴 **[High] Context Window Management (Token Counting)**: Integrate `tiktoken` to count tokens in source code *before* sending requests. Implement strategies to skip, truncate, or chunk files that exceed model limits to prevent API errors.
- [ ] 🟡 **[Medium] Rate-Limit Handling**: Add a semaphore or token-bucket rate limiter to manage LLM API usage during parallel runs.
- [ ] 🟡 **[Medium] OpenAI Batch API Integration**: Add an alternative execution mode that generates a `.jsonl` request file and uses the OpenAI Batch API. Reduces costs by 50% and provides higher rate limits.


## 🧠 LLM & Intelligence
- [ ] 🟡 **[Medium] Local LLM Integration**: Provide a concrete implementation of `LLMClient` for [Ollama](https://ollama.com/) or [vLLM](https://github.com/vllm-project/vllm) to allow 100% offline analysis.
- [ ] 🟡 **[Medium] Model Fallback Chain**: Extend `ResilientLLMClient` to support automatic fallback to a secondary model (e.g., from `gpt-4o` to `gpt-4o-mini`) if the primary model is unavailable or rate-limited.

## 🛠 Features & Architecture
- [ ] 🔴 **[High] Professional License Detection**: Integrate **scancode-toolkit** as a primary fast-path for license and copyright identification to reduce reliance on custom regex and LLMs.
- [ ] 🟡 **[Medium] Additional Language Support**: Replace Python's `ast` module with **Tree-sitter** to support multiple languages (Go, C++, Java, etc.) with a single, high-performance parser.
- [ ] 🟡 **[Medium] Observability & Cost Tracking**: Collect statistics on `prompt_tokens` and `completion_tokens` from API responses.
- [ ] 🔵 **[Low] Advanced Deduplication**: Improve `FunctionList` logic to handle class-method shadowing and overloading in a more language-aware manner.
- [ ] 🔵 **[Low] Tracing Integration**: Integrate OpenTelemetry, LangSmith, or Langfuse to visualize LLM call durations and Pydantic validation failures.

## 🛡 Security & Quality
- [ ] 🔴 **[High] Prompt Injection Sanitization**: Escaping or removing `<SOURCE_CODE>` tags from the input source code before template substitution to prevent "jailbreaking" and instruction overriding.
- [ ] 🔴 **[High] Resilience to Broken Code**: Expand tests with cases of malformed, partial, or syntactically incorrect source code to ensure 100% robust fallback behavior.
- [ ] 🟡 **[Medium] Input Filtering**: Implement a whitelist of supported file extensions (`.py`, `.js`, `.ts`, `.jsx`, `.tsx`) in `AnalysisPipeline` to avoid wasting resources on irrelevant files (e.g. `.css`, `.json`, `.md`).
- [ ] 🟡 **[Medium] Matrix Testing**: Implement a combinatorial testing suite to verify stability across different dimensions (languages, license types, file sizes, and LLM models).
- [ ] 🟡 **[Medium] Hardened File I/O**: Implement protections against path traversal (symlink checks), memory exhaustion (size limits), and improve encoding robustness (`utf-8-sig`) in `AnalysisPipeline`.
- [ ] 🔵 **[Low] Rust Verification**: Add an optional validation step that tries to run `cargo check` on the generated code and provides feedback to the LLM for self-correction.
