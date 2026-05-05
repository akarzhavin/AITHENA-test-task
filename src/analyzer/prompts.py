"""All LLM prompt templates — single source of truth."""

from llama_index.core.prompts import PromptTemplate

# ---------------------------------------------------------------------------
# License extraction
# ---------------------------------------------------------------------------

LICENSE_EXTRACTION_PROMPT = PromptTemplate(
    "Analyse the following source code and extract the license information.\n"
    "\n"
    "Rules for category:\n"
    '- MIT, BSD, Apache, ISC, Unlicense → "permissive"\n'
    '- GPL, LGPL, AGPL, MPL, CC-BY-SA → "copyleft"\n'
    '- Anything else or unclear → "unknown"\n'
    "\n"
    "Source code:\n"
    "```\n"
    "{source_code}\n"
    "```\n"
)

# ---------------------------------------------------------------------------
# Function extraction
# ---------------------------------------------------------------------------

FUNCTION_EXTRACTION_PROMPT = PromptTemplate(
    "Analyse the following source code and extract all function definitions.\n"
    "Exclude `self` when counting method arguments.\n"
    "\n"
    "Source code:\n"
    "```\n"
    "{source_code}\n"
    "```\n"
)

# ---------------------------------------------------------------------------
# Rust rewriting
# ---------------------------------------------------------------------------

RUST_REWRITE_PROMPT = PromptTemplate(
    "Rewrite the following source code in Rust.\n"
    "Produce idiomatic, safe Rust code that preserves the original behaviour.\n"
    "Return ONLY the Rust source code, with no markdown fences or explanation.\n"
    "\n"
    "Source code:\n"
    "```\n"
    "{source_code}\n"
    "```\n"
)
