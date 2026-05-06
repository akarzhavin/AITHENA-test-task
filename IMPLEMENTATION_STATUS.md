# Questions for the Technical Specifications & Implementation Status

## 1. Architecture and Infrastructure (System Design)

### 1.1. Scale, Scaling and Cost
- **[✅ Resolved]** What is the expected volume of input data? 
  - **Decision:** Serial processing is chosen for simplicity and reliability. Given the small-scale nature of the project, parallelization is deferred as premature optimization.
- **[✅ Done]** Are there budget constraints on API calls? We implemented **SPDX Fast-Path** and **Micro-snippets** to drastically reduce LLM token usage.
- **[✅ Resolved]** File size (Context Window Limit):
  - **Decision:** Current models (Gemini/GPT-4o) handle large files natively. No chunking implemented to avoid complexity.
- **[✅ Resolved]** Time constraints (SLA):
  - **Decision:** No strict SLA requirements. Sequential processing is preferred for better error tracking and rate-limit management.

### 1.2. LLM Infrastructure, Security and Deployment
- **[✅ Done]** Should the LLM provider be replaceable/abstracted? Yes, implemented via `LLMClient` protocol.
- **[✅ Done]** Support for local LLMs? Abstracted architecture allows swapping Gemini for local Ollama/Llama3 providers.
- **[✅ Done]** Determinism: Default `temperature=0.0` is used for all analysis calls to ensure consistent results.
- **[✅ Done]** Prompt Isolation and Basic Protection:
  - Prompts are stored in a dedicated `prompts.py` file.
  - Safe substitution via `string.Template` prevents conflicts with code curly braces.
  - Security instruction included to ignore any commands inside `<SOURCE_CODE>` tags.

### 1.3. Fault Tolerance and Idempotency
- **[✅ Done]** Checkpointing/Idempotency: Implemented via output file existence check.
- **[✅ Done]** Incorrect/invalid LLM response: Handled via JSON Mode and Retry Mechanism.
- **[✅ Done]** Unreadable/binary files: Handled via `UnicodeDecodeError` catch and skip.
- **[✅ Done]** Partial output: Results are written to disk as they are processed, ensuring partial success is saved.

### 1.4. Component Selection: LLM vs. Deterministic Algorithms
- **[✅ Done]** Hybrid approach (Fallback): Implemented! Priority fast parsing (AST/SPDX) with switching to LLM/Regex for errors.

---

## 2. Business Logic Detailing and Success Criteria

### 2.1. License Classification
- **[✅ Done]** Files without a license: Handled via `LicenseCategory.UNKNOWN`.
- **[✅ Done]** Ready-made database (SPDX): Implemented `SPDX_CATEGORY_MAP` for deterministic classification.
- **[✅ Done]** Proprietary/Commercial licenses: Handled via `LicenseCategory.UNKNOWN`.
- **[✅ Done]** MPL Classification: Explicitly mapped and tested as `copyleft`.
- **[✅ Resolved]** Dual-license files:
  - **Decision:** "First-match wins" strategy. The first detected valid license determines the category.

### 2.2. Function Extraction
- **[✅ Done]** Nested functions, lambdas, class methods: Handled by AST (Python) and LLM (others).
- **[✅ Done]** Variadic arguments: Counted as single arguments in AST/LLM.
- **[✅ Done]** Language support: Full support for Python and JS (including JSX/TSX).
- **[✅ Resolved]** File 3.py contains JS: **Resolved via Fallback.** Pipeline detects SyntaxError in AST and successfully falls back to LLM/Regex.
- **[✅ Done]** No functions in file: Handled gracefully (returns 0/empty list).
- **[✅ Done]** Overloaded/Overridden functions: Unique signatures are counted; exact duplicates (same name and arg count) are removed via `FunctionList` validator.
- **[✅ Done]** Duplicate definitions in `2.py`: Automatically handled by `FunctionList.deduplicate`.

### 2.3. Rewriting in Rust
- **[✅ Resolved]** Success criterion: **Syntactic Draft (Best-effort)**. The goal is to preserve logic and structure; full compilability is not guaranteed without dependency resolution.
- **[✅ Resolved]** Frameworks (Django/React): LLM performs a best-effort rewrite of the core logic.