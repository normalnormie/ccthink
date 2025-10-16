# Changelog

All notable changes to this project will be documented in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.7.1] - 2025-10-12

### Refactoring

- Renamed `sonnet_colors` to `colors` for global color control across all display modes

## [0.7.0] - 2025-10-12

### Features

- CLI flags for chat text control with renamed `chat_text_enabled` configuration

### Refactoring

- Renamed `text_enabled` to `chat_text_enabled` for clarity

## [0.6.0] - 2025-10-12

### Features

- Configurable thinking and chat text colors with fallback logic for display customization

## [0.5.0] - 2025-10-12

### Features

- CSS/hex to ANSI 256 color converter utility for flexible color specification

## [0.4.7] - 2025-10-06

### Bug Fixes

- Separator now appears between thinking and text sections in display output

## [0.4.6] - 2025-10-06

### Testing

- Directory structure for process_thinking handler testing

## [0.4.5] - 2025-10-06

### Bug Fixes

- Content accumulation from batched entries no longer drops remainder data

## [0.4.4] - 2025-10-06

### Bug Fixes

- Duplicate thinking display no longer occurs; both content types process properly

## [0.4.3] - 2025-10-06

### Bug Fixes

- Git commit messages no longer contain ANSI color codes that cause formatting issues

## [0.4.2] - 2025-10-06

### Performance

- Double compression no longer occurs; compression happens once and result is reused

## [0.4.1] - 2025-10-06

### Bug Fixes

- Merge error handling and branch validation provide safer git operations

## [0.4.0] - 2025-10-06

### Features

- Dual content type support enabling simultaneous processing of thinking and text content

### Refactoring

- Renamed configuration fields for dual content type support

## [0.3.1] - 2025-10-04

### Bug Fixes

- Circuit breaker prevents infinite loops on SDK failures

## [0.3.0] - 2025-10-04

### Features

- JSON-repair fallback mechanism handles LLM-generated invalid JSON responses

## [0.2.0] - 2025-10-03

### Features

- Tool use display in chronological order alongside thinking output for better debugging

## [0.1.7] - 2025-10-03

### Bug Fixes

- Claude responses no longer contain ANSI codes that cause integer conversion crashes

## [0.1.6] - 2025-10-03

### Bug Fixes

- POSIX-compliant string handling replaces bash arrays in install.sh for broader compatibility

## [0.1.5] - 2025-10-03

### Bug Fixes

- Separator placement in compressed commits is now correct

## [0.1.4] - 2025-10-03

### Bug Fixes

- Sonnet compression applies to timer-based and file-switch commits

## [0.1.3] - 2025-10-03

### Bug Fixes

- File paths are preserved when formatting long lines

## [0.1.2] - 2025-10-03

### Bug Fixes

- Installation script compatibility and symlink resolution work reliably

## [0.1.1] - 2025-10-02

### Bug Fixes

- Code block preservation in thinking transformation maintains formatting

## [0.1.0] - 2025-10-02

### Features

- First release of CCThink
