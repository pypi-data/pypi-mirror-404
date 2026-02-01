# HeyGen MCP Server

[![VS Code Marketplace Installs](https://img.shields.io/visual-studio-marketplace/i/sbroenne.heygen-mcp?label=VS%20Code%20Installs)](https://marketplace.visualstudio.com/items?itemName=sbroenne.heygen-mcp)
[![PyPI Downloads](https://img.shields.io/pypi/dm/heygen-mcp-sbroenne?label=PyPI%20Downloads)](https://pypi.org/project/heygen-mcp-sbroenne/)
[![GitHub Downloads](https://img.shields.io/github/downloads/sbroenne/heygen-mcp/total?label=GitHub%20Downloads)](https://github.com/sbroenne/heygen-mcp/releases)

[![CI](https://github.com/sbroenne/heygen-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/sbroenne/heygen-mcp/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/sbroenne/heygen-mcp)](https://github.com/sbroenne/heygen-mcp/releases/latest)
[![PyPI Version](https://img.shields.io/pypi/v/heygen-mcp-sbroenne)](https://pypi.org/project/heygen-mcp-sbroenne/)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.10--3.13-blue.svg)](https://www.python.org/downloads/)
[![Built with Copilot](https://img.shields.io/badge/Built%20with-GitHub%20Copilot-0366d6.svg)](https://copilot.github.com/)

![HeyGen Logo](heygen_logo.png)

> ⚠️ **Disclaimer**: This is a community fork of the original HeyGen MCP server, which appears to be abandoned. This is **not** an official HeyGen repository. Use at your own discretion.

**Generate AI Videos with Natural Language** - A Model Context Protocol (MCP) server for HeyGen API integration with AI assistants.

The HeyGen MCP server enables AI assistants (GitHub Copilot, Claude, ChatGPT) to generate AI avatar videos, manage templates, and work with assets through natural language commands.

## 🚀 Quick Start (1 Minute)

**Requirements:** Python 3.10+ | HeyGen API Key ([get one here](https://app.heygen.com/settings?nav=API) - 10 free credits/month)

### ⭐ Recommended: VS Code Extension (One-Click Setup)

**Fastest way to get started - everything configured automatically:**

**[Install from VS Code Marketplace →](https://marketplace.visualstudio.com/items?itemName=sbroenne.heygen-mcp)**

The extension handles server registration and API key configuration automatically!

---

## Installation

### Prerequisites

- Python 3.10 or higher
- A Heygen API key (get one from [Heygen](https://www.heygen.com/)). Includes 10 Free Credits per Month

### Install from PyPI

Install the package directly using pip or uv:

```bash
# Using pip
pip install heygen-mcp-sbroenne

# Using uv (recommended)
uv pip install heygen-mcp-sbroenne

# Or run directly without installing (uvx)
uvx heygen-mcp-sbroenne
```

### Install from GitHub Releases

Download pre-built packages from [GitHub Releases](https://github.com/sbroenne/heygen-mcp/releases):

1. Download the `.whl` or `.tar.gz` file from the latest release
2. Install with pip:
   ```bash
   pip install heygen_mcp_sbroenne-*.whl
   ```

For the VS Code extension, download the `.vsix` file and install via:
- VS Code → Extensions → `...` menu → "Install from VSIX..."

## Usage

### VS Code Extension (Recommended)

The easiest way to use HeyGen MCP with VS Code is through the community VS Code extension:

1. **Install the extension**:
   - [Install from VS Code Marketplace →](https://marketplace.visualstudio.com/items?itemName=sbroenne.heygen-mcp)
   - Or search for "sbroenne.heygen-mcp" in VS Code Extensions (Ctrl+Shift+X)

2. **Configure your API key**:
   - Use Command Palette (Ctrl+Shift+P)
   - Search for "HeyGen: Configure API Key"
   - Enter your API key

3. **Start using it**:
   - The HeyGen MCP server will automatically be available to your AI assistant
   - Ask your AI assistant to generate videos, manage templates, etc.

See [vscode-extension/README.md](vscode-extension/README.md) for more details.

### Quickstart with Claude Desktop

1. Get your API key from [HeyGen](https://www.heygen.com/).
2. Install uv package manager (see [Installing uv](#installing-uv) section above).
3. Go to Claude > Settings > Developer > Edit Config > `claude_desktop_config.json` to include the following:

```json
{
  "inputs": [
    {
      "id": "heygen-api-key",
      "type": "promptString",
      "description": "HeyGen API Key",
      "password": true
    }
  ],
  "mcpServers": {
    "HeyGen": {
      "command": "uvx",
      "args": ["heygen-mcp-sbroenne"],
      "env": {
        "HEYGEN_API_KEY": "${input:heygen-api-key}"
      }
    }
  }
}
```

If you're using Windows, you'll need to enable "Developer Mode" in Claude Desktop to use the MCP server. Click "Help" in the hamburger menu at the top left and select "Enable Developer Mode".

### Using with VS Code (Manual Configuration)

Add the following to your VS Code settings (`.vscode/mcp.json`):

```json
{
  "inputs": [
    {
      "id": "heygen-api-key",
      "type": "promptString",
      "description": "HeyGen API Key",
      "password": true
    }
  ],
  "servers": {
    "HeyGen": {
      "type": "stdio",
      "command": "uvx",
      "args": ["heygen-mcp-sbroenne"],
      "env": {
        "HEYGEN_API_KEY": "${input:heygen-api-key}"
      }
    }
  }
}
```

### Using a Local Development Version

If you want to run from a local clone (for development or testing), use `uv run` instead of `uvx`:

```json
{
  "inputs": [
    {
      "id": "heygen-api-key",
      "type": "promptString",
      "description": "HeyGen API Key",
      "password": true
    },
    {
      "id": "heygen-mcp-path",
      "type": "promptString",
      "description": "Path to local heygen-mcp repository"
    }
  ],
  "mcpServers": {
    "HeyGen": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "--directory",
        "${input:heygen-mcp-path}",
        "python",
        "-m",
        "heygen_mcp.server"
      ],
      "env": {
        "HEYGEN_API_KEY": "${input:heygen-api-key}"
      }
    }
  }
}
```

For VS Code, use `servers` instead of `mcpServers`.

### Available MCP Tools

The server provides 7 resource-based tools, each with multiple actions:

#### `user` - User Account Management

| Action | Description |
|--------|-------------|
| `info` | Get user profile information |
| `credits` | Get remaining credits/quota |

#### `voices` - Voice Management

| Action | Description |
|--------|-------------|
| `list` | Get available voices (max 100, private voices first) |

#### `avatars` - Avatar Management

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | - | Get all avatars and talking photos |
| `get` | `avatar_id` | Get details for a specific avatar |
| `list_groups` | `include_public` (optional) | Get avatar groups |
| `list_in_group` | `group_id` | Get avatars in a specific group |

#### `videos` - Video Generation

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | `token` (optional) | List all videos with pagination |
| `generate` | `video_inputs_json` (JSON array of scenes), `title` (optional) | Create a new avatar video |
| `generate_iv` | `image_key`, `script`, `voice_id`, `video_title`, motion options | Create Avatar IV video from photo |
| `status` | `video_id` | Check video processing status |

**✨ Video Background Support** - Generate videos with color, image, or video backgrounds. See [Video Backgrounds Guide](docs/VIDEO_BACKGROUNDS.md) for details.

#### `templates` - Template Management

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | - | Get all templates in your account |
| `get` | `template_id` | Get template details including variables |
| `generate` | `template_id`, `variables` (optional), `title`, `test`, `caption` | Create video from template |

#### `assets` - Asset Management

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | - | Get all assets (images, videos, audios) |
| `upload` | `file_path` | Upload a media file, returns asset_id |
| `delete` | `asset_id` | Remove an asset |

#### `folders` - Folder Management

| Action | Parameters | Description |
|--------|------------|-------------|
| `list` | - | Get all folders |
| `create` | `name` | Create a new folder |
| `delete` | `folder_id` | Delete a folder |

**Example Usage:**

```
# Get remaining credits
user(action="credits")

# List all avatars
avatars(action="list")

# Get specific avatar details
avatars(action="get", avatar_id="avatar_123")

# Generate a video (single scene)
videos(action="generate", video_inputs_json='[{"character": {"avatar_id": "..."}, "voice": {"voice_id": "...", "input_text": "Hello!"}}]')
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/sbroenne/heygen-mcp.git
cd heygen-mcp

# Install dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Pre-commit Hooks

This project uses pre-commit to run checks before each commit:

- **ruff** - Linting and auto-fixing
- **ruff-format** - Code formatting
- **pyright** - Type checking
- **trailing-whitespace** - Remove trailing whitespace
- **end-of-file-fixer** - Ensure files end with newline
- **check-yaml** - Validate YAML files

Run hooks manually on all files:

```bash
uv run pre-commit run --all-files
```

### Running with MCP Inspector

To run the server locally with the MCP Inspector for testing and debugging:

```bash
uv run mcp dev heygen_mcp/server.py
```

This will start the server in development mode and allow you to use the MCP Inspector to test the available tools and functionality.

### Running Tests

```bash
# Run all tests (requires HEYGEN_API_KEY in .env)
uv run pytest tests/ -v

# Skip video generation tests (uses credits)
uv run pytest tests/ -v -k "not video_generation"
```

### LLM Integration Tests

This project includes LLM-based tests using [agent-benchmark](https://github.com/mykhaliev/agent-benchmark) to validate that AI assistants can correctly understand and use the MCP tools.

```bash
cd tests/heygen_mcp_llm_tests

# List available test scenarios
python run_llm_tests.py --list

# Run safe tests (read-only, no credits consumed)
python run_llm_tests.py

# Run a specific scenario
python run_llm_tests.py -s user-credits-test
```

**Requirements:** Azure OpenAI endpoint (`AZURE_OPENAI_ENDPOINT`) and HeyGen API key (`HEYGEN_API_KEY`).

See [tests/heygen_mcp_llm_tests/README.md](tests/heygen_mcp_llm_tests/README.md) for full documentation.

## Roadmap

- [x] Tests (integration tests + MCP server smoke tests)
- [x] Template API Support
- [x] CI/CD (GitHub Actions + PyPI release)
- [ ] Photo Avatar APIs Support
- [ ] SSE And Remote MCP Server with OAuth Flow
- [ ] Translation API Support
- [ ] Interactive Avatar API Support

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

For maintainers: see the [Publishing Guide](docs/PUBLISHING.md) for release instructions.

## Related Projects

- **[Windows MCP Servers](https://windowsmcpserver.dev/)** - Collection of Windows-focused MCP servers
- **[ExcelMcp](https://github.com/sbroenne/mcp-server-excel)** - MCP Server for Microsoft Excel automation
- **[OBS Studio MCP](https://github.com/sbroenne/mcp-server-obs)** - MCP Server for OBS Studio screen recording
- **[agent-benchmark](https://github.com/mykhaliev/agent-benchmark)** - Framework for testing LLM + MCP integrations

## License

This project is licensed under the MIT License - see the LICENSE file for details.
