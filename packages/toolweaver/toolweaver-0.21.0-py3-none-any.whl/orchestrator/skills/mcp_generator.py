"""
MCP Server Generator: Auto-generate Model Context Protocol servers for skills.

Generates MCP-compliant servers that expose skills as tools, enabling integration
with MCP clients like Claude Desktop, VS Code extensions, and other MCP-aware applications.
"""

import json
import logging
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP tool definition."""

    name: str
    description: str
    inputSchema: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


@dataclass
class MCPServer:
    """MCP server configuration."""

    name: str
    version: str
    description: str
    tools: list[MCPTool]

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "tools": [t.to_dict() for t in self.tools],
        }


class MCPGenerator:
    """Generator for MCP protocol servers from skills."""

    # MCP protocol version
    PROTOCOL_VERSION = "2024-11-05"

    def __init__(self, skills_dir: str = "orchestrator/skills"):
        """
        Initialize MCP generator.

        Args:
            skills_dir: Directory containing skill definitions
        """
        self.skills_dir = Path(skills_dir)

    def load_skill_metadata(self, skill_name: str) -> dict[str, Any] | None:
        """
        Load skill metadata from YAML file.

        Args:
            skill_name: Name of the skill

        Returns:
            Skill metadata dictionary or None
        """
        yaml_path = self.skills_dir / skill_name / f"{skill_name}.yaml"

        if not yaml_path.exists():
            logger.warning(f"Skill metadata not found: {yaml_path}")
            return None

        try:
            with open(yaml_path, encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.error(f"Failed to load skill metadata for {skill_name}: {e}")
            return None

    def generate_tool_from_skill(self, skill_name: str) -> MCPTool | None:
        """
        Generate MCP tool definition from skill metadata.

        Args:
            skill_name: Name of the skill

        Returns:
            MCPTool or None
        """
        metadata = self.load_skill_metadata(skill_name)
        if not metadata:
            return None

        # Build input schema from parameters
        properties = {}
        required = []

        parameters = metadata.get("parameters", {})
        for param_name, param_def in parameters.items():
            # Handle both dict and simple type definitions
            if isinstance(param_def, dict):
                param_type = param_def.get("type", "string")
                param_desc = param_def.get("description", "")
                param_required = param_def.get("required", False)
                param_default = param_def.get("default")

                properties[param_name] = {
                    "type": param_type,
                    "description": param_desc,
                }

                if param_default is not None:
                    properties[param_name]["default"] = param_default

                if param_required:
                    required.append(param_name)
            else:
                # Simple type definition
                properties[param_name] = {
                    "type": "string",
                    "description": f"Parameter: {param_name}",
                }

        input_schema = {
            "type": "object",
            "properties": properties,
        }

        if required:
            input_schema["required"] = required

        # Create MCP tool
        tool = MCPTool(
            name=skill_name.replace("_", "-"),
            description=metadata.get("description", f"Execute {skill_name} skill"),
            inputSchema=input_schema,
        )

        return tool

    def generate_server(
        self,
        skill_names: list[str],
        server_name: str = "toolweaver-skills",
        version: str = "1.0.0",
    ) -> MCPServer:
        """
        Generate MCP server configuration for multiple skills.

        Args:
            skill_names: List of skill names to include
            server_name: Name of the MCP server
            version: Server version

        Returns:
            MCPServer configuration
        """
        tools = []

        for skill_name in skill_names:
            tool = self.generate_tool_from_skill(skill_name)
            if tool:
                tools.append(tool)
                logger.info(f"Generated MCP tool for skill: {skill_name}")
            else:
                logger.warning(f"Skipped skill (no metadata): {skill_name}")

        server = MCPServer(
            name=server_name,
            version=version,
            description=f"MCP server exposing {len(tools)} ToolWeaver skills",
            tools=tools,
        )

        return server

    def generate_server_code(self, server: MCPServer, output_dir: str = "generated") -> str:
        """
        Generate Python server implementation code.

        Args:
            server: MCP server configuration
            output_dir: Output directory for generated code

        Returns:
            Path to generated server file
        """
        output_path = Path(output_dir) / f"{server.name.replace('-', '_')}_server.py"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Generate server code
        code = self._generate_server_template(server)

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(code)

        logger.info(f"Generated MCP server code: {output_path}")
        return str(output_path)

    def _generate_server_template(self, server: MCPServer) -> str:
        """Generate Python server template code."""
        tools_json = json.dumps(server.to_dict()["tools"], indent=2)

        tool_handlers = "\n\n".join([self._generate_tool_handler(tool) for tool in server.tools])

        tool_dispatch = "\n        ".join(
            [f'"{tool.name}": handle_{tool.name.replace("-", "_")},' for tool in server.tools]
        )

        template = f'''"""
Auto-generated MCP Server: {server.name}

Generated by ToolWeaver MCP Generator
Protocol Version: {self.PROTOCOL_VERSION}
Server Version: {server.version}

This server exposes {len(server.tools)} skills as MCP tools.
"""

import json
import sys
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# ===== MCP Protocol Implementation =====

class MCPServer:
    """MCP protocol server implementation."""

    def __init__(self):
        """Initialize MCP server."""
        self.tools = {tools_json}

    def handle_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming MCP request.

        Args:
            request: MCP request dictionary

        Returns:
            MCP response dictionary
        """
        method = request.get("method")
        params = request.get("params", {{}})
        request_id = request.get("id")

        try:
            if method == "tools/list":
                result = {{"tools": self.tools}}
            elif method == "tools/call":
                tool_name = params.get("name")
                arguments = params.get("arguments", {{}})
                result = self._call_tool(tool_name, arguments)
            elif method == "initialize":
                result = {{
                    "protocolVersion": "{self.PROTOCOL_VERSION}",
                    "serverInfo": {{
                        "name": "{server.name}",
                        "version": "{server.version}",
                    }},
                    "capabilities": {{
                        "tools": {{}},
                    }},
                }}
            else:
                raise ValueError(f"Unknown method: {{method}}")

            return {{
                "jsonrpc": "2.0",
                "id": request_id,
                "result": result,
            }}

        except Exception as e:
            logger.error(f"Error handling request: {{e}}")
            return {{
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {{
                    "code": -32603,
                    "message": str(e),
                }},
            }}

    def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call a tool by name.

        Args:
            tool_name: Name of tool to call
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        handler = TOOL_HANDLERS.get(tool_name)

        if not handler:
            raise ValueError(f"Unknown tool: {{tool_name}}")

        result = handler(**arguments)

        return {{
            "content": [
                {{
                    "type": "text",
                    "text": json.dumps(result, indent=2),
                }}
            ]
        }}

    def run(self):
        """Run MCP server (stdio transport)."""
        logger.info("Starting MCP server: {server.name}")

        for line in sys.stdin:
            try:
                request = json.loads(line.strip())
                response = self.handle_request(request)
                print(json.dumps(response), flush=True)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON: {{e}}")
            except Exception as e:
                logger.error(f"Error processing request: {{e}}")


# ===== Tool Handlers =====

{tool_handlers}


# Tool handler registry
TOOL_HANDLERS = {{
        {tool_dispatch}
}}


# ===== Main Entry Point =====

def main():
    """Main entry point."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )

    server = MCPServer()
    server.run()


if __name__ == "__main__":
    main()
'''

        return template

    def _generate_tool_handler(self, tool: MCPTool) -> str:
        """Generate handler function for a tool."""
        handler_name = f"handle_{tool.name.replace('-', '_')}"

        # Extract parameters from schema
        properties = tool.inputSchema.get("properties", {})
        params = []
        for param_name, param_def in properties.items():
            param_type = param_def.get("type", "str")
            type_map = {
                "string": "str",
                "integer": "int",
                "number": "float",
                "boolean": "bool",
                "array": "list",
                "object": "dict",
            }
            python_type = type_map.get(param_type, "Any")
            params.append(f"{param_name}: {python_type}")

        params_str = ", ".join(params) if params else "**kwargs"

        handler = f'''def {handler_name}({params_str}) -> Dict[str, Any]:
    """
    Handle {tool.name} tool execution.

    {tool.description}
    """
    # TODO: Implement actual skill execution logic
    # This is a placeholder that should be replaced with real skill invocation

    logger.info(f"Executing tool: {tool.name}")

    return {{
        "status": "success",
        "tool": "{tool.name}",
        "message": "Tool executed successfully (placeholder)",
        "result": {{"placeholder": True}},
    }}'''

        return handler

    def generate_all_skills_server(self, output_dir: str = "generated") -> str:
        """
        Generate MCP server for all available skills.

        Args:
            output_dir: Output directory

        Returns:
            Path to generated server file
        """
        # Scan skills directory
        skill_names = []
        for skill_dir in self.skills_dir.iterdir():
            if skill_dir.is_dir() and not skill_dir.name.startswith("_"):
                yaml_file = skill_dir / f"{skill_dir.name}.yaml"
                if yaml_file.exists():
                    skill_names.append(skill_dir.name)

        logger.info(f"Found {len(skill_names)} skills: {skill_names}")

        # Generate server
        server = self.generate_server(skill_names)
        return self.generate_server_code(server, output_dir)

    def export_mcp_config(
        self,
        server: MCPServer,
        output_path: str = "mcp_config.json",
    ) -> None:
        """
        Export MCP server configuration to JSON.

        Args:
            server: MCP server
            output_path: Output file path
        """
        config = server.to_dict()

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        logger.info(f"Exported MCP config: {output_path}")

    def generate_client_example(
        self,
        server: MCPServer,
        output_path: str = "generated/mcp_client_example.py",
    ) -> None:
        """
        Generate example client code for testing the MCP server.

        Args:
            server: MCP server configuration
            output_path: Output file path
        """
        output_path_obj = Path(output_path)
        output_path_obj.parent.mkdir(parents=True, exist_ok=True)

        tool_examples = "\n\n".join(
            [
                self._generate_tool_example(tool)
                for tool in server.tools[:3]  # First 3 tools
            ]
        )

        client_code = f'''"""
Example MCP Client for {server.name}

This is an example client demonstrating how to interact with the MCP server.
"""

import json
import subprocess
import sys


class MCPClient:
    """Simple MCP client using stdio transport."""

    def __init__(self, server_command: list):
        """
        Initialize MCP client.

        Args:
            server_command: Command to start server (e.g., ["python", "server.py"])
        """
        self.process = subprocess.Popen(
            server_command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

    def send_request(self, method: str, params: dict = None) -> dict:
        """
        Send request to MCP server.

        Args:
            method: MCP method name
            params: Method parameters

        Returns:
            Server response
        """
        request = {{
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or {{}},
        }}

        # Send request
        request_str = json.dumps(request)
        self.process.stdin.write(request_str + "\\n")
        self.process.stdin.flush()

        # Read response
        response_str = self.process.stdout.readline()
        return json.loads(response_str)

    def initialize(self) -> dict:
        """Initialize connection with server."""
        return self.send_request("initialize")

    def list_tools(self) -> dict:
        """List available tools."""
        return self.send_request("tools/list")

    def call_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        Call a tool.

        Args:
            tool_name: Name of tool
            arguments: Tool arguments

        Returns:
            Tool result
        """
        return self.send_request("tools/call", {{
            "name": tool_name,
            "arguments": arguments,
        }})

    def close(self):
        """Close connection."""
        self.process.terminate()
        self.process.wait()


# ===== Example Usage =====

def main():
    """Example client usage."""
    print("Starting MCP client example...")

    # Start client
    client = MCPClient(["python", "{server.name.replace("-", "_")}_server.py"])

    try:
        # Initialize
        print("\\n1. Initializing connection...")
        response = client.initialize()
        print(json.dumps(response, indent=2))

        # List tools
        print("\\n2. Listing available tools...")
        response = client.list_tools()
        print(f"Found {{len(response['result']['tools'])}} tools")

        # Call tool examples
{tool_examples}

    finally:
        client.close()
        print("\\nClient closed.")


if __name__ == "__main__":
    main()
'''

        with open(output_path_obj, "w", encoding="utf-8") as f:
            f.write(client_code)

        logger.info(f"Generated client example: {output_path_obj}")

    def _generate_tool_example(self, tool: MCPTool) -> str:
        """Generate example tool call."""
        # Create sample arguments
        properties = tool.inputSchema.get("properties", {})
        sample_args: dict[str, Any] = {}

        for param_name, param_def in properties.items():
            param_type = param_def.get("type", "string")
            if param_type == "string":
                sample_args[param_name] = f"sample_{param_name}"
            elif param_type == "integer":
                sample_args[param_name] = 42
            elif param_type == "number":
                sample_args[param_name] = 3.14
            elif param_type == "boolean":
                sample_args[param_name] = True
            elif param_type == "array":
                sample_args[param_name] = ["item1", "item2"]
            else:
                sample_args[param_name] = {{"key": "value"}}

        args_json = json.dumps(sample_args, indent=12)

        return f'''        # Call {tool.name}
        print("\\n3. Calling {tool.name}...")
        response = client.call_tool("{tool.name}", {args_json})
        print(json.dumps(response, indent=2))'''
