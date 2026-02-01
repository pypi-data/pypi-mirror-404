# AWSP - AWS Profile Switcher

A command-line utility for easily managing and switching between AWS CLI profiles.

## Features

- **List profiles** - View all configured AWS profiles (IAM and SSO)
- **Switch profiles** - Interactive profile selection with fuzzy search
- **Add profiles** - Create new IAM or SSO profiles interactively
- **Remove profiles** - Safely remove profiles with confirmation
- **Validate credentials** - Test AWS credentials using STS
- **Shell integration** - Seamless profile switching in bash, zsh, and fish

## Installation

```bash
pip install awsp
```

## Quick Start

```bash
# List all profiles
awsp list

# Interactive profile switcher
awsp

# Switch to a specific profile
awsp switch my-profile

# Add a new profile
awsp add

# Show current profile
awsp current

# Validate credentials
awsp validate
```

## Shell Integration

Add to your shell configuration for automatic profile switching:

**Bash** (`~/.bashrc`):
```bash
eval "$(awsp init)"
```

**Zsh** (`~/.zshrc`):
```bash
eval "$(awsp init)"
```

**Fish** (`~/.config/fish/config.fish`):
```fish
awsp init --shell fish | source
```

## Commands

| Command | Description |
|---------|-------------|
| `awsp` | Interactive profile switcher |
| `awsp list` | List all AWS profiles |
| `awsp switch [NAME]` | Switch to a profile |
| `awsp add` | Add a new profile (IAM or SSO) |
| `awsp remove NAME` | Remove a profile |
| `awsp current` | Show current active profile |
| `awsp validate [NAME]` | Validate profile credentials |
| `awsp info [NAME]` | Show detailed profile info |
| `awsp init` | Output shell integration hook |

## Requirements

- Python 3.10+
- AWS CLI (for credential validation and SSO login)

## License

MIT
