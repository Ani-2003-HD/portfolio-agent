#!/bin/bash
echo "🗑️  Uninstalling Portfolio Agent..."

# Stop Ollama
brew services stop ollama 2>/dev/null || true

# Remove global command
sudo rm -f /usr/local/bin/portfolio-agent 2>/dev/null || true

# Remove config
rm -rf ~/.portfolio_agent

# Remove project directory option
read -p "Remove project directory ($HOME/portfolio-agent)? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf "$HOME/portfolio-agent"
    echo "✅ Project directory removed"
fi

echo "✅ Portfolio Agent uninstalled"
