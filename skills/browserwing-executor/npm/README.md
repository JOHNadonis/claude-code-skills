# BrowserWing

Native Browser Automation Platform with AI Integration

## Installation

```bash
# Using npm
npm install -g browserwing

# Using pnpm
pnpm add -g browserwing

# Using yarn
yarn global add browserwing
```

### macOS Users - Important

If you encounter an error when running BrowserWing on macOS (app gets killed immediately), run this command:

```bash
xattr -d com.apple.quarantine $(which browserwing)
```

This removes the quarantine attribute that macOS applies to downloaded executables. [Learn more](https://github.com/browserwing/browserwing/blob/main/docs/MACOS_INSTALLATION_FIX.md)

## Quick Start

```bash
# Start BrowserWing server
browserwing --port 8080

# Open in browser
# http://localhost:8080
```

## Features

- **Complete Browser Control**: 26+ HTTP API endpoints for full-featured browser automation
- **Built-in AI Agent**: Direct conversational interface for browser automation tasks
- **Universal AI Tool Integration**: Native MCP & Skills protocol support
- **Visual Script Recording**: Record, edit, and replay browser actions
- **Flexible Export Options**: Convert scripts to MCP commands or Skills files
- **Intelligent Data Extraction**: LLM-powered semantic extraction
- **Session Management**: Robust cookie and storage handling

## Documentation

- Website: https://browserwing.com
- GitHub: https://github.com/browserwing/browserwing
- Issues: https://github.com/browserwing/browserwing/issues

## License

MIT
