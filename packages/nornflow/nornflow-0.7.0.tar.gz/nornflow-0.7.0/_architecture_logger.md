# Updated NornFlow Logging Architecture Document

## 1. Executive Summary

This document outlines the architectural design for a centralized, file-based logging system for NornFlow. The system will capture all application events into timestamped log files, providing a comprehensive audit trail for workflow executions, task runs, and system operations.

## 2. Background and Motivation

### Current State
NornFlow currently lacks a unified logging strategy, with various modules using print statements or ad-hoc logging approaches. This creates several challenges:
- No persistent record of execution history
- Difficulty debugging production issues
- Mixed output between application logs and task results
- No centralized configuration or control

### Design Goals
- **Centralization**: Single logging configuration and management point
- **Isolation**: Logs separated from console output to avoid polluting task results
- **Traceability**: Every log entry timestamped and associated with an execution context
- **Persistence**: File-based storage for post-execution analysis
- **Flexibility**: Support for CLI, programmatic, and future API-based invocations

## 3. Architectural Overview

### 3.1 Core Components

#### Logging Module Structure
```
nornflow/logger.py  # Core logging module
```

The [`logger.py`]expander.py ) module will serve as the single source of truth for all logging operations within NornFlow. It will:
- Configure the root logger for the entire application
- Manage log file creation and rotation
- Provide a singleton logger instance for import by all modules
- Handle execution context tracking

### 3.2 Logger Singleton Pattern

A module-level singleton pattern will ensure all components use the same logger instance:
- Single `Logger` instance created at module import time
- Lazy initialization of file handlers when execution context is established
- Thread-safe operations for concurrent task execution

### 3.3 File Naming Convention

Log files will follow a deterministic naming pattern:
```
{execution_name}_{timestamp}.log
```

Where:
- `execution_name`: Sanitized name derived from:
  - Workflow name (for workflow executions)
  - Task name (for single task runs)
  - Custom identifier (for programmatic usage)
- [`timestamp`]run.py ): Format `YYYYMMDD_HHMMSS` (24-hour format)

### 3.4 Execution Context Management

The logging system will maintain an execution context that tracks:
- Execution start time (used for file naming)
- Execution type (workflow/task/programmatic)
- Execution identifier (name/path)
- Log directory location

## 4. Technical Design

### 4.1 Initialization Flow

1. **Module Import Phase**:
   - Logger module imported by NornFlow components
   - Base logger configured with NullHandler (no output yet)
   - Logger instance made available for import

2. **Execution Start Phase**:
   - Execution context established (CLI/programmatic entry point)
   - Log file path determined based on context
   - File handler attached to logger
   - Initial execution metadata logged

3. **Runtime Phase**:
   - All modules log through the shared logger instance
   - Each log entry automatically timestamped
   - Log level filtering applied based on configuration

4. **Execution End Phase**:
   - Final execution summary logged
   - File handler flushed and closed
   - Context cleared for next execution

### 4.2 Log Format Specification

Each log entry will contain:
```
[TIMESTAMP] [LEVEL] [MODULE] [FUNCTION] - MESSAGE
```

Example:
```
[2024-01-15 14:23:45.123] [INFO] [nornflow.workflow] [run] - Starting workflow execution: deploy_config
[2024-01-15 14:23:45.456] [DEBUG] [nornflow.tasks] [validate] - Validating task parameters for: napalm_get
```

### 4.3 Log Levels and Usage

- **DEBUG**: Detailed diagnostic information (variable values, execution paths)
- **INFO**: General informational messages (task starts/completions, workflow progress)
- **WARNING**: Potentially problematic situations (deprecated features, recoverable errors)
- **ERROR**: Error conditions that don't halt execution (failed hosts, skipped tasks)
- **CRITICAL**: Fatal errors requiring execution termination

### 4.4 Directory Structure

Default log location hierarchy:
```
.nornflow/logs/         # Default location (configurable)
├── deploy_config_20240115_142345.log
├── backup_devices_20240115_150122.log
└── napalm_get_20240116_090015.log
```

### 4.5 Integration Points

The logger will integrate with:
- **CLI Module**: Establish context from command arguments
- **Builder Pattern**: Set context during NornFlow construction
- **Task Execution**: Log task lifecycle events
- **Processor System**: Capture processor operations
- **Variable Manager**: Track variable resolution
- **Error Handlers**: Record exception details

## 5. Configuration Management

### 5.1 Settings Integration

Logger configuration via NornFlowSettings:
- Log directory path (default: [`.nornflow/logs`]__init__.py ))
- Log level (default: INFO)
- Log rotation policy (future enhancement)
- Maximum log file size (future enhancement)

The logger settings will be stored as a dictionary in NornFlowSettings under a key like `logger`. This dictionary will contain minimal required keys:
- `directory`: Path to the log directory (default: logs)
- `level`: Logging level (default: `INFO`)

Additional keys may be added as needed for logger configuration, but the structure will remain minimal.

### 5.2 Environment Variables

The main logger settings dictionary in NornFlowSettings can be influenced through granular environment variables. Since NornFlow environment variables are prefixed with `NORNFLOW_SETTINGS_`, individual keys within the `logger` dictionary can be set using `NORNFLOW_SETTINGS_LOGGER_<nested_key_name>`. For example:
- `NORNFLOW_SETTINGS_LOGGER_directory` sets `logger['directory']`
- `NORNFLOW_SETTINGS_LOGGER_level` sets `logger['level']`

This allows fine-grained control over logger settings without requiring the entire dictionary to be overridden, maintaining configuration integrity while providing flexibility.

### 5.3 Default Configuration

The initial sane default for the logger settings dictionary is:
```python
{
    "directory": ".nornflow/logs",
    "level": "INFO"
}
```

If the specified log directory does not exist, NornFlow will attempt to create it during logger initialization.

## 6. Usage Patterns

### 6.1 Module Integration

Every NornFlow module will follow this pattern:
```python
from nornflow.logger import logger

# Use logger throughout the module
logger.info("Starting operation")
logger.debug(f"Processing with value: {value}")
```

### 6.2 Context Establishment

Entry points will establish execution context:
```python
# CLI entry
initialize_logging(execution_name="workflow.yaml", execution_type="workflow")

# Programmatic entry
initialize_logging(execution_name="api_triggered_job", execution_type="programmatic")
```

Context in this context refers to the execution context, which is a data structure (typically a dictionary or object) that holds metadata about the current execution session. This includes:
- Execution identifier (name/path of workflow or task)
- Execution type (workflow, task, or programmatic)
- Start timestamp
- Log directory path
- Any other session-specific information needed for logging

The context is established at the beginning of an execution (e.g., when running a workflow or task) and is used to:
- Determine the log file name and location
- Configure the logger with appropriate handlers
- Provide consistent metadata across all log entries for that execution
- Ensure thread-safe logging in concurrent scenarios

## 7. Performance Considerations

### 7.1 Buffering Strategy
- Use buffered I/O to minimize disk writes
- Flush on critical events and execution completion
- Configurable buffer size

Python's standard `logging` module does support buffered I/O through the `BufferingHandler` class, which accumulates log records in memory and flushes them in batches. This reduces the number of disk I/O operations, improving performance for high-volume logging scenarios. The logger can be configured to use a `BufferingHandler` with a custom buffer size (e.g., flush every 100 records or when buffer reaches a certain size). No external dependencies are required—it's built into the standard library. Custom code would only be needed to integrate it with the file handler and manage flush triggers (e.g., on execution completion or critical events).

### 7.2 Async Logging (Future)
- Consider async logging for high-throughput scenarios
- Queue-based approach to prevent I/O blocking

Async logging can be implemented now using Python's `logging.handlers.QueueHandler` and `logging.handlers.QueueListener`. The strategy involves:
- A main thread logger that uses a `QueueHandler` to send log records to a queue
- A separate listener thread that processes the queue and writes to files
- This prevents logging from blocking the main execution thread

Since NornFlow's code is currently synchronous, implementing async logging has minimal impact—it simply offloads I/O to a background thread without changing existing synchronous code. No changes to existing synchronous code are needed; the async behavior is handled internally by the logging infrastructure.

## 8. Error Handling

### 8.1 Fallback Mechanisms
- If log directory creation fails: Fall back to temp directory
- If file write fails: Fall back to stderr with warning
- If logger initialization fails: Use Python's default logging

### 8.2 Failure Isolation
- Logging failures must not crash the application
- All logging operations wrapped in try-except blocks
- Critical errors logged to stderr as last resort

## 9. Security Considerations

### 9.1 Sensitive Data
- Implement log sanitization for passwords/secrets
- Use the existing PROTECTED_KEYWORDS list
- Provide masking utilities for custom sensitive data

### 9.2 File Permissions
- Log files created with restrictive permissions (owner-only)
- Directory permissions prevent unauthorized access

## 10. Future Enhancements

### 10.1 Structured Logging
- JSON-formatted logs for machine parsing
- Integration with log aggregation systems
- Searchable log attributes

### 10.2 Remote Logging
- Syslog protocol support
- Cloud logging service integration
- Centralized logging for distributed deployments

### 10.3 Log Analysis Tools
- Built-in log parsing utilities
- Execution timeline visualization
- Performance analysis from logs

## 11. Implementation Roadmap

### Phase 1: Core Logger Module and Constants - DONE ✅
1. Add `NORNFLOW_DEFAULT_LOGGER` constant to constants.py
2. Update `NornFlowSettings` in settings.py to include logger field
3. Create logger.py module with singleton logger, lazy initialization, execution context management, log format, and file handler creation logic

### Phase 2: Settings Integration - DONE ✅
1. Implement environment variable support for logger settings
2. Add configuration validation
3. Create default directory structure

### Phase 3: Module Integration
This phase involves adding meaningful logging throughout the entire NornFlow codebase, covering all ~40+ .py files. The goal is to provide comprehensive audit trails without over-polluting the code or interfering with Nornir's logging. Logging will focus on key events, errors, and debug information using appropriate levels (DEBUG, INFO, WARNING, ERROR, CRITICAL). Print statements will NOT be replaced—only new logging will be added.

#### Substep 1: Core Infrastructure
- Add logging to nornflow.py, builder.py, settings.py, nornir_manager.py, constants.py, exceptions.py, `logger.py`
- Focus: Initialization, errors, key operations

#### Substep 2: Catalogs and Utilities
- Add logging to catalogs.py, utils.py
- Focus: Discovery processes, validation, errors

#### Substep 3: Models
- Add logging to workflow.py, task.py, hookable.py, base.py, blueprint.py, validators.py
- Focus: Validation, creation, execution events

#### Substep 4: Variables System
- Add logging to manager.py, `vars/processor.py`, proxy.py, context.py, exceptions.py, constants.py
- Focus: Variable resolution, context management, errors

#### Substep 5: Jinja2 Service
- Add logging to core.py, exceptions.py, constants.py
- Focus: Template resolution, environment setup, errors

#### Substep 6: Hooks Core
- Add logging to base.py, `hooks/loader.py`, `hooks/mixins.py`, exceptions.py
- Focus: Hook loading, validation, execution

#### Substep 7: Built-in Hooks
- Add logging to if_hook.py, set_to.py, shush.py
- Focus: Condition evaluation, data extraction, suppression logic

#### Substep 8: Built-ins
- Add logging to tasks.py, filters.py, utils.py, default_processor.py, failure_strategy_processor.py, hook_processor.py, custom_filters.py, py_wrapper_filters.py
- Focus: Task execution, filtering, processing, filter registration

#### Substep 9: Blueprints
- Add logging to expander.py, resolver.py
- Focus: Blueprint expansion, resolution, dependency detection

#### Substep 10: CLI
- Add logging to entrypoint.py, run.py, init.py, show.py, exceptions.py, constants.py
- Focus: Command execution, initialization, display operations

### Phase 4: CLI Integration
1. Establish context in CLI entry points
2. Add logging for CLI operations
3. Ensure clean separation from console output
4. Add debug flag support for verbose logging

### Phase 5: Testing and Refinement
1. Add unit tests for logger module
2. Integration tests for end-to-end logging
3. Performance testing and optimization
4. Documentation and usage examples

### Phase 6: Advanced Features (Future)
1. Log rotation implementation
2. Async logging support
3. Structured logging format
4. Analysis tools and utilities

## 12. Success Criteria

- All NornFlow operations produce timestamped log entries
- Log files created with correct naming convention
- No performance degradation from logging
- Clean separation between logs and console output
- Comprehensive execution history available for debugging
- Thread-safe operation in concurrent scenarios

## Answers to Additional Questions

7. **Performance Considerations - Buffered IO**: Yes, we will use buffered I/O. Python's standard `logging` module supports this through the `BufferingHandler`, which accumulates log records in memory and flushes them in batches to reduce disk I/O. This can be configured with a buffer size (e.g., flush every 100 records). No external dependencies are needed—it's built-in. Custom code would handle integration with file handlers and flush triggers (like execution completion).

8. **Async Logging**: Async logging can be implemented now using `logging.handlers.QueueHandler` and `logging.handlers.QueueListener`. The strategy involves a queue where the main logger sends records, and a background listener thread processes them to write to files. This prevents I/O blocking in the main thread. Since NornFlow is synchronous, there's no impact—async logging is handled internally without changing existing code. It improves performance in high-volume scenarios by offloading I/O.

9. **Log Rotation**: Log rotation is the process of managing log file sizes by automatically creating new files when the current one reaches a threshold (e.g., size or time-based). For example, when a log file exceeds 10MB, it's renamed (e.g., `app.log.1`), and a new `app.log` is created. This prevents unbounded file growth and aids in log management. Python's `logging.handlers.RotatingFileHandler` or `TimedRotatingFileHandler` can handle this automatically.

## Answers to Additional Questions

7. **Performance Considerations - Buffered IO**: Yes, we will use buffered I/O. Python's standard `logging` module supports this through the `BufferingHandler`, which accumulates log records in memory and flushes them in batches to reduce disk I/O. This can be configured with a buffer size (e.g., flush every 100 records). No external dependencies are needed—it's built-in. Custom code would handle integration with file handlers and flush triggers (like execution completion).

8. **Async Logging**: Async logging can be implemented now using `logging.handlers.QueueHandler` and `logging.handlers.QueueListener`. The strategy involves a queue where the main logger sends records, and a background listener thread processes them to write to files. This prevents I/O blocking in the main thread. Since NornFlow is synchronous, there's no impact—async logging is handled internally without changing existing code. It improves performance in high-volume scenarios by offloading I/O.

9. **Log Rotation**: Log rotation is the process of managing log file sizes by automatically creating new files when the current one reaches a threshold (e.g., size or time-based). For example, when a log file exceeds 10MB, it's renamed (e.g., `app.log.1`), and a new `app.log` is created. This prevents unbounded file growth and aids in log management. Python's `logging.handlers.RotatingFileHandler` or `TimedRotatingFileHandler` can handle this automatically.



---- 

### Explanation of `logger.exception()`

`logger.exception()` is a method in Python's logging module that logs a message at the ERROR level and automatically includes the traceback (stack trace) of the current exception. It is typically used within an `except` block to capture and log the details of an exception that has just been caught. This is different from `logger.error()`, which only logs the message without the traceback.

Key points:
- It sets the log level to ERROR.
- It appends the full traceback to the log message, making it useful for debugging unhandled or unexpected exceptions.
- It should be called only when an exception is being handled, as it relies on the current exception context (via `sys.exc_info()`).
- Unlike automatic logging in constructors, it provides control over when and where to log exceptions, avoiding duplicate or excessive logging for handled exceptions.

### Files Requiring Changes

Based on the reviewer's feedback, the automatic logging in `NornFlowError.__init__` should be removed to prevent excessive and duplicate logging. Instead, explicit logging should be added in exception handlers throughout the codebase where logging is appropriate (e.g., for unhandled errors or in catch blocks where the exception represents a genuine error).

The primary file to change is exceptions.py (to remove auto-logging). Then, several other files need updates to add explicit logging in places where exceptions are raised or caught. I've identified the following files based on the provided codebase and diffs:

1. **exceptions.py**: Remove auto-logging from `NornFlowError.__init__`.
2. **expander.py**: Add explicit logging in exception handlers.
3. **resolver.py**: Add explicit logging in exception handlers.
4. **utils.py**: Add explicit logging in exception handlers.
5. **nornir_manager.py**: Add explicit logging in exception handlers.
6. **nornflow.py**: Add explicit logging in exception handlers.
7. **settings.py**: Add explicit logging in exception handlers.
8. **workflow.py**: Add explicit logging in exception handlers.
9. **validators.py**: Add explicit logging in exception handlers.
10. **task.py**: Add explicit logging in exception handlers.
11. **hookable.py**: Add explicit logging in exception handlers.
12. **base.py**: Add explicit logging in exception handlers.
13. **loader.py**: Add explicit logging in exception handlers.
14. **exceptions.py**: Add explicit logging in exception handlers.
15. **exceptions.py**: Add explicit logging in exception handlers.
16. **run.py**: Add explicit logging in exception handlers.
17. **init.py**: Add explicit logging in exception handlers.
18. **show.py**: Add explicit logging in exception handlers.
19. **utils.py**: Add explicit logging in exception handlers.
20. **tasks.py**: Add explicit logging in exception handlers.
21. **hook_processor.py**: Add explicit logging in exception handlers.
22. **failure_strategy_processor.py**: Add explicit logging in exception handlers.
23. **default_processor.py**: Add explicit logging in exception handlers.
24. **decorators.py**: Add explicit logging in exception handlers.
25. **custom_filters.py**: Add explicit logging in exception handlers.
26. **if_hook.py**: Add explicit logging in exception handlers.
27. **set_to.py**: Add explicit logging in exception handlers.
28. **shush.py**: Add explicit logging in exception handlers.

For each file, I've provided the full updated code below. Changes include:
- Removing the `logger.error(message)` line from `NornFlowError.__init__`.
- Adding `logger.exception()` or `logger.error()` in relevant exception handlers (e.g., in `try`-`except` blocks or when raising exceptions), but only where it represents an actual error (not for validation or expected exceptions that are handled gracefully).


----

Looking at the diffs and the documentation files, here are the changes needed to document the new logging functionality:

## 1. nornflow_settings.md - Add new `logger` setting

Add a new section for the `logger` setting in the Optional Settings section, after `dry_run`:

```markdown
### `logger`

- **Description**: Configuration for NornFlow's logging system. Controls where log files are written and the logging verbosity level.
- **Type**: `dict` with keys `directory` and `level`
- **Default**: `{"directory": ".nornflow/logs", "level": "INFO"}`
- **Example**:
  ```yaml
  logger:
    directory: ".nornflow/logs"
    level: "DEBUG"
  ```
- **Sub-keys**:
  - `directory`: Path to the directory where log files will be written. Relative paths resolve against the project root. Created automatically if it doesn't exist.
  - `level`: Logging verbosity level. Valid values: `"DEBUG"`, `"INFO"`, `"WARNING"`, `"ERROR"`, `"CRITICAL"`
- **Note**: Log files are automatically created with timestamped filenames (e.g., `my_workflow_20240115_143022.log`). Each workflow execution creates a new log file.
```

## 2. quick_start.md - Mention logs in project structure

Update the project structure created by `nornflow init` to show the default logs location:

```markdown
This creates:
- 📁 tasks - Where your Nornir tasks should live
- 📁 workflows - Holds YAML workflow definitions
- 📁 filters - Custom Nornir inventory filters
- 📁 hooks - Custom hook implementations for extending task behavior
- 📁 blueprints - Reusable task collections
- 📁 j2_filters - Custom Jinja2 filters for templates
- 📁 vars - Will contain Global and Domain-specific default variables
- 📁 nornir_configs - Nornir configuration
- 📁 .nornflow/logs - Execution log files (created automatically)
- 📑 nornflow.yaml - NornFlow settings
```

## 3. core_concepts.md - Add logging section

Add a new section about logging, perhaps after "Failure Strategies (Summary)":

```markdown
## Logging

NornFlow provides centralized logging that captures detailed execution information for debugging and auditing purposes.

### Log Files

- **Location**: Configured via `logger.directory` setting (default: `.nornflow/logs`)
- **Naming**: Files are timestamped with the workflow/task name (e.g., `my_workflow_20240115_143022.log`)
- **Format**: Each log entry includes timestamp, log level, logger name, and message

### Log Levels

Configure verbosity via `logger.level` in `nornflow.yaml`:

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed diagnostic information including variable resolution, template compilation |
| `INFO` | General execution flow, task start/completion, workflow progress |
| `WARNING` | Potential issues that don't stop execution |
| `ERROR` | Errors that may affect results (also printed to console) |
| `CRITICAL` | Severe errors that may halt execution |

### Configuration

```yaml
# nornflow.yaml
logger:
  directory: ".nornflow/logs"
  level: "INFO"
```

### Sensitive Data Protection

NornFlow automatically redacts sensitive data in log messages. Values associated with keys like `password`, `secret`, `token`, `api_key`, and similar are replaced with `***REDACTED***`.

### Console Output

Errors (`ERROR` level and above) are always printed to stderr regardless of the log level setting, ensuring critical issues are immediately visible.
```

## 4. nornflow_settings.md - Update sample nornflow.yaml

The sample configuration shown in the documentation should include the logger section to match the updated `cli/samples/nornflow.yaml`:

```yaml
nornir_config_file: "nornir_configs/config.yaml"
local_tasks:
  - "tasks"
local_workflows:
  - "workflows"
local_filters:
  - "filters"
local_hooks:
  - "hooks"
local_blueprints:
  - "blueprints"
local_j2_filters:
  - "j2_filters"
imported_packages: []
dry_run: false
failure_strategy: "skip-failed"
processors:
  - class: "nornflow.builtins.DefaultNornFlowProcessor"
vars_dir: "vars"

logger:
  directory: ".nornflow/logs"
  level: "INFO"
```

## 5. api_reference.md - Document NornFlowLogger

Add a section for the logging module:

```markdown
## Logging

### NornFlowLogger Class

Singleton logger class providing centralized logging for NornFlow.

```python
from nornflow.logger import logger

logger.info("This is an info message")
logger.debug("Debug details")
logger.error("An error occurred")
```

### Methods

| Method | Description |
|--------|-------------|
| `debug(message, *args, **kwargs)` | Log debug message |
| `info(message, *args, **kwargs)` | Log info message |
| `warning(message, *args, **kwargs)` | Log warning message |
| `error(message, *args, **kwargs)` | Log error message |
| `critical(message, *args, **kwargs)` | Log critical message |
| `exception(message, *args, **kwargs)` | Log exception with traceback |
| `set_execution_context(...)` | Configure logging for a workflow execution |
| `clear_execution_context()` | Stop file logging and clear context |
| `get_execution_context()` | Get current execution context |

### Execution Context

The logger automatically creates timestamped log files when a workflow starts:

```python
logger.set_execution_context(
    execution_name="my_workflow",
    execution_type="workflow",
    log_dir=".nornflow/logs",
    log_level="INFO"
)
```

### Sensitive Data Sanitization

Log messages are automatically sanitized to redact sensitive values:

```python
from nornflow.logger import sanitize_log_message

# Values after keywords like 'password', 'secret', 'token' are redacted
sanitize_log_message("password=secret123")  # "password=***REDACTED***"
```
```

## 6. `hooks_guide.md` - Update shush hook note

The `shush` hook section mentions `print()` but now uses `logger.warning()`. Update the explanation:

```markdown
**Warning on incompatibility**: Shows a warning in the logs if no compatible processor is found.
```

## Summary of Required Documentation Changes

| File | Change Type | Description |
|------|-------------|-------------|
| nornflow_settings.md | **Add** | New `logger` setting documentation |
| nornflow_settings.md | **Update** | Sample nornflow.yaml with logger section |
| quick_start.md | **Update** | Project structure to mention logs directory |
| core_concepts.md | **Add** | New "Logging" section |
| api_reference.md | **Add** | NornFlowLogger class documentation |
| hooks_guide.md | **Update** | Minor wording update for shush hook warning |