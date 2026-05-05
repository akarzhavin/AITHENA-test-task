from analyzer.models import LicenseCategory

# Map common SPDX identifiers to our categories
# This acts as a 'knowledge base' for the SmartLicenseExtractor
SPDX_CATEGORY_MAP = {
    "MIT": LicenseCategory.PERMISSIVE,
    "APACHE-2.0": LicenseCategory.PERMISSIVE,
    "BSD-3-CLAUSE": LicenseCategory.PERMISSIVE,
    "BSD-2-CLAUSE": LicenseCategory.PERMISSIVE,
    "ISC": LicenseCategory.PERMISSIVE,
    "GPL-2.0-ONLY": LicenseCategory.COPYLEFT,
    "GPL-2.0-OR-LATER": LicenseCategory.COPYLEFT,
    "GPL-3.0-ONLY": LicenseCategory.COPYLEFT,
    "GPL-3.0-OR-LATER": LicenseCategory.COPYLEFT,
    "AGPL-3.0-ONLY": LicenseCategory.COPYLEFT,
    "AGPL-3.0-OR-LATER": LicenseCategory.COPYLEFT,
    "LGPL-2.1-ONLY": LicenseCategory.COPYLEFT,
    "LGPL-2.1-OR-LATER": LicenseCategory.COPYLEFT,
    "LGPL-3.0-ONLY": LicenseCategory.COPYLEFT,
    "LGPL-3.0-OR-LATER": LicenseCategory.COPYLEFT,
}
