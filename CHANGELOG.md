# Changelog

All notable changes to Art Factory will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-06-09

### Added

#### Core Features
- **Model-specific parameter defaults** - Dynamic parameter forms that adapt to each AI model's requirements, fixing compatibility issues with FLUX models (#2)
- **Batch generation support** - Efficient multi-image generation using provider batch capabilities, reducing API calls from N to N/batch_size (#14)
- **Inventory management** - Download and delete functionality for generated products with bulk operations support (#11)
- **Order status visibility** - Real-time status updates and user notifications for order processing with toast notifications (#12)
- **Comprehensive error handling** - Graceful failure recovery with user-friendly error messages and retry capabilities (#13)

#### UI/UX Improvements
- **Bootstrap 5 migration** - Complete UI overhaul using Bootstrap 5 for consistent, responsive design across all pages (#10)
- **Enhanced order page layout** - Preview area, live product updates, and improved visual hierarchy following UX specifications (#3)
- **Refined notification system** - Consistent toast notifications and error banners with Bootstrap integration (#15)

#### Infrastructure
- **CI/CD pipeline** - GitHub Actions workflow with matrix testing (Python 3.11/3.12), code quality checks, and security scanning (#32)
- **Test coverage reporting** - Coverage.py integration with 44% coverage achieved, HTML/XML reports, and CI integration (#29)
- **Comprehensive test suite** - Factory machine tests, error handling tests, and batch generation tests (#30, #31)

### Fixed
- **Non-SDXL model failures** - Fixed parameter schema mismatches preventing FLUX model generation (#1)
- **Orphaned orders** - Added transaction-based order creation to prevent orders without OrderItems (#9)
- **Test suite failures** - Updated tests for batch generation architecture and removed async processing expectations (#26)

### Security
- Security vulnerabilities in dependencies resolved through CI/CD security scanning implementation

### Documentation
- Test coverage usage documented in `docs/testing.md`
- CI/CD pipeline configuration and usage documented

## [Unreleased]

See the [v0.1 MVP milestone](https://github.com/bendavieshe3/art-factory/milestone/1) for remaining issues.

[0.1.0]: https://github.com/bendavieshe3/art-factory/releases/tag/v0.1.0