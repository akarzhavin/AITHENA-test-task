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
    @pytest.mark.parametrize("category", [LicenseCategory.PERMISSIVE, LicenseCategory.COPYLEFT])
    def test_valid_categories(self, category):
        """Test validation of LicenseInfo for different valid license categories."""
        info = LicenseInfo(copyright_holder="Alice", license_name="Test", category=category)
        assert info.category == category

    def test_invalid_category_raises(self):
        """Test that invalid license category strings raise a ValueError."""
        with pytest.raises(ValueError):
            LicenseCategory("banana")


class TestFunctionSignature:
    def test_valid(self):
        """Test valid creation of a FunctionSignature model."""
        fn = FunctionSignature(name="foo", num_args=3)
        assert fn.name == "foo"
        assert fn.num_args == 3

    def test_negative_args_rejected(self):
        """Test that negative argument counts are rejected by Pydantic validation."""
        with pytest.raises(ValidationError):
            FunctionSignature(name="bad", num_args=-1)


class TestAnalysisResult:
    @pytest.fixture
    def base_info(self):
        return LicenseInfo(
            copyright_holder="X", license_name="MIT", category=LicenseCategory.PERMISSIVE
        )

    def test_result_variants(self, base_info):
        """Test AnalysisResult with different optional fields (functions, rust rewrite)."""
        # Minimal
        res_min = AnalysisResult(file="test.py", license_info=base_info)
        assert res_min.extracted_functions is None

        # With functions
        res_fn = AnalysisResult(
            file="test.py",
            license_info=base_info,
            extracted_functions=[FunctionSignature(name="f", num_args=1)],
        )
        assert res_fn.extracted_functions is not None
        assert len(res_fn.extracted_functions) == 1

        # With rust rewrite
        res_rs = AnalysisResult(
            file="test.py",
            license_info=base_info,
            rust_rewrite=RustRewrite(rust_code="fn main() {}", source_file="test.py"),
        )
        assert res_rs.rust_rewrite is not None
        assert res_rs.rust_rewrite.rust_code == "fn main() {}"
