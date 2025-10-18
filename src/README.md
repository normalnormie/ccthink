# ccthink Source Code

## Overview

The `src/` directory contains the core implementation of **ccthink** ("ultrathink"), a CLI tool that monitors Claude Code thinking sessions in real-time. It watches JSONL conversation files from Claude projects, extracts thinking content, optionally transforms it using AI-powered phrase compression, and commits it to git with smart accumulation logic.

## Features

- **Real-time JSONL Monitoring**: Watches Claude project conversation files for incoming content
- **Dual Content Type Support**: Extracts and processes both thinking and text content independently
- **Smart Accumulation**: Batches multiple entries before committing to reduce noise
- **AI-Powered Compression**: Optional phrase transformation with multiple Claude models (Sonnet 4.5, Haiku 4.5, Opus) and colored terminal output
- **Git Integration**: Automatic branch management, validation, and commits for each conversation session
- **Persistent State**: Tracks file positions, UUIDs, and configuration across sessions
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Usage

### Basic Monitoring

```bash
# Navigate to your project directory
cd /path/to/your/project

# Start monitoring (display only, no commits)
ccthink

# Enable git commits
ccthink --commit

# Enable Sonnet phrase transformation
ccthink --sonnet

# Enable Haiku phrase transformation (faster, lower cost)
ccthink --haiku

# Enable streaming output with colors
ccthink --sonnet --colors
```

### Configuration

Configuration is stored per-project in `ccthink.conf` and globally in `~/.config/ccthink/config.json`:

```json
{
  "commit_enabled": false,
  "sonnet_enabled": false,
  "sonnet_streaming": false,
  "model": "sonnet",
  "colors": true,
  "thinking_enabled": true,
  "chat_text_enabled": false,
  "poll_interval_seconds": 1.0,
  "line_max_length": 55,
  "separator": "\n\n---\n\n",
  "main_branch": "master"
}
```

Compression configuration:

- `model`: Claude model for phrase compression - "sonnet", "haiku", or "opus" (default: "sonnet")
- `colors`: Enable colored output for all content (default: true)

Content type controls:

- `thinking_enabled`: Extract and process thinking content (default: true)
- `chat_text_enabled`: Extract and process text content (default: false)

### CLI Flags

| Flag             | Effect                              | Persists |
| ---------------- | ----------------------------------- | -------- |
| `--commit`       | Enable git commits                  | Yes      |
| `--no-commit`    | Disable git commits                 | Yes      |
| `--sonnet`       | Enable Sonnet phrase transformation | Yes      |
| `--no-sonnet`    | Disable phrase transformation       | Yes      |
| `--haiku`        | Enable Haiku phrase transformation  | Yes      |
| `--no-haiku`     | Disable phrase transformation       | Yes      |
| `--streaming`    | Enable streaming output             | Yes      |
| `--no-streaming` | Disable streaming output            | Yes      |
| `--colors`       | Enable colored output               | Yes      |
| `--no-colors`    | Disable colored output              | Yes      |

Flags update the persistent configuration, so settings are remembered across sessions.

## Dependencies

Core dependencies managed in `requirements.txt`:

- **claude-agent-sdk** (≥0.0.25): Integration with Claude Code agent for phrase transformation
- **pydantic** (≥2.0.0): Data validation and settings management
- **orjson** (≥3.9.0): Fast JSON parsing for JSONL files
- **pytest** (≥7.0.0): Validation framework

## API Reference

### Main Entry Point

**`main()`** in `main.py`

- Bootstraps the application with CLI arguments
- Initializes configuration from file or defaults
- Starts the async monitoring loop
- Handles graceful shutdown with SIGINT/SIGTERM

### Core Handlers

#### MonitorLoopHandler

**Purpose**: Executes one iteration of the monitoring cycle

**Parameters**:

- `config`: Current configuration state
- `enable_git`: Whether git operations are enabled
- `timer_task`: Optional async timer for accumulation timeout

**Process**:

1. Validate main branch exists in git repository
2. Find current JSONL file in Claude project directory
3. Detect file switches and bring previous branches into main
4. Parse thinking and text entries from file position
5. Compress all entries if Sonnet is enabled (both content types separately)
6. Display content with pre-compressed results
7. Process accumulation logic
8. Commit if threshold reached (strips ANSI codes from commit messages)

#### ProcessThinkingHandler

**Purpose**: Implements content accumulation logic for both thinking and text entries

**Logic**:

- **First content entry**: Start waiting, accumulate
- **Additional content while waiting**: Commit accumulated + first additional entry
- **Timeout reached**: Commit accumulated entries
- **Both content types disabled**: Skip commit and clear accumulation state

**Input**: Accepts pre-compressed content maps to avoid double compression

**Returns**: Decision on whether to commit and what content to commit

#### CommitThinkingHandler

**Purpose**: Creates git commits with thinking content

**Parameters**:

- `message`: Thinking content (may be compressed)
- `simulate`: Dry-run mode for validation

**Process**:

1. Stage all changes with `git add -A`
2. Create commit with thinking as message
3. Handle "nothing to commit" gracefully

### Phrase Transformation

#### TransformThinkingHandler

**Purpose**: Compress thinking phrases using Claude Agent SDK

**Parameters**:

- `thinking_lines`: Lines to transform
- `enable_streaming`: Stream output as it's generated
- `enable_colors`: Apply ANSI 256 color codes

**Output**: Compressed phrases with optional color formatting

#### CompressEntriesHandler

**Purpose**: Compress both thinking and text content from multiple entries

**Parameters**:

- `entries`: List of thinking entries to process
- `config`: Application configuration with content type toggles

**Process**:

1. Loop through all entries
2. Extract thinking content if `thinking_enabled` is true
3. Extract text content if `chat_text_enabled` is true
4. Compress each content type separately using Sonnet transformation
5. Return separate maps for compressed thinking and text content

**Returns**: Compressed content maps keyed by entry parent_uuid

#### ColoredFormatter

**Purpose**: Apply ANSI 256 terminal colors to text

**Methods**:

- `format(text, color)`: Apply color code to text
- `format_with_fallback(text, color, fallback)`: Apply color with fallback on failure

**Features**:

- Terminal capability detection
- Color code validation (0-255)
- Graceful degradation for non-color terminals

## Related Components

### Feature Modules

- **`features/monitoring/`**: JSONL file monitoring, parsing, display, compression, and file switching
- **`features/processing/`**: Content accumulation and commit logic
- **`features/git_operations/`**: Branch management, validation, commits, and accumulated thinking commits
- **`features/gitignore/`**: .gitignore file management with defensive checking
- **`features/phrase_transformation/`**: Claude model compression (Sonnet/Haiku/Opus) and formatting
- **`features/config/`**: Configuration loading and persistence
- **`features/cli/`**: Argument parsing
- **`features/app/`**: Application bootstrapping and graceful exit handling

### Shared Components

- **`shared/models.py`**: Pydantic models for Config, ThinkingEntry, Message structures
- **`shared/constants.py`**: Default paths, timeouts, and configuration values

## Project Structure

```
src/
├── ccthink.py                                  # Entry point script
├── main.py                                     # Main application orchestration
├── shared/                                     # Shared models and constants
│   ├── models.py                               # Pydantic data models
│   └── constants.py                            # Configuration constants
└── features/                                   # Feature-based vertical slices
    ├── app/                                    # Application bootstrapping
    │   ├── graceful_exit/                      # Graceful shutdown with commits
    │   └── get_claude_directory/               # Claude project directory lookup
    ├── cli/                                    # CLI argument parsing
    ├── config/                                 # Configuration management
    ├── git_operations/                         # Git branch and commit operations
    │   ├── commit_accumulated_thinking/        # Commit batched thinking entries
    │   ├── commit_thinking/                    # Individual commit operations
    │   ├── ensure_branch/                      # Branch creation and validation
    │   └── merge_branch/                       # Branch merging
    ├── gitignore/                              # .gitignore management
    ├── monitoring/                             # JSONL monitoring, parsing, display
    │   ├── find_current_jsonl/                 # Current file discovery
    │   ├── parse_thinking/                     # JSONL parsing
    │   ├── display_item/                       # Content display
    │   ├── compress_entries/                   # Batch content compression
    │   ├── process_file_switch/                # File switch handling
    │   └── monitor_loop/                       # Main loop orchestration
    │       ├── display_coordinator.py          # Display coordination helper
    │       ├── commit_helper.py                # Commit management helper
    │       └── commit_formatter.py             # Commit message formatting
    ├── phrase_transformation/                  # Claude model compression
    └── processing/                             # Content accumulation logic
```

Each feature follows a consistent structure:

- `*_command.py`: Input parameters (dataclass)
- `*_handler.py`: Business logic (static class)
- `*_response.py`: Output results (dataclass, optional)

## How It Works

### Monitoring Flow

1. **Validate Branch**: Verify configured main branch exists in git repository
2. **Find Current File**: Locate the most current JSONL file in `~/.claude/projects/{project-name}/`
3. **Read Content**: Read from last known file position to end
4. **Parse Entries**: Extract thinking and text entries from JSONL records (controlled by content type toggles)
5. **Compress Content**: If Sonnet enabled, compress all entries (thinking and text separately)
6. **Display Content**: Show content with pre-compressed results
7. **Accumulate**: Add to waiting list if first entry, or commit if additional entry
8. **Commit**: Create git commit when threshold reached (plain text without ANSI codes)
9. **Update State**: Save file position, UUID, and config

### Git Branch Strategy

- Main branch is validated on startup (warns if configured branch doesn't exist)
- Each JSONL file (conversation) gets its own branch named by file stem
- Branches are created automatically on first thinking entry
- .gitignore is ensured to contain ccthink.conf before any merge or commit
- Defensive check removes ccthink.conf from git index if accidentally staged
- When switching to a different conversation, previous branch is merged into main # noqm
- All commits happen on conversation-specific branches
- Graceful exit handler commits pending thinking and brings branches into main before shutdown

### State Management

Persistent state tracked in configuration:

- `last_processed_uuid`: Last content entry committed
- `last_file_position`: Byte position in JSONL file
- `monitored_file`: Currently watched file path
- `waiting_for_thinking`: Currently accumulating entries
- `accumulated_thinking`: Content entries (thinking or text) waiting to be committed
- `waiting_target_uuid`: Target UUID for next commit

### Phrase Transformation Pipeline

When compression is enabled (Sonnet/Haiku/Opus):

1. **Extract Content**: Parse thinking and text content from JSONL (controlled by content type toggles)
2. **Batch Compress**: Send all entries to CompressEntriesHandler for parallel compression
3. **Transform**: Each content type sent to Claude Agent SDK with compression prompt
4. **Validate Response**: Ensure Agent SDK returns non-empty content (fail fast if empty)
5. **Parse Response**: Extract compressed phrase and color from JSON response
6. **Format**: Apply ANSI color codes if colors enabled
7. **Cache Results**: Store compressed content maps keyed by parent_uuid
8. **Display/Commit**: Show formatted output with pre-compressed content, commit plain text

## Error Handling

- **File Not Found**: Gracefully handles missing JSONL files (waits for next poll)
- **Branch Validation**: Warns if configured main branch doesn't exist, suggests alternatives
- **Merge Conflicts**: Optionally quits on conflict or continues with manual resolution
- **Git Errors**: Logs errors but continues monitoring
- **Transform Failures**: Falls back to original content text
- **Parse Errors**: Skips malformed JSONL entries and continues

## Performance Considerations

- **Polling Interval**: Default 1.0 second (configurable)
- **File Position Tracking**: Only reads incoming content, not entire file
- **Async Architecture**: Non-blocking monitoring loop
- **Streaming Output**: Real-time display as thinking arrives
- **State Caching**: Minimal file I/O with persistent position tracking

## Validation

Run the validation suite:

```bash
# Run all checks
pytest

# Run with coverage
pytest --cov=src

# Run specific module checks
pytest tests/unit/features/processing/
```

Validation follows the feature structure:

```
tests/
├── unit/
│   └── features/
│       ├── monitoring/
│       ├── processing/
│       ├── git_operations/
│       └── phrase_transformation/
└── integration/
    └── end_to_end/
```

## Security Model

- **Local File Access**: Only reads from `~/.claude/projects/` directory
- **Git Operations**: Uses subprocess with explicit command validation
- **Configuration**: Stored in user-local directories (no global state)
- **API Keys**: Managed by Claude Agent SDK (not stored by ccthink)
- **Subprocess Safety**: All git commands validated and sanitized

## Future Improvements

- WebSocket-based monitoring instead of polling
- Configurable accumulation strategies (count-based, time-based, hybrid)
- Multi-project monitoring in single instance
- Export thinking to markdown/HTML
- Integration with other VCS systems (Mercurial, SVN)
- Cloud sync for configuration and state
