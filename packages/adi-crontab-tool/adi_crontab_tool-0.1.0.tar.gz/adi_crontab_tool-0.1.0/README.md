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

Provide a cron expression as a quoted string argument:

```bash
crontab-tool "*/5 * * * *"
```

**Output Example:**

```text
At every 5th minute.
Next run: 2023-10-27 10:05:00
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