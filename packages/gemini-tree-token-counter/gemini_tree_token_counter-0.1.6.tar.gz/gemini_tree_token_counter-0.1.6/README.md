# Gemini Tree Token Counter (gtc)

[🇯🇵 日本語 (Japanese)](./README_ja.md)

A CLI tool to estimate tokens for Gemini models across local directories and GitHub repositories.
It visualizes the file tree with token counts and supports "Time Travel" (analyzing specific Git commits/dates).

> **Note:** The token counting logic is based on regex approximations (ported from `smartprocure/gemini-token-estimator`) and is designed for speed. It is accurate within ~10% for most cases.

## Features

- 🚀 **Fast Estimation**: Uses regex-based logic (no API calls required).
- 🌳 **Tree Visualization**: Displays directory structure with token counts per node.
- 🐙 **GitHub Support**: Analyze remote repositories directly.
- ⏳ **Time Travel**: Check token counts for a specific branch, commit hash, or date (e.g., "how many tokens was this repo in 2023?").
- 📄 **Content Inspection**: Optionally output file contents for context generation.
- 🧹 **Exclude Patterns**: Ignore files via `.gtcignore` or `--exclude`.

## Installation

### Prerequisites
- Python 3.7+
- **Git** (The `git` command must be available in your system path)

### Install via pip

```bash
pip install gemini-tree-token-counter
```

## Usage

Basic usage scans the current directory:

```bash
gtc
```

### Options

- `target`: Local path or GitHub URL (default: current directory).
- `-d`, `--dir`: Target specific subdirectories (can be used multiple times).
- `-c`, `--content`: Display file contents (useful for piping to LLMs).
- `-e`, `--exclude`: Exclude patterns (glob). Can be used multiple times.
- `-b`, `--branch`: Checkout a specific Git branch.
- `--commit`: Checkout a specific Git commit hash.
- `--date`: Checkout the latest commit before a specific date (format: YYYY-MM-DD).
- `--first`: Checkout the first (initial) commit of the repo.

### Exclude Patterns

You can exclude files/folders that are tracked by Git but unnecessary for token counting.

1. **CLI (`--exclude`)**
   ```bash
   gtc . --exclude "*.test.ts" --exclude "__snapshots__" --exclude "telemetry"
   ```

2. **`.gtcignore` (project root)**
   ```gitignore
   # Tests and snapshots
   *.test.ts
   __snapshots__/
   __mocks__/

   # Heavy directories
   telemetry/
   packages/core/src/mcp/
   ```

### Examples

```bash
# 1. Local Directory
gtc                       # Scan current directory
gtc . -d src -d lib       # Scan specific dirs
gtc . -c > context.txt    # Dump all code and tokens to a file
gtc . -e "*.test.ts" -e "__snapshots__"  # Exclude patterns

# 2. GitHub Repository
gtc https://github.com/user/repo
gtc https://github.com/user/repo -b develop

# 3. Time Travel (Git History)
gtc . --date 2023-01-01   # How big was this project last year?
gtc . --first             # How small was the first commit?
```

## Output Example (ver 0.1.2)

```text
$ gtc

Source       : .
Working Path : /Users/sakasegawa/src/github.com/nyosegawa/gemini-tree-token-counter
------------------------------------------------------------
├── src/ (4679 tokens)
│   └── gemini_tree_token_counter/ (4679 tokens)
│       ├── __init__.py (11 tokens)
│       └── main.py (4668 tokens)
├── tests/ (2596 tokens)
│   ├── __init__.py (0 tokens)
│   └── test_tokenizer.py (2596 tokens)
├── .gitignore (682 tokens)
├── LICENSE (0 tokens)
├── pyproject.toml (249 tokens)
├── README.md (1130 tokens)
└── README_ja.md (594 tokens)
------------------------------------------------------------
Grand Total Tokens: 9930
------------------------------------------------------------
```

## License & Acknowledgments

This project is licensed under the **MIT License**.

However, the tokenizer regex logic is a port of [gemini-token-estimator](https://github.com/smartprocure/gemini-token-estimator) by **GovSpend**, which is licensed under the **ISC License**.

### Tokenizer Logic Copyright
Copyright (c) GovSpend

Permission to use, copy, modify, and/or distribute this software for any purpose with or without fee is hereby granted, provided that the above copyright notice and this permission notice appear in all copies.
