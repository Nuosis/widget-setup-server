# Widget Setup MCP Server

This MCP (Model Context Protocol) server provides tools to create FileMaker widget projects. It automates the setup process by initializing the repository and generating prompts for agents.

## Features

- Initializes a new FileMaker widget project repository
- Generates prompts for agents to complete the widget setup
- Sets up the project structure and installs dependencies
- Creates necessary files and directories

## Prerequisites

- Python 3.13 or higher
- uv
- Git (for cloning the repository)
- npm (for installing JavaScript dependencies)

## Installation

1. Clone or download this repository
2. Install the dependencies:
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv sync
```

## Client Configuration

To use this server with an MCP client, you need to connect to it using the server name "widget-setup". Here's how to connect using different client libraries:

### Code Agent

```json
{
    "mcpServers": {
        "widget-setup": {
            "command": "/Users/<<user>>/.local/bin/uv",
            "args": [
                "--directory", "/Users/<<user>>/<<path to mcp dir>>/widget-setup-server",
                "run", "widget_setup_server.py"
            ]
        }
    }
}
```

### Python Client

```python
from mcp.client import Client

# Connect to the widget-setup server
client = Client()
client.connect_stdio_server("widget-setup", ["python", "widget_setup_server.py"])

# Now you can use the server's tools
result = client.use_tool("widget-setup", "initialize_repo", {
    "projectName": "MyWidget"
})
print(result)

# Generate a prompt for the agent
prompt_result = client.use_tool("widget-setup", "get_prompt", {
    "projectName": "MyWidget",
    "widgetIntention": "A widget to display customer data",
    "techStack": [2],
    "useTypeScript": True
})
print(prompt_result["prompt"])
```

### Command Line

Using the MCP CLI:

```bash
# Start the server in one terminal
python widget_setup_server.py

# In another terminal, use the MCP CLI to connect and use tools
mcp connect stdio widget-setup "python widget_setup_server.py"
mcp use widget-setup initialize_repo --projectName="MyWidget"
mcp use widget-setup get_prompt --projectName="MyWidget" --widgetIntention="A widget to display customer data"
```

## Available Tools

### initialize_repo

Initializes a new FileMaker widget repository with the basic file structure.

**Parameters:**
- `projectName` (required): Name of the widget project.
- `projectDir` (optional): Base directory for projects. If not provided, it will use the default directory (~/javascript).

**Returns:**
- `result`: A message indicating the widget project was initialized
- `project_path`: The path to the created project

**Example:**
```python
# Initialize a new widget repository
response = client.use_tool("widget-setup", "initialize_repo", {
    "projectName": "CustomerWidget"
})
```

### get_prompt

Generates a prompt for the agent to use to finish the widget setup.

**Parameters:**
- `projectName` (required): Name of the widget project.
- `widgetIntention` (required): Description of the widget's intended purpose.
- `fileMakerPath` (optional): FileMaker file path or URL.
- `fileName` (optional): FileMaker file name.
- `scriptName` (optional): FileMaker script name to run.
- `techStack` (optional): Tech stack options (1=CommonJS, 2=React, 3=Next.js).
- `useTypeScript` (optional): Whether to use TypeScript.
- `stateLibrary` (optional): Name of the state management library.
- `stylePaths` (optional): List of paths to style/example images.

**Returns:**
- `result`: A message indicating the prompt was generated
- `prompt`: The generated prompt for the agent

**Example:**
```python
# Generate a prompt for a React widget with TypeScript
response = client.use_tool("widget-setup", "get_prompt", {
    "projectName": "CustomerWidget",
    "widgetIntention": "A widget to display customer data",
    "techStack": [2],
    "useTypeScript": True
})

# Generate a prompt for a basic CommonJS widget
response = client.use_tool("widget-setup", "get_prompt", {
    "projectName": "SimpleWidget",
    "widgetIntention": "A simple widget for data entry",
    "techStack": [1]
})
```

## Development

If you want to modify the server or add new features:

1. Edit the files in the project directory
2. Restart the MCP server for changes to take effect
