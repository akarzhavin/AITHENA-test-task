"""Unit tests for domain models."""

import pytest
from pydantic import ValidationError

from analyzer.models import (
    AnalysisResult,
    FunctionSignature,
    LicenseCategory,
    LicenseInfo,
    RustRewrite,
)


class TestLicenseInfo:
    def test_valid_permissive(self):
        info = LicenseInfo(
            copyright_holder="Alice",
            license_name="MIT",
            category=LicenseCategory.PERMISSIVE,
        )
        assert info.category == LicenseCategory.PERMISSIVE

    def test_valid_copyleft(self):
        info = LicenseInfo(
            copyright_holder="Bob",
            license_name="GPL-3.0",
            category=LicenseCategory.COPYLEFT,
        )
        assert info.category == LicenseCategory.COPYLEFT

    def test_invalid_category_raises(self):
        with pytest.raises(ValueError):
            LicenseCategory("banana")


class TestFunctionSignature:
    def test_valid(self):
        fn = FunctionSignature(name="foo", num_args=3)
        assert fn.name == "foo"
        assert fn.num_args == 3

    def test_negative_args_rejected(self):
        with pytest.raises(ValidationError):
            FunctionSignature(name="bad", num_args=-1)


class TestAnalysisResult:
    def test_minimal(self):
        result = AnalysisResult(
            file="test.py",
            license_info=LicenseInfo(
                copyright_holder="X",
                license_name="MIT",
                category=LicenseCategory.PERMISSIVE,
            ),
        )
        assert result.extracted_functions is None
        assert result.rust_rewrite is None

    def test_with_functions(self):
        result = AnalysisResult(
            file="test.py",
            license_info=LicenseInfo(
                copyright_holder="X",
                license_name="MIT",
                category=LicenseCategory.PERMISSIVE,
            ),
            extracted_functions=[FunctionSignature(name="f", num_args=1)],
        )
        assert result.extracted_functions is not None
        assert len(result.extracted_functions) == 1

    def test_with_rust_rewrite(self):
        result = AnalysisResult(
            file="test.py",
            license_info=LicenseInfo(
                copyright_holder="X",
                license_name="GPL-3.0",
                category=LicenseCategory.COPYLEFT,
            ),
            rust_rewrite=RustRewrite(rust_code="fn main() {}", source_file="test.py"),
        )
        assert result.rust_rewrite is not None
        assert result.rust_rewrite.rust_code == "fn main() {}"
