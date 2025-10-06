# ccthink Source Code

## Overview

The `src/` directory contains the core implementation of **ccthink** ("ultrathink"), a CLI tool that monitors Claude Code thinking sessions in real-time. It watches JSONL conversation files from Claude projects, extracts thinking content, optionally transforms it using AI-powered phrase compression, and commits it to git with smart accumulation logic.

## Features

- **Real-time JSONL Monitoring**: Watches Claude project conversation files for incoming thinking content
- **Smart Accumulation**: Batches multiple thinking entries before committing to reduce noise
- **AI-Powered Compression**: Optional Sonnet-based phrase transformation with colored terminal output
- **Git Integration**: Automatic branch management and commits for each conversation session
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
  "sonnet_colors": false,
  "poll_interval_seconds": 1.0,
  "line_max_length": 55,
  "separator": "\n\n---\n\n",
  "main_branch": "master"
}
```

### CLI Flags

| Flag             | Effect                        | Persists |
| ---------------- | ----------------------------- | -------- |
| `--commit`       | Enable git commits            | Yes      |
| `--no-commit`    | Disable git commits           | Yes      |
| `--sonnet`       | Enable phrase transformation  | Yes      |
| `--no-sonnet`    | Disable phrase transformation | Yes      |
| `--streaming`    | Enable streaming output       | Yes      |
| `--no-streaming` | Disable streaming output      | Yes      |
| `--colors`       | Enable colored output         | Yes      |
| `--no-colors`    | Disable colored output        | Yes      |

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

1. Find current JSONL file in Claude project directory
2. Detect file switches and bring previous branches into main
3. Parse thinking entries from file position
4. Display thinking (with optional compression)
5. Process accumulation logic
6. Commit if threshold reached

#### ProcessThinkingHandler

**Purpose**: Implements thinking accumulation logic

**Logic**:

- **First thinking**: Start waiting, accumulate
- **Additional thinking while waiting**: Commit accumulated + first additional entry
- **Timeout reached**: Commit accumulated entries

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

- **`features/monitoring/`**: JSONL file monitoring and parsing
- **`features/processing/`**: Thinking accumulation and commit logic
- **`features/git_operations/`**: Branch management and commits
- **`features/phrase_transformation/`**: Sonnet compression and formatting
- **`features/config/`**: Configuration loading and persistence
- **`features/cli/`**: Argument parsing
- **`features/app/`**: Application bootstrapping

### Shared Components

- **`shared/models.py`**: Pydantic models for Config, ThinkingEntry, Message structures
- **`shared/constants.py`**: Default paths, timeouts, and configuration values

## Project Structure

```
src/
├── ccthink.py                    # Entry point script
├── main.py                       # Main application orchestration
├── shared/                       # Shared models and constants
│   ├── models.py                 # Pydantic data models
│   └── constants.py              # Configuration constants
└── features/                     # Feature-based vertical slices
    ├── app/                      # Application bootstrapping
    ├── cli/                      # CLI argument parsing
    ├── config/                   # Configuration management
    ├── git_operations/           # Git branch and commit operations
    ├── gitignore/               # .gitignore management
    ├── monitoring/              # JSONL monitoring and parsing
    ├── phrase_transformation/   # Sonnet compression
    └── processing/              # Thinking accumulation logic
```

Each feature follows a consistent structure:

- `*_command.py`: Input parameters (dataclass)
- `*_handler.py`: Business logic (static class)
- `*_response.py`: Output results (dataclass, optional)

## How It Works

### Monitoring Flow

1. **Find Current File**: Locate the most current JSONL file in `~/.claude/projects/{project-name}/`
2. **Read Content**: Read from last known file position to end
3. **Parse Entries**: Extract thinking entries from JSONL records
4. **Display Thinking**: Show thinking content (optionally compressed)
5. **Accumulate**: Add to waiting list if first entry, or commit if additional entry
6. **Commit**: Create git commit when threshold reached
7. **Update State**: Save file position, UUID, and config

### Git Branch Strategy

- Each JSONL file (conversation) gets its own branch named by file stem
- Branches are created automatically on first thinking entry
- When switching to a different conversation, previous branch is merged into main # noqm
- All commits happen on conversation-specific branches

### State Management

Persistent state tracked in configuration:

- `last_processed_uuid`: Last thinking entry committed
- `last_file_position`: Byte position in JSONL file
- `monitored_file`: Currently watched file path
- `waiting_for_thinking`: Currently accumulating entries
- `accumulated_thinking`: Entries waiting to be committed
- `waiting_target_uuid`: Target UUID for next commit

### Phrase Transformation Pipeline

When Sonnet is enabled:

1. **Extract Thinking**: Parse thinking content from JSONL
2. **Transform**: Send to Claude Agent SDK with compression prompt
3. **Parse Response**: Extract compressed phrase and color from JSON response
4. **Format**: Apply ANSI color codes if colors enabled
5. **Display/Commit**: Show formatted output or commit plain text

## Error Handling

- **File Not Found**: Gracefully handles missing JSONL files (waits for next poll)
- **Merge Conflicts**: Optionally quits on conflict or continues with manual resolution
- **Git Errors**: Logs errors but continues monitoring
- **Transform Failures**: Falls back to original thinking text
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
