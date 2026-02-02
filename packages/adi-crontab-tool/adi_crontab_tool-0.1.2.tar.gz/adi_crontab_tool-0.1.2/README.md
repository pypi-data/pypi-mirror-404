# adi-crontab-tool

A small CLI to validate and explain cron expressions.

## Installation

### From PyPI (Recommended)

```bash
pip install adi-crontab-tool
```

### From Source

Navigate to the tool's directory and install it:

```bash
cd crontab
pip install .
```

### For Development

To install in editable mode with development dependencies (like `pytest`):

```bash
pip install -e .[dev]
```

## Usage

Once installed, you can use the `crontab-tool` command.

### Validate and Explain a Cron Expression

Use the `explain` subcommand to get a description of the schedule:

```bash
crontab-tool explain "*/5 * * * *"
```

### Just Validate

Use the `validate` subcommand to check if an expression is valid (returns exit code 0 if valid, 2 if invalid):

```bash
crontab-tool validate "0 9 * * *"
```

**Output Example:**

```text
Every 5 minutes.
```

### Help

To see available options:

```bash
crontab-tool --help
```

## Testing

To run the tests, make sure you installed the package with `[dev]` dependencies:

```bash
pytest
```