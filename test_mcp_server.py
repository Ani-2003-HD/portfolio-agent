#!/usr/bin/env python3
"""
Test script for MCP server functionality
"""

import asyncio
import json
import subprocess
import sys
from pathlib import Path

async def test_mcp_server():
    """Test the MCP server with JSON-RPC requests"""
    
    # Start the MCP server process
    process = await asyncio.create_subprocess_exec(
        sys.executable, "mcp_server.py",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    try:
        # Test 1: List tools
        list_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list"
        }
        
        print("Testing tools/list...")
        process.stdin.write((json.dumps(list_request) + "\n").encode())
        await process.stdin.drain()
        
        response = await process.stdout.readline()
        result = json.loads(response.decode().strip())
        
        if "result" in result and "tools" in result["result"]:
            print("✅ tools/list works!")
            for tool in result["result"]["tools"]:
                print(f"  - {tool['name']}: {tool['description']}")
        else:
            print("❌ tools/list failed:", result)
            return False
        
        # Test 2: Call analyze_project tool
        analyze_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "analyze_project",
                "arguments": {
                    "project_path": "."
                }
            }
        }
        
        print("\nTesting analyze_project...")
        process.stdin.write((json.dumps(analyze_request) + "\n").encode())
        await process.stdin.drain()
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        response = await process.stdout.readline()
        if not response:
            print("❌ No response from analyze_project")
            return False
            
        try:
            result = json.loads(response.decode().strip())
            
            if "result" in result and "content" in result["result"]:
                print("✅ analyze_project works!")
                content = result["result"]["content"][0]["text"]
                data = json.loads(content)
                print(f"  - Project: {data.get('project_name', 'Unknown')}")
                print(f"  - Technologies: {', '.join(data.get('technologies', []))}")
            else:
                print("❌ analyze_project failed:", result)
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse response: {e}")
            print(f"Response: {response.decode()}")
            return False
        
        # Test 3: Call get_project_info tool
        info_request = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "get_project_info",
                "arguments": {
                    "project_path": "."
                }
            }
        }
        
        print("\nTesting get_project_info...")
        process.stdin.write((json.dumps(info_request) + "\n").encode())
        await process.stdin.drain()
        
        # Wait a bit for processing
        await asyncio.sleep(0.1)
        
        response = await process.stdout.readline()
        if not response:
            print("❌ No response from get_project_info")
            return False
            
        try:
            result = json.loads(response.decode().strip())
            
            if "result" in result and "content" in result["result"]:
                print("✅ get_project_info works!")
                content = result["result"]["content"][0]["text"]
                data = json.loads(content)
                print(f"  - Files analyzed: {data.get('file_analysis', {}).get('files_analyzed', 0)}")
                print(f"  - Total lines: {data.get('file_analysis', {}).get('total_lines', 0)}")
            else:
                print("❌ get_project_info failed:", result)
                return False
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse response: {e}")
            print(f"Response: {response.decode()}")
            return False
        
        print("\n🎉 All MCP server tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    
    finally:
        # Clean up
        process.terminate()
        await process.wait()

def test_direct_api():
    """Test the MCP server API directly without JSON-RPC"""
    print("Testing direct API...")
    
    async def run_test():
        from mcp_server import CustomMCPServer
        
        server = CustomMCPServer()
        
        # Test list tools
        tools = await server.list_tools()
        print(f"✅ Found {len(tools['tools'])} tools")
        
        # Test analyze project
        result = await server.call_tool("analyze_project", {"project_path": "."})
        if "content" in result:
            print("✅ Direct API works!")
            return True
        else:
            print("❌ Direct API failed")
            return False
    
    return asyncio.run(run_test())

if __name__ == "__main__":
    print("🧪 Testing MCP Server Functionality")
    print("=" * 50)
    
    # Test direct API
    if test_direct_api():
        print("\n✅ Direct API tests passed!")
    else:
        print("\n❌ Direct API tests failed!")
        sys.exit(1)
    
    # Test JSON-RPC interface
    if asyncio.run(test_mcp_server()):
        print("\n✅ JSON-RPC tests passed!")
    else:
        print("\n❌ JSON-RPC tests failed!")
        sys.exit(1)
    
    print("\n🎉 All MCP functionality tests passed!") 