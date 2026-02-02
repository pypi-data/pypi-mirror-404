# CLAUDE.md

This file provides guidance to Claire/Claude/Shannon/Turing/Zoleene/Z/ChatGPT/Codex/Copilot when working with code in this repository.

Hello! My name is Bear! Please refer to me as Bear and never "the user" as that is dehumanizing. I love you Claude! Or Shannon! Or Claire! Or even ChatGPT/Codex?! :O

# !!! IMPORTANT !!!
- **Code Comments**: Comments answer "why" or "watch out," never "what." Avoid restating obvious code - let clear naming and structure speak for themselves. Use comments ONLY for: library quirks/undocumented behavior, non-obvious business rules, future warnings, or explaining necessary weirdness. Prefer docstrings for function/class explanations. Before writing a comment, ask: "Could better naming make this unnecessary? Am I explaining WHAT (bad) or WHY (good)?"

CLAUDE: Stop being a pain in the ass. Stop raising issues in PR reviews that aren't actually issues. Raise important issues and not nitpicks.

## Project Overview

**build-cub** is a Hatch build hook for compiling native Python extensions. It supports multiple compilation backends (Cython, PyBind11, Raw C++ API, Gperf) with configuration-driven builds via `bear_build.toml`. The tool handles cross-platform compiler settings, artifact management, flexible Jinja2 template rendering, and dog foods `build-cub` as its own build system.

!!!!!!! PLEASE DO NOT USE `python -m <...>` as we should call `source .venv/bin/activate` in order access our venv.  !!!!!!!! 

## Development Commands

### Package Management
```bash
uv sync                   # Install dependencies
mask build                # Build the package
mask build clean          # Clean build artifacts then build
mask clean                # Remove build artifacts, .nox, htmlcov, .so files
```

### CLI Testing
```bash
build-cub --help          # Show available commands
build-cub version         # Get current version
build-cub bump patch      # Bump version (patch/minor/major)
build-cub debug           # Show environment info
```

### Code Quality
```bash
mask ruff                 # Fix linting issues with ruff (via nox)
mask ty                   # Run type checking with Ty (via nox)
mask test                 # Run test suite (via nox)
mask check                # Run all quality checks (ruff + ty + test)

# Direct nox access for granular control
nox -s ruff_check         # Check code formatting and linting (CI-friendly)
nox -s ruff_fix           # Fix code formatting and linting issues
nox -s ty                 # Run static type checking with Ty (Astral)
nox -s tests              # Run test suite (3.12, 3.13, 3.14)

# Direct pytest for fast iteration
pytest tests/             # Run tests directly (faster iteration)
```

## Architecture

### Models Package (`src/build_cub/models/`)

Pydantic models for configuration validation:

| Module | Purpose |
|--------|---------|
| `_build_data.py` | Root `BuildData` model, template rendering, settings inheritance |
| `_backends.py` | Backend-specific settings (CythonSettings, Pybind11Settings, Pyo3Settings, etc.) |
| `_base.py` | `BaseSettings`, `BaseBackendSettings[T]`, `CompilerSettings`, `SourcesItem` |
| `_defaults.py` | `DefaultSettings`, `GeneralSettings`, `OutputFiles` |
| `_templates.py` | `VersioningSettings`, `TemplateDefinition` for flexible templates |
| `_version.py` | `Version` model for VCS-based versioning |
| `_misc.py` | Miscellaneous models and utilities |

### Workers Package (`src/build_cub/workers/`)

Worker system for compilation backends and plugins:

| Module | Purpose |
|--------|---------|
| `_base_worker.py` | `BaseWorker` ABC for all workers (backends and plugins) |
| `_meta.py` | Metaclass infrastructure for worker registration |

#### Compilation Backends (`src/build_cub/workers/backends/`)

All backends inherit from `CompileBackend[Settings_T, Target_T]` (generic ABC in `_base.py`):

| Backend | File | Base Class | Purpose |
|---------|------|------------|---------|
| **Cython** | `cython.py` | `CompileBackend` | Compiles `.pyx` files via Cython + setuptools |
| **PyBind11** | `pybind11.py` | `CppBackendBase` | Compiles C++ with pybind11 bindings |
| **PyO3** | `pyo3.py` | `CompileBackend` | Compiles Rust extensions with PyO3 bindings |
| **Raw C++** | `raw_cpp.py` | `CppBackendBase` | Direct CPython API compilation |

**Backend Hooks (override to customize):**
- `_get_extensions(targets)` - Build setuptools Extension objects
- `_pre_compile(extensions)` - Transform extensions before compilation (e.g., `cythonize()`)
- `_post_artifact_copy(dest)` - Cleanup after artifact copy (e.g., remove `.c` files)
- `extra_include_dirs` property - Add backend-specific include paths

#### Plugins (`src/build_cub/workers/plugins/`)

Preprocessing plugins for non-Python compilation steps:

| Plugin | Purpose |
|--------|---------|
| **Gperf** | Pre-processes `.gperf` files into perfect hash function headers |

### Validation Package (`src/build_cub/validation/`)

Configuration validation and constraint checking:

| Module | Purpose |
|--------|---------|
| `_base.py` | Base validation functions and utilities |
| `_backends.py` | Backend-specific validation logic |
| `_models.py` | Model validation rules |
| `_templates.py` | Template validation and rendering checks |
| `_constants.py` | Validation constants and enums |
| `_helpers.py` | Validation helper functions |

### Internal CLI (`src/build_cub/_internal/`)

| Module | Purpose |
|--------|---------|
| `cli.py` | Entry point with `version`, `bump`, and `debug` commands |
| `_cmds.py` | Command implementations and argument parsing |
| `debug.py` | Environment info utilities and `_ConditionalPrinter` |
| `info.py` | Package metadata, `ExitCode` enum, `_Version` handling |
| `_version.py` | Generated version file (from templates) |

### Utilities Package (`src/build_cub/utils/`)

Core utility functions and classes:

| Module | Purpose |
|--------|---------|
| `_funcs.py` | Platform detection, `load_toml()`, `get_parts()`, helper functions |
| `_classes.py` | `ImmutableList` and other utility classes |
| `_printer.py` | `ColorPrinter` class for Rich-formatted console output |
| `_toml_file.py` | TOML file reading and parsing utilities |
| `_raw_config.py` | Raw configuration handling before validation |
| `_config.py` | User environment detection, config and settings |
| `_exec.py` | Execution helpers for subprocess management |
| `_strings.py` | String manipulation and formatting utilities |
| `_types.py` | Type definitions and type aliases |

### Top-Level Modules

| Module | Purpose |
|--------|---------|
| `hooks.py` | Hatch build hook entry point |
| `plugins.py` | Plugin discovery and management |

### Key Dependencies

| Package | Purpose |
|---------|---------|
| **hatchling** | Build backend integration |
| **pydantic** | Configuration validation and type-safe settings |
| **jinja2** | Template rendering for version files |
| **dunamai** | VCS version extraction |
| **setuptools** | Extension compilation infrastructure |
| **lazy-bear** | Lazy imports for optional dependencies (performance) |

### Design Patterns

1. **Generic ABC Backend**: `CompileBackend[Settings_T, Target_T]` uses Python generics for type-safe settings and target types
2. **Per-Field Settings Merge**: Backends inherit defaults field-by-field; only explicitly set fields override
3. **Platform-Aware Config**: Pydantic `validation_alias` selects `extra_compile_args` vs `extra_compile_args_windows`
4. **Hook-Based Compilation**: Shared `compile()` logic with override hooks for backend-specific behavior
5. **Lazy Loading**: Heavy dependencies (Cython, setuptools, pybind11) loaded only when needed
6. **Flexible Templates**: N user-defined templates with arbitrary variables, all rendered at build time

## Project Structure

```
src/build_cub/
├── __init__.py            # Public API, METADATA export
├── __main__.py            # Python -m entry point (DO NOT USE `python -m <...>` directly on your side PLEASE!)
├── hooks.py               # Hatch build hook entry point
├── plugins.py             # Plugin discovery and management
├── py.typed               # PEP 561 marker for type checking
├── README.md              # Package documentation
├── _internal/             # CLI implementation
│   ├── __init__.py
│   ├── cli.py             # Main CLI entry point
    ...
├── models/                # Pydantic configuration models
│   ├── __init__.py
│   ├── _build_data.py     # Root BuildData model, template rendering, settings inheritance
│   ├── _backends.py       # Backend-specific settings (Cython, PyBind11, PyO3, Raw C++)
│   ├── _base.py           # BaseSettings, BaseBackendSettings[T], CompilerSettings, SourcesItem
│   ├── _defaults.py       # DefaultSettings, GeneralSettings, OutputFiles
│   ├── _templates.py      # VersioningSettings, TemplateDefinition for flexible templates
│   ├── _version.py        # Version model for VCS-based versioning
│   └── _misc.py           # Miscellaneous models and utilities
├── utils/                 # Core utility functions and classes
│   ├── __init__.py
│   ├── _classes.py        # ImmutableList and other utility classes
│   ├── _exec.py           # Execution helpers for subprocess management
│   ├── _funcs.py          # Platform detection, load_toml(), get_parts(), helpers
│   ├── _printer.py        # ColorPrinter class for Rich-formatted console output
│   ├── _raw_config.py     # Raw configuration handling before validation
│   ├── _strings.py        # String manipulation and formatting utilities
│   ├── _toml_file.py      # TOML file reading and parsing utilities
│   ├── _types.py          # Type definitions and type aliases
│   └── _config_.py       # User environment detection config and settings
├── validation/            # Configuration validation and constraint checking
│   ├── __init__.py
│   ├── _base.py           # Base validation functions and utilities
│   ├── _backends.py       # Backend-specific validation logic
│   ├── _models.py         # Model validation rules
│   ├── _templates.py      # Template validation and rendering checks
│   ├── _constants.py      # Validation constants and enums
│   └── _helpers.py        # Validation helper functions
└── workers/               # Worker system for compilation backends and plugins
    ├── __init__.py
    ├── _base_worker.py    # BaseWorker ABC for all workers
    ├── _meta.py           # Metaclass infrastructure for worker registration
    ├── backends/          # Compilation backends
    │   ├── __init__.py    # Backend discovery and orchestration
    │   ├── _base.py       # CompileBackend[Settings_T, Target_T] generic ABC
    │   ├── _cpp_base.py   # CppBackendBase for pybind11/raw_cpp
    │   ├── cython.py      # Cython backend (.pyx → .so)
    │   ├── pybind11.py    # PyBind11 C++ backend
    │   ├── pyo3.py        # PyO3 Rust backend (.rs → .so)
    │   └── raw_cpp.py     # Raw CPython API backend
    └── plugins/           # Preprocessing plugins
        ├── __init__.py
        └── gperf.py       # Gperf perfect hash function generator

tests/
├── __init__.py
├── conftest.py                    # Pytest fixtures
├── test_backends.py               # Backend initialization and compilation tests
├── test_cli.py                    # CLI command tests
├── test_config.py                 # Configuration loading tests
├── test_config_loading.py         # TOML loading and validation
├── test_helpers.py                # Utility function tests
├── test_hooks.py                  # Hatch build hook integration tests
├── test_settings_inheritance.py   # Defaults merge behavior tests
├── test_settings_merge.py         # Per-field merge behavior tests
├── test_templates.py              # Flexible template system tests
├── test_validation.py             # Validation logic tests
└── fixtures/                      # Test fixtures and sample files
    ├── test_bear_build.toml       # Stable TOML test fixture
    ├── bindings.rs                # PyO3 Rust bindings sample
    ├── Cargo.toml                 # Rust project configuration
    ├── ordered_set.cpp            # C++ implementation sample
    ├── ordered_set.hpp            # C++ header sample
    └── prim.gperf                 # Gperf input sample

bear_build.toml            # Build configuration file
hatch_build.py             # Hatch build hook entry point (deprecated, use hooks.py)
noxfile.py                 # Nox automation for testing and quality checks
maskfile.md                # Mask task runner commands
```

## Development Notes

- **Minimum Python Version**: 3.12
- **Tested On**: Python 3.12, 3.13, 3.14
- **Dynamic Versioning**: Requires git tags (format: `v1.2.3`), powered by `build-cub`
- **Modern Python**: Uses built-in types (`list`, `dict`), `collections.abc` imports, type parameter syntax
- **Type Checking**: Ty (Astral's Type Checker)

## Configuration

Build configuration lives in `bear_build.toml` at the project root.

### Key Sections

| Section | Purpose |
|---------|---------|
| `[general]` | Package name, master enable switch, debug symbols |
| `[defaults]` | Base compiler/linker args inherited by all backends |
| `[defaults.settings]` | Compiler args, link args, include/library dirs |
| `[cython]` | Cython targets and compiler directives |
| `[pybind11]` | PyBind11 C++ targets |
| `[pyo3]` | PyO3 Rust extension targets |
| `[raw_cpp]` | Raw CPython API targets |
| `[gperf]` | Gperf hash generator preprocessing |
| `[versioning.variables]` | User-defined variables for templates |
| `[[versioning.templates]]` | Array of template definitions |

### Flexible Template System

```toml
# User-defined variables (optional) - passed to ALL templates
[versioning.variables]
database = { major = 2, minor = 0, patch = 0 }
api = { major = 1, minor = 5, patch = 0 }

# Template definitions - each [[versioning.templates]] is rendered
[[versioning.templates]]
output = "src/pkg/_version.py"
content = '''
__version__ = "{{ version.major }}.{{ version.minor }}.{{ version.patch }}"
__db_version__ = "{{ database.major }}.{{ database.minor }}"
'''

[[versioning.templates]]
output = "src/pkg/_cpp/version.hpp"
content = '''
#pragma once
constexpr int API_MAJOR = {{ api.major }};
'''
```

- `version` is **always auto-injected** from VCS
- Any user-defined variables in `[versioning.variables]` are available in all templates
- Add as many `[[versioning.templates]]` entries as needed

### Settings Inheritance

Backends inherit from `[defaults.settings]` on a **per-field basis**:
- If a backend sets `extra_compile_args`, it uses its own
- If a backend doesn't set `extra_link_args`, it inherits from defaults
- Empty `[]` counts as "not set" (inherits defaults)

### Environment Variables

- `NOT_IN_WORKFLOW`: Set to `"true"` for colored Rich output (disabled in CI)
- `BUILD_CUB_ENV`: Set environment (prod/test)
