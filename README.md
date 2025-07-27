# Portfolio Agent 🤖

> AI-powered portfolio and resume manager that runs completely offline on your MacBook Air M2

## ✨ What it does

**Portfolio Agent** automatically analyzes your coding projects and updates your GitHub Pages portfolio and resume with compelling, ATS-optimized content. Everything runs locally using Ollama and Llama 3.1 - no cloud APIs needed!

### Key Features
- 🔍 **Smart Project Analysis** - Reads your code and documentation to understand what your project does
- 📝 **Auto-Generated Content** - Creates portfolio entries and resume bullet points
- 🎯 **ATS-Optimized** - Resume bullets designed to pass applicant tracking systems
- 🚀 **Full Git Workflow** - Commits, pushes, and deploys automatically
- 💾 **Backup System** - Creates restore points before making changes
- 🔒 **100% Private** - All processing happens on your machine

## 🚀 One-Command Setup

```bash
# Download and run the complete setup
curl -fsSL https://raw.githubusercontent.com/yourusername/portfolio-agent/main/setup.sh | bash
```

That's it! The script will:
- Install Ollama and download the AI model
- Set up Python environment with all dependencies  
- Create global `portfolio-agent` command
- Configure everything for your MacBook Air M2

## 📋 Quick Usage

```bash
# Analyze and add a project to your portfolio
portfolio-agent /path/to/your/project

# Different modes
portfolio-agent ~/my-react-app --mode auto        # Fully automated
portfolio-agent ./python-api --mode dry-run      # Preview changes  
portfolio-agent /code/project --mode analyze-only # Just analyze
```

## 🎯 Workflow

1. **Project Analysis** 📊
   - Scans your project files (README, code, package.json, etc.)
   - Uses local AI to understand what your project does
   - Identifies technologies and key features

2. **Portfolio Update** 🎨
   - Adds project to your `Portfolio.tsx` (newest first)
   - Includes technologies, description, and highlights

3. **Resume Update** 📄
   - Shows current 3 resume projects
   - Asks which to replace (if needed)
   - Generates ATS-optimized bullet points
   - Creates PDF and ensures single-page format

4. **Deploy** 🚀
   - Creates backup branch
   - Commits all changes
   - Pushes to GitHub
   - Deploys via `npm run deploy`

## 📁 Portfolio Structure Required

Your portfolio should have this structure:
```
aniruddha-portfolio/
├── src/Portfolio.tsx        # Contains: const projects = [...]
├── public/resume.html       # Has projects section
├── package.json            # Has generate-pdf script
└── scripts/generate-pdf.js  # PDF generation
```

## 🛠️ Advanced Usage

### Configuration
```bash
# View current config
cat ~/.portfolio_agent/config.json

# Reconfigure (delete config to trigger setup)
rm ~/.portfolio_agent/config.json
portfolio-agent /any/project
```

### MCP Server Integration

The portfolio agent can be used as a Model Context Protocol (MCP) server for integration with AI assistants:

```bash
# Start MCP server
./portfolio-mcp

# Test mode (list available tools)
./portfolio-mcp --test

# With custom log level
./portfolio-mcp --log-level DEBUG
```

Available MCP tools:
- `analyze_project`: Analyze a software project and extract key information
- `update_portfolio`: Add project to portfolio with specified mode
- `get_project_info`: Get detailed project information and file structure
- `deploy_portfolio`: Deploy portfolio changes to GitHub Pages
- `list_projects`: List all projects in the portfolio

#### MCP Client Example

```python
# Example usage of the MCP client
from mcp_client_example import MCPClient
import asyncio

async def main():
    client = MCPClient()
    await client.start_server()
    
    # List available tools
    tools = await client.list_tools()
    print(f"Available tools: {len(tools)}")
    
    # Analyze a project
    analysis = await client.analyze_project("/path/to/project")
    print(f"Project: {analysis['project_name']}")
    print(f"Technologies: {analysis['technologies']}")
    
    await client.stop_server()

asyncio.run(main())
```

#### JSON-RPC Interface

The MCP server communicates via JSON-RPC over stdin/stdout:

```json
// List tools
{"jsonrpc": "2.0", "id": 1, "method": "tools/list"}

// Analyze project
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "tools/call",
  "params": {
    "name": "analyze_project",
    "arguments": {"project_path": "/path/to/project"}
  }
}
```

### Troubleshooting
```bash
# View logs
tail -f ~/.portfolio_agent/logs/agent_$(date +%Y%m%d).log

# Test AI model
ollama list
ollama run llama3.1:8b "Hello"

# Restart Ollama
brew services restart ollama
```

### Rollback Changes
```bash
cd ~/aniruddha-portfolio
git branch  # See backup branches
git checkout backup-20241127-143022
git checkout main  
git reset --hard backup-20241127-143022
```

## 🎨 Example Output

**For a React project:**
```
✅ Project analyzed: my-react-dashboard
📝 Description: Interactive data visualization dashboard with real-time updates
🔧 Technologies: React, TypeScript, D3.js, Node.js

📋 Key highlights:
  1. Built responsive dashboard with 8+ interactive charts and graphs
  2. Implemented real-time data streaming using WebSocket connections  
  3. Created reusable component library with TypeScript definitions
  4. Optimized rendering performance for datasets with 10,000+ records
```

**Generated Resume Bullets:**
- Built interactive React dashboard with 8+ data visualization components serving 200+ users
- Implemented real-time WebSocket integration reducing data latency by 60%  
- Developed TypeScript component library with comprehensive testing coverage

## 🔒 Privacy & Security

- ✅ **100% Offline** - No data sent to external APIs
- ✅ **Local AI** - Llama 3.1 runs entirely on your Mac
- ✅ **Automatic Backups** - Git branches created before changes
- ✅ **No Telemetry** - Zero usage tracking
- ✅ **Open Source** - All code is transparent

## 📚 Requirements

- **macOS** (optimized for M1/M2)
- **Python 3.8+**
- **Node.js 16+** 
- **Git**
- **8GB+ RAM** (for AI model)
- **Existing GitHub Pages portfolio** with the required structure

## 🗑️ Uninstall

```bash
~/portfolio-agent/uninstall.sh
```

Removes all components, configs, and optionally the project directory.

## 🤝 Contributing

This is designed as a personal tool, but feel free to fork and adapt for your needs!

## 📄 License

MIT - Use freely for personal and commercial projects.

---

**Ready to supercharge your portfolio? Get started with one command! 🚀**