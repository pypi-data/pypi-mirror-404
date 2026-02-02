# Installation

This guide covers installing Prisme on different platforms.

## Requirements

- **Python**: 3.13 or higher
- **Node.js**: 22 or higher (for frontend development)
- **Database**: PostgreSQL (recommended) or SQLite

## Install Prisme

### Using uv (Recommended)

[uv](https://docs.astral.sh/uv/) is a fast Python package manager that we recommend for Prisme projects.

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install prisme
uv add prisme
```

### Using pip

```bash
pip install prisme
```

### Verify Installation

```bash
prism --version
```

You should see the installed version number.

## Platform-Specific Instructions

### macOS

```bash
# Install Homebrew if needed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install Python 3.13
brew install python@3.13

# Install Node.js 22
brew install node@22

# Install PostgreSQL (optional, SQLite works for development)
brew install postgresql@16

# Install uv
brew install uv

# Install Prisme
uv add prisme
```

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python 3.13 (may need deadsnakes PPA)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt install python3.13 python3.13-venv

# Install Node.js 22
curl -fsSL https://deb.nodesource.com/setup_22.x | sudo -E bash -
sudo apt install nodejs

# Install PostgreSQL (optional)
sudo apt install postgresql postgresql-contrib

# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Prisme
uv add prisme
```

### Windows

```powershell
# Install Python 3.13 from python.org or Microsoft Store

# Install Node.js 22 from nodejs.org

# Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install Prisme
uv add prisme
```

### Windows with WSL2 (Recommended)

For the best development experience on Windows, we recommend using WSL2:

```bash
# Enable WSL2 (run in PowerShell as Administrator)
wsl --install

# After restart, open Ubuntu terminal and follow Linux instructions above
```

## Docker Installation (Alternative)

If you prefer containerized development:

```bash
# Install Docker Desktop
# https://docs.docker.com/desktop/

# Create project with Docker support
prism create my-project --docker

# Start development environment
cd my-project
prism dev --docker
```

See [Docker Development](../user-guide/docker-development.md) for more details.

## Development Dependencies

For contributing to Prisme itself:

```bash
# Clone the repository
git clone https://github.com/Lasse-numerous/prisme.git
cd prisme

# Install all dependencies including dev tools
uv sync --all-extras

# Verify setup
uv run pytest
uv run ruff check .
uv run mypy src
```

## Troubleshooting

### Python Version Issues

If `python3.13` is not found:

```bash
# Check available Python versions
ls /usr/bin/python*

# Create alias if needed
alias python3.13=/usr/bin/python3.13

# Or use pyenv for version management
curl https://pyenv.run | bash
pyenv install 3.13
pyenv global 3.13
```

### Permission Errors

If you get permission errors installing packages:

```bash
# Don't use sudo with pip/uv!
# Instead, use virtual environments

# Create a virtual environment
python3.13 -m venv .venv

# Activate it
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Then install
uv add prisme
```

### uv Not Found After Installation

```bash
# Add uv to your PATH
export PATH="$HOME/.cargo/bin:$PATH"

# Add to your shell profile (~/.bashrc, ~/.zshrc)
echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

## Next Steps

Now that Prisme is installed, continue to the [Quick Start](quickstart.md) to create your first project.
