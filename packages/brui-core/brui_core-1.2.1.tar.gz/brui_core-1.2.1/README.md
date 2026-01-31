# BRUI Core (Browser UI Automation Core)

A flexible and robust browser UI automation framework that provides essential functionality for browser-based UI automation projects.

## Features

- **Browser Management**: Automated browser launching and control across different operating systems
- **Configuration Handling**: Flexible configuration management with TOML and environment variable support
- **Clipboard Integration**: Easy clipboard monitoring and manipulation
- **UI Integration Base**: Extensible base classes for UI automation
- **Cross-Platform Support**: Works on Linux and macOS

## Installation

### From PyPI (recommended)

```bash
pip install brui_core
```

### From source (editable)

#### Using `uv` (recommended)

```bash
git clone https://github.com/AutoByteus/brui_core.git
cd brui_core
uv sync
```

### Development / testing extras

With `uv`, dev dependencies are synced by default. To sync all extras:

```bash
uv sync --all-extras
```

### Build the distribution

This project utilizes `uv` for modern, isolated builds:

```bash
# Build with specific Python version
uv build --python 3.11
```

This will produce the source distribution and wheel in the `dist/` directory.

## Quick Start

```python
from brui_core.ui_integrator import UIIntegrator

async def main():
    # Initialize the UI integrator
    ui = UIIntegrator()
    await ui.initialize()

    try:
        # Your automation code here
        pass
    finally:
        # Clean up
        await ui.close()

# Run with asyncio
import asyncio
asyncio.run(main())
```

## Requirements

- Python 3.11+
- Playwright (pinned in `pyproject.toml` and installed automatically)
- Chrome/Chromium browser installed
- Pillow, pyperclip, and other transitive dependencies installed with the package

## Configuration

The framework is configured using environment variables:

| Environment Variable           | Description                                 | Default          |
| ------------------------------ | ------------------------------------------- | ---------------- |
| `CHROME_PROFILE_DIRECTORY`     | Chrome profile to use                       | `Profile 1`      |
| `CHROME_REMOTE_DEBUGGING_PORT` | Remote debugging port                       | `9222`           |
| `CHROME_DOWNLOAD_DIRECTORY`    | Directory for downloads                     | (System Default) |
| `CHROME_USER_DATA_DIR`         | User data directory for session persistence | (System Default) |

### Session Persistence (Logins & Cookies)

To maintain login states (cookies, local storage, cache) across different automation runs, you can configure the `user_data_dir`.

- **Default Behavior:** If `user_data_dir` is not set, Chrome uses your system's default user profile (e.g., `~/.config/google-chrome` on Linux). This means your automation shares the same session as your personal browsing.
- **Custom / Isolated Session:** To keep your automation isolated (or to maintain multiple distinct signed-in states), set `user_data_dir` to a specific path. As long as you point to the same directory, Chrome will restore your previous session, keeping you logged in.
- **Chrome/Chromium 136+ Requirement:** Recent Chrome **and Chromium** versions (136+) refuse to enable remote debugging on the default profile directory. You must set `user_data_dir` to a non-default path for CDP to work.

**Example (Environment Variable):**

```bash
export CHROME_USER_DATA_DIR="./my-bot-profile"
```

## Manual Smoke Tests

This repo includes a few manual smoke tests under `scripts/` to verify local setup.
These are not part of automated CI.

### Browser CDP connectivity

```bash
uv run python scripts/test_browser.py
```

This connects to a running Chromium instance over CDP on `http://localhost:9222` and opens Google.

### UIIntegrator sanity check

```bash
uv run python scripts/test_ui_integrator.py
```

This initializes `UIIntegrator`, opens a page, and optionally writes a screenshot.

### LLM server + Chromium Docker check

```bash
bash scripts/test_llm_server_docker.sh
```

This waits for a local LLM server on port `51739` and Chromium on port `9222`, then probes their HTTP endpoints.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please open an issue in the GitHub repository.

## Acknowledgments

- Built with Playwright
- Developed by AutoByteus
