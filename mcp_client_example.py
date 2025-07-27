#!/usr/bin/env python3
"""
Example MCP Client for Portfolio Agent
Shows how to use the MCP server programmatically
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

class MCPClient:
    """Simple MCP client for Portfolio Agent"""
    
    def __init__(self, server_command="./portfolio-mcp"):
        self.server_command = server_command
        self.process = None
    
    async def start_server(self):
        """Start the MCP server"""
        self.process = await asyncio.create_subprocess_exec(
            self.server_command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        print("🚀 MCP Server started")
    
    async def stop_server(self):
        """Stop the MCP server"""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            print("🛑 MCP Server stopped")
    
    async def send_request(self, method, params=None, request_id=1):
        """Send a JSON-RPC request to the server"""
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method
        }
        
        if params:
            request["params"] = params
        
        # Send request
        self.process.stdin.write((json.dumps(request) + "\n").encode())
        await self.process.stdin.drain()
        
        # Wait for response
        await asyncio.sleep(0.1)
        response = await self.process.stdout.readline()
        
        if response:
            return json.loads(response.decode().strip())
        else:
            return None
    
    async def list_tools(self):
        """List available tools"""
        response = await self.send_request("tools/list")
        if response and "result" in response:
            return response["result"]["tools"]
        return []
    
    async def analyze_project(self, project_path):
        """Analyze a project"""
        params = {
            "name": "analyze_project",
            "arguments": {
                "project_path": project_path
            }
        }
        
        response = await self.send_request("tools/call", params)
        if response and "result" in response:
            content = response["result"]["content"][0]["text"]
            return json.loads(content)
        return None
    
    async def get_project_info(self, project_path):
        """Get detailed project information"""
        params = {
            "name": "get_project_info",
            "arguments": {
                "project_path": project_path
            }
        }
        
        response = await self.send_request("tools/call", params)
        if response and "result" in response:
            content = response["result"]["content"][0]["text"]
            return json.loads(content)
        return None

async def main():
    """Example usage of the MCP client"""
    client = MCPClient()
    
    try:
        # Start the server
        await client.start_server()
        
        # List available tools
        print("\n📋 Available tools:")
        tools = await client.list_tools()
        for tool in tools:
            print(f"  - {tool['name']}: {tool['description']}")
        
        # Analyze current project
        print("\n🔍 Analyzing current project...")
        analysis = await client.analyze_project(".")
        
        if analysis:
            print(f"✅ Project: {analysis.get('project_name', 'Unknown')}")
            print(f"📝 Description: {analysis.get('description', 'No description')}")
            print(f"🔧 Technologies: {', '.join(analysis.get('technologies', []))}")
            
            file_analysis = analysis.get('file_analysis', {})
            print(f"📊 Files analyzed: {file_analysis.get('files_analyzed', 0)}")
            print(f"📏 Total lines: {file_analysis.get('total_lines', 0)}")
        
        # Get detailed project info
        print("\n📁 Getting detailed project info...")
        info = await client.get_project_info(".")
        
        if info:
            print(f"📂 Project structure (first 10 files):")
            for file_path in info.get('project_structure', [])[:10]:
                print(f"  - {file_path}")
        
        print("\n🎉 MCP client example completed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    finally:
        # Stop the server
        await client.stop_server()

if __name__ == "__main__":
    asyncio.run(main()) 