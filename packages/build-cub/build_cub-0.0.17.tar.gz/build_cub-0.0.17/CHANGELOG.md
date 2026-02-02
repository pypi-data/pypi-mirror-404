# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v0.0.16](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.16) - 2026-02-01

<small>[Compare with v0.0.15](https://github.com/sicksubroutine/build-cub/compare/v0.0.15...v0.0.16)</small>

### Features

- add methods for dynamic source and argument management in settings (#11) ([e88c843](https://github.com/sicksubroutine/build-cub/commit/e88c843f4f95f14be98bf06ec68ba440c3a21fd0) by Chaz).

## [v0.0.15](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.15) - 2026-01-28

<small>[Compare with v0.0.14](https://github.com/sicksubroutine/build-cub/compare/v0.0.14...v0.0.15)</small>

### Bug Fixes

- disable compilation settings for general and Rust/PyO3 ([7c8c222](https://github.com/sicksubroutine/build-cub/commit/7c8c22273b6066469d0226653fc270cc0a477a4f) by chaz).
- enable compilation settings and improve message handling in backend processes (#10) ([940c2fa](https://github.com/sicksubroutine/build-cub/commit/940c2fae580239d514cf15ee91d568f6975c1187) by Chaz).

## [v0.0.14](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.14) - 2026-01-27

<small>[Compare with v0.0.13](https://github.com/sicksubroutine/build-cub/compare/v0.0.13...v0.0.14)</small>

### Bug Fixes

- disable Rust/PyO3 compilation and clean up configuration formatting ([40ce028](https://github.com/sicksubroutine/build-cub/commit/40ce0282c0235386b2cda095998b1ecb0e87434a) by chaz).

## [v0.0.13](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.13) - 2026-01-27

<small>[Compare with v0.0.12](https://github.com/sicksubroutine/build-cub/compare/v0.0.12...v0.0.13)</small>

### Bug Fixes

- refactor artifact handling and validation logic in build process (#9) ([912d0d0](https://github.com/sicksubroutine/build-cub/commit/912d0d0fcc3fb1987a480edef124978f392da01c) by Chaz).

## [v0.0.12](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.12) - 2026-01-25

<small>[Compare with v0.0.11](https://github.com/sicksubroutine/build-cub/compare/v0.0.11...v0.0.12)</small>

### Bug Fixes

- remove debug print statements from search_paths function ([5252993](https://github.com/sicksubroutine/build-cub/commit/5252993113b0c9f243b37eb9e1bf9c31c3e30539) by chaz).

## [v0.0.11](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.11) - 2026-01-25

<small>[Compare with v0.0.10](https://github.com/sicksubroutine/build-cub/compare/v0.0.10...v0.0.11)</small>

### Features

- enhance configuration management (#8) ([bf83b26](https://github.com/sicksubroutine/build-cub/commit/bf83b2632ef3c02cb2e11ab8747463ad12e2d1d7) by Chaz).

## [v0.0.10](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.10) - 2026-01-23

<small>[Compare with v0.0.9](https://github.com/sicksubroutine/build-cub/compare/v0.0.9...v0.0.10)</small>

### Bug Fixes

- update success message formatting and rename post artifact copy attribute ([44a73f1](https://github.com/sicksubroutine/build-cub/commit/44a73f16eeb3328ce3b1876c6dbd4dd503d2ae5d) by chaz).
- update setuptools version to 80.10.1 and simplify build command ([21d01d2](https://github.com/sicksubroutine/build-cub/commit/21d01d26ffcadf3c1c5adbd1b46f1a210608a055) by chaz).

## [v0.0.9](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.9) - 2026-01-23

<small>[Compare with v0.0.8](https://github.com/sicksubroutine/build-cub/compare/v0.0.8...v0.0.9)</small>

### Bug Fixes

- implement default behavior for pre and post execute hooks (#7) ([ec6bae2](https://github.com/sicksubroutine/build-cub/commit/ec6bae2501ada3a76544c4168a150910e552cfd2) by Chaz).

## [v0.0.8](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.8) - 2026-01-23

<small>[Compare with v0.0.7](https://github.com/sicksubroutine/build-cub/compare/v0.0.7...v0.0.8)</small>

### Bug Fixes

- update build command, disable Rust/PyO3 compilation, and clean up type hints ([88ae951](https://github.com/sicksubroutine/build-cub/commit/88ae95180391b36e50344b358a352634857009a4) by chaz).

## [v0.0.7](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.7) - 2026-01-23

<small>[Compare with v0.0.6](https://github.com/sicksubroutine/build-cub/compare/v0.0.6...v0.0.7)</small>

### Bug Fixes

- update build command to disable build isolation and improve type hints (#6) ([a4e6a45](https://github.com/sicksubroutine/build-cub/commit/a4e6a455d93ccd45b18e1d6de007673fa97b6d79) by Chaz).

## [v0.0.6](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.6) - 2026-01-23

<small>[Compare with v0.0.5](https://github.com/sicksubroutine/build-cub/compare/v0.0.5...v0.0.6)</small>

### Features

- add PyO3 backend for Rust extensions and update build config (#5) ([6fc3c8f](https://github.com/sicksubroutine/build-cub/commit/6fc3c8fffbdef91ba54ae1ba7216fe9242ac685e) by Chaz). Co-authored-by: Claude Opus 4.5 <noreply@anthropic.com>
- restore simple use of build cub hook into projects hatch build ([ec6f960](https://github.com/sicksubroutine/build-cub/commit/ec6f960695984c1f2abe86c5f1926919790cf65b) by chaz).

## [v0.0.5](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.5) - 2026-01-20

<small>[Compare with v0.0.4](https://github.com/sicksubroutine/build-cub/compare/v0.0.4...v0.0.5)</small>

## [v0.0.4](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.4) - 2026-01-20

<small>[Compare with v0.0.3](https://github.com/sicksubroutine/build-cub/compare/v0.0.3...v0.0.4)</small>

## [v0.0.3](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.3) - 2026-01-19

<small>[Compare with v0.0.2](https://github.com/sicksubroutine/build-cub/compare/v0.0.2...v0.0.3)</small>

### Features

- Refactor build process and enhance versioning support (#3) ([ce77c2a](https://github.com/sicksubroutine/build-cub/commit/ce77c2a747a57a12ceb8352361c6eb02d9440270) by Chaz).

## [v0.0.2](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.2) - 2026-01-18

<small>[Compare with v0.0.1](https://github.com/sicksubroutine/build-cub/compare/v0.0.1...v0.0.2)</small>

### Features

- Update build configuration and improve helper functions ([aae1019](https://github.com/sicksubroutine/build-cub/commit/aae1019b33882580e371ab6a4516e34be9d6694b) by chaz).
- Add GitHub Actions workflow for building and publishing packages (#2) ([488e57b](https://github.com/sicksubroutine/build-cub/commit/488e57bce9a858c6edd908ec7e8784c565ab52a4) by Chaz).
- Add C++ and Cython compilation backends with gperf support ([0a29180](https://github.com/sicksubroutine/build-cub/commit/0a29180406bfea2fc45f37a00feaea52bc0fd735) by chaz).

## [v0.0.1](https://github.com/sicksubroutine/build-cub/releases/tag/v0.0.1) - 2026-01-17

<small>[Compare with first commit](https://github.com/sicksubroutine/build-cub/compare/eb5e6d6d8a9e1b7078bdc427bb212a973cb4761f...v0.0.1)</small>
