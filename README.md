# AITHENA Code Analyzer 🚀

Production-grade code analysis pipeline for automated license identification, function signature extraction, and code translation.

## 🌟 Key Features

- **Smart License Identification**: Three-layer architecture (SPDX fast-path, micro-snippet LLM fallback, and full-file analysis) for high accuracy and low cost.
- **Language-Agnostic Extraction**: 
    - **Python**: High-speed AST parsing for 100% accurate function counting and signature extraction.
    - **Other Languages (JS, C++, Rust, etc.)**: Intelligent LLM-based fallback for function identification.
- **Strategy-Based Processing**: 
    - **Permissive Licenses**: Automatic function signature extraction into JSON.
    - **Copyleft Licenses**: Threshold-based branching (>2 functions → extract signatures; ≤2 functions → **automatic rewrite to Rust**).
- **Production-Grade Reliability**: Built-in retry mechanisms, type safety with Pydantic v2, and idempotency (skips already processed files).
- **High Test Coverage**: Robust unit, integration, and acceptance test suites.

## 🛠 Tech Stack

- **Core**: Python 3.12+
- **LLM Orchestration**: OpenAI SDK (Structured Outputs)
- **Data Validation**: Pydantic v2
- **Testing**: Pytest & Asyncio
- **Rewriting Engine**: LLM-powered Rust translation

## 🚀 Getting Started

### 1. Prerequisites
- Python 3.12
- OpenAI API Key

### 2. Installation
```bash
# Clone the repository
git clone git@github.com:akarzhavin/AITHENA-test-task.git
cd AITHENA-test-task

# Install dependencies using Makefile
make setup
```

### 3. Configuration
Create a `.env` file in the root directory:
```env
OPENAI_API_KEY=your_key_here
# Optional tunables
OPENAI_MODEL=gpt-4o-mini
COPYLEFT_FUNCTION_THRESHOLD=2
```

### 4. Running the Pipeline
Place your source files in the `data/` directory and run:
```bash
# Run via Makefile
make run

# Or directly
python -m analyzer
```
Results will be saved in the `output/` directory as JSON files (and `.rs` files for Rust rewrites).

## 🧪 Testing

```bash
# Run all tests
make test

# Run with coverage report
pytest --cov=src
```

## 🏗 Architecture

The project follows a modular, strategy-based architecture:
- `extractors/`: Smart components for license and function identification.
- `strategies/`: Domain logic for different license categories.
- `transformers/`: Code-to-code translation logic (e.g., Rust rewriter).
- `persistence/`: Pluggable writers for results (JSON, etc.).

## 📝 Assumptions

A duplicate of the `bar1` function was found in one of the source files. Since the requirements do not specify how to handle this case, the decision was made to deduplicate functions during the structured data generation phase, as the Python interpreter itself overwrites previous definitions with the latest one.

---
*Created as part of the AITHENA Technical Task.*
