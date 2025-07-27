#!/usr/bin/env python3
"""
MCP Server Interface - Custom Model Context Protocol server for Portfolio Agent
Works with Python 3.9+ without requiring the official MCP package
"""

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
import argparse
import subprocess

from portfolio_agent import PortfolioAgent
from file_handlers import FileAnalyzer

class CustomMCPServer:
    """Custom MCP Server for Portfolio Agent functionality"""
    
    def __init__(self):
        self.agent = None
        self.file_analyzer = FileAnalyzer()
        self.logger = self.setup_logging()
        self.tools = self._define_tools()
    
    def setup_logging(self):
        """Setup logging for MCP server"""
        log_dir = Path.home() / ".portfolio_agent" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / "mcp_server.log"),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger(__name__)
    
    def _define_tools(self):
        """Define available tools"""
        return {
            "analyze_project": {
                "description": "Analyze a software project and extract key information",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project directory"
                        }
                    },
                    "required": ["project_path"]
                }
            },
            "update_portfolio": {
                "description": "Add a project to the portfolio",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project directory"
                        },
                        "mode": {
                            "type": "string",
                            "enum": ["interactive", "auto", "dry-run"],
                            "description": "Execution mode",
                            "default": "auto"
                        }
                    },
                    "required": ["project_path"]
                }
            },
            "get_project_info": {
                "description": "Get detailed information about a project",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "project_path": {
                            "type": "string",
                            "description": "Path to the project directory"
                        }
                    },
                    "required": ["project_path"]
                }
            },
            "deploy_portfolio": {
                "description": "Deploy portfolio changes to GitHub Pages",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "commit_message": {
                            "type": "string",
                            "description": "Git commit message",
                            "default": "Update portfolio"
                        }
                    }
                }
            },
            "list_projects": {
                "description": "List all projects in the portfolio",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        }
    
    async def list_tools(self) -> Dict[str, Any]:
        """List available tools"""
        return {
            "tools": [
                {
                    "name": name,
                    "description": tool["description"],
                    "inputSchema": tool["parameters"]
                }
                for name, tool in self.tools.items()
            ]
        }
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tool calls"""
        try:
            if tool_name == "analyze_project":
                return await self._analyze_project(arguments)
            elif tool_name == "update_portfolio":
                return await self._update_portfolio(arguments)
            elif tool_name == "get_project_info":
                return await self._get_project_info(arguments)
            elif tool_name == "deploy_portfolio":
                return await self._deploy_portfolio(arguments)
            elif tool_name == "list_projects":
                return await self._list_projects(arguments)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
        except Exception as e:
            self.logger.error(f"Tool call failed: {e}")
            return {
                "content": [{"type": "text", "text": f"Error: {str(e)}"}],
                "isError": True
            }
    
    async def _analyze_project(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze a project using file handlers"""
        project_path = Path(arguments["project_path"])
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        # Initialize agent if needed
        if not self.agent:
            try:
                # Create agent without any extra arguments
                self.agent = PortfolioAgent()
            except Exception as e:
                self.logger.warning(f"Could not initialize PortfolioAgent: {e}")
                # Create a minimal agent for file analysis only
                self.agent = None
        
        # Analyze project files
        file_analysis = self.file_analyzer.analyze_project(project_path)
        
        # Convert file_analysis to JSON-serializable format
        file_analysis_dict = {
            "files_analyzed": file_analysis["files_analyzed"],
            "total_lines": file_analysis["total_lines"],
            "technologies": list(file_analysis["technologies"]),
            "complexity_score": file_analysis["complexity_score"],
            "file_types": file_analysis.get("file_types", {}),
            "analyses": [
                {
                    "file": analysis["file"],
                    "analysis": {
                        "file_type": analysis["analysis"].file_type,
                        "content_summary": analysis["analysis"].content_summary,
                        "key_components": analysis["analysis"].key_components,
                        "technologies": analysis["analysis"].technologies,
                        "complexity_score": analysis["analysis"].complexity_score,
                        "lines_of_code": analysis["analysis"].lines_of_code
                    }
                }
                for analysis in file_analysis["analyses"]
            ]
        }
        
        # Use AI to generate project description if agent is available
        if self.agent:
            try:
                await self.agent.initialize_ollama()
                project_info = await self.agent.analyze_project(str(project_path))
                
                result = {
                    "project_name": project_info.name,
                    "description": project_info.description,
                    "technologies": project_info.technologies,
                    "bullet_points": project_info.bullet_points,
                    "special_features": project_info.special_features,
                    "file_analysis": file_analysis_dict
                }
            except Exception as e:
                self.logger.warning(f"AI analysis failed, using file analysis only: {e}")
                result = {
                    "project_name": project_path.name,
                    "description": f"Software project with {file_analysis['files_analyzed']} files",
                    "technologies": list(file_analysis['technologies']),
                    "bullet_points": [
                        f"Contains {file_analysis['files_analyzed']} source files",
                        f"Uses {len(file_analysis['technologies'])} different technologies",
                        f"Total lines of code: {file_analysis['total_lines']}"
                    ],
                    "special_features": [],
                    "file_analysis": file_analysis_dict
                }
        else:
            # Use file analysis only
            result = {
                "project_name": project_path.name,
                "description": f"Software project with {file_analysis['files_analyzed']} files",
                "technologies": list(file_analysis['technologies']),
                "bullet_points": [
                    f"Contains {file_analysis['files_analyzed']} source files",
                    f"Uses {len(file_analysis['technologies'])} different technologies",
                    f"Total lines of code: {file_analysis['total_lines']}"
                ],
                "special_features": [],
                "file_analysis": file_analysis_dict
            }
        
        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }
    
    async def _update_portfolio(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Update portfolio with a new project"""
        project_path = arguments["project_path"]
        mode = arguments.get("mode", "auto")
        
        # Initialize agent
        if not self.agent:
            self.agent = PortfolioAgent()
        
        # Run the workflow
        success = await self.agent.run_workflow(project_path, mode)
        
        if success:
            return {
                "content": [{"type": "text", "text": f"Successfully added project to portfolio: {project_path}"}]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Failed to add project to portfolio: {project_path}"}],
                "isError": True
            }
    
    async def _get_project_info(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed information about a project"""
        project_path = Path(arguments["project_path"])
        
        if not project_path.exists():
            raise ValueError(f"Project path does not exist: {project_path}")
        
        # Analyze project files
        file_analysis = self.file_analyzer.analyze_project(project_path)
        
        # Convert file_analysis to JSON-serializable format
        file_analysis_dict = {
            "files_analyzed": file_analysis["files_analyzed"],
            "total_lines": file_analysis["total_lines"],
            "technologies": list(file_analysis["technologies"]),
            "complexity_score": file_analysis["complexity_score"],
            "file_types": file_analysis.get("file_types", {}),
            "analyses": [
                {
                    "file": analysis["file"],
                    "analysis": {
                        "file_type": analysis["analysis"].file_type,
                        "content_summary": analysis["analysis"].content_summary,
                        "key_components": analysis["analysis"].key_components,
                        "technologies": analysis["analysis"].technologies,
                        "complexity_score": analysis["analysis"].complexity_score,
                        "lines_of_code": analysis["analysis"].lines_of_code
                    }
                }
                for analysis in file_analysis["analyses"]
            ]
        }
        
        # Get project structure
        project_structure = []
        for file_path in project_path.rglob('*'):
            if file_path.is_file():
                relative_path = str(file_path.relative_to(project_path))
                if not any(pattern in relative_path for pattern in ['node_modules', '.git', '__pycache__', 'venv']):
                    project_structure.append(relative_path)
        
        result = {
            "project_name": project_path.name,
            "project_path": str(project_path),
            "file_analysis": file_analysis_dict,
            "project_structure": project_structure[:50],  # Limit to first 50 files
            "total_files": len(project_structure)
        }
        
        return {
            "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
        }
    
    async def _deploy_portfolio(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy portfolio changes"""
        commit_message = arguments.get("commit_message", "Update portfolio")
        
        # Initialize agent
        if not self.agent:
            self.agent = PortfolioAgent()
        
        # Run git workflow
        success = self.agent.git_workflow(commit_message)
        
        if success:
            return {
                "content": [{"type": "text", "text": f"Successfully deployed portfolio with message: {commit_message}"}]
            }
        else:
            return {
                "content": [{"type": "text", "text": f"Failed to deploy portfolio"}],
                "isError": True
            }
    
    async def _list_projects(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """List all projects in the portfolio"""
        # Initialize agent
        if not self.agent:
            self.agent = PortfolioAgent()
        
        portfolio_file = Path(self.agent.config.portfolio_path) / "src" / "Portfolio.tsx"
        
        if not portfolio_file.exists():
            return {
                "content": [{"type": "text", "text": "Portfolio file not found"}],
                "isError": True
            }
        
        try:
            with open(portfolio_file, 'r') as f:
                content = f.read()
            
            # Extract project names from Portfolio.tsx
            import re
            project_matches = re.findall(r'name:\s*["\']([^"\']+)["\']', content)
            
            result = {
                "projects": project_matches,
                "total_projects": len(project_matches)
            }
            
            return {
                "content": [{"type": "text", "text": json.dumps(result, indent=2)}]
            }
        except Exception as e:
            return {
                "content": [{"type": "text", "text": f"Error reading portfolio: {str(e)}"}],
                "isError": True
            }

class SimpleMCPServer:
    """Simple MCP server that communicates via stdin/stdout"""
    
    def __init__(self):
        self.server = CustomMCPServer()
    
    async def run(self):
        """Run the MCP server"""
        print("Portfolio Agent MCP Server started", file=sys.stderr)
        
        while True:
            try:
                # Read input from stdin
                line = await asyncio.get_event_loop().run_in_executor(None, input)
                if not line:
                    continue
                
                request = json.loads(line)
                
                # Handle different request types
                if request.get("method") == "tools/list":
                    response = await self.server.list_tools()
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": response
                    }))
                
                elif request.get("method") == "tools/call":
                    tool_name = request["params"]["name"]
                    arguments = request["params"]["arguments"]
                    
                    result = await self.server.call_tool(tool_name, arguments)
                    
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "result": result
                    }))
                
                else:
                    print(json.dumps({
                        "jsonrpc": "2.0",
                        "id": request.get("id"),
                        "error": {"code": -32601, "message": "Method not found"}
                    }))
                
                sys.stdout.flush()
                
            except EOFError:
                break
            except json.JSONDecodeError as e:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": {"code": -32700, "message": f"Parse error: {str(e)}"}
                }))
                sys.stdout.flush()
            except Exception as e:
                print(json.dumps({
                    "jsonrpc": "2.0",
                    "id": request.get("id") if 'request' in locals() else None,
                    "error": {"code": -32603, "message": str(e)}
                }))
                sys.stdout.flush()

async def main():
    """Main entry point for MCP server"""
    parser = argparse.ArgumentParser(description="Portfolio Agent MCP Server")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--test", action="store_true", help="Run in test mode")
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(level=getattr(logging, args.log_level))
    
    if args.test:
        # Test mode - run a simple test
        server = CustomMCPServer()
        tools = await server.list_tools()
        print("Available tools:")
        for tool in tools["tools"]:
            print(f"  - {tool['name']}: {tool['description']}")
        return
    
    # Create and run server
    mcp_server = SimpleMCPServer()
    await mcp_server.run()

if __name__ == "__main__":
    asyncio.run(main()) 