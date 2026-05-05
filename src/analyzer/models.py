"""All domain models — kept in a single file for simplicity."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field, field_validator

# ---------------------------------------------------------------------------
# License
# ---------------------------------------------------------------------------


class LicenseCategory(StrEnum):
    """Broad classification used by strategies."""

    PERMISSIVE = "permissive"
    COPYLEFT = "copyleft"
    UNKNOWN = "unknown"


class LicenseInfo(BaseModel):
    """Extracted license metadata for a single file."""

    copyright_holder: str
    license_name: str
    category: LicenseCategory


# ---------------------------------------------------------------------------
# Functions
# ---------------------------------------------------------------------------


class FunctionSignature(BaseModel):
    """A single extracted function."""

    model_config = {"frozen": True}
    name: str
    num_args: int = Field(ge=0)


class FunctionList(BaseModel):
    """Collection of function signatures for one file."""

    functions: list[FunctionSignature] = Field(default_factory=list)
    total_count: int | None = None

    @field_validator("functions", mode="after")
    @classmethod
    def deduplicate(cls, v: list[FunctionSignature]) -> list[FunctionSignature]:
        seen = set()
        unique = []
        for fn in v:
            if fn not in seen:
                seen.add(fn)
                unique.append(fn)
        return unique

    @property
    def effective_count(self) -> int:
        """Return the raw count if available, otherwise the length of the deduplicated list."""
        return self.total_count if self.total_count is not None else len(self.functions)


# ---------------------------------------------------------------------------
# Rust rewrite
# ---------------------------------------------------------------------------


class RustRewrite(BaseModel):
    """Result of an LLM-based Rust translation."""

    rust_code: str
    source_file: str


# ---------------------------------------------------------------------------
# Analysis result (what the pipeline persists)
# ---------------------------------------------------------------------------


class AnalysisResult(BaseModel):
    """Final output for a single analysed file."""

    file: str
    license_info: LicenseInfo
    total_functions_in_file: int | None = None
    extracted_functions: list[FunctionSignature] | None = None
    rust_rewrite: RustRewrite | None = Field(default=None, exclude=True)
