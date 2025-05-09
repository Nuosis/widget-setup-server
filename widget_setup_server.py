import os
import subprocess
from typing import Annotated

from mcp.server.fastmcp import FastMCP

from prompt_tool import get_prompt

mcp = FastMCP("widget-setup")

# Define all required inputs and their questions
REQUIRED_INPUTS = [
    {
        "name": "widgetIntention",
        "question": "What is the widget's intended purpose? The more detail you provide the better",
        "suggestions": [
            "Create a date picker widget for selecting dates in FileMaker",
            "Build a data table widget for displaying and editing FileMaker records",
            "Develop a chart widget for visualizing FileMaker data",
        ],
        "description": "A detailed description of what the widget will do and how it will be used",
        "required": True,
    },
    {
        "name": "fileName",
        "question": "What is the FileMaker file name? Make sure to include .fmp12",
        "suggestions": ["MyDatabase.fmp12", "Development.fmp12", "Production.fmp12"],
        "description": "The name of the FileMaker file that will host this widget (.fmp12 extension required)",
        "required": True,
    },
    {
        "name": "fileMakerPath",
        "question": "Where is the FileMaker file located? Provide a url or path.",
        "suggestions": [
            "fmp://$/MyDatabase",
            "fmp://localhost/MyDatabase",
            "/path/to/MyDatabase.fmp12",
        ],
        "description": "The URL or file path where the FileMaker file can be accessed",
        "required": True,
    },
    {
        "name": "techStack",
        "question": "What is the tech stack? (1=CommonJS, 2=React, 3=Next.js)",
        "suggestions": ["[1]", "[2]", "[3]"],
        "description": "The technical framework to use: CommonJS for simple widgets, React for component-based UIs, Next.js for complex applications",
        "required": True,
    },
    {
        "name": "scriptName",
        "question": "What is the name of the FileMaker script to run for data fetching? (default: JS * fetch)",
        "suggestions": ["JS * fetch", "UploadToHTML", "JS * performSearch"],
        "description": "The FileMaker script that will handle communication between the widget and FileMaker",
        "required": False,
        "default": "JS * fetch",
    },
    {
        "name": "useTypeScript",
        "question": "Do you want to use TypeScript? (yes/no)",
        "suggestions": ["yes", "no"],
        "description": "Whether to enable TypeScript support for better type safety and development experience",
        "required": False,
        "default": "no",
    },
    {
        "name": "stateLibrary",
        "question": "What state management library do you want to use? (e.g., Redux, MobX, None)",
        "suggestions": ["None", "Redux", "MobX", "Zustand"],
        "description": "The library to use for managing application state, if needed",
        "required": False,
        "default": "None",
    },
]


@mcp.tool("get_version")
def get_version():
    """Get the current version of the widget setup server."""
    return {"version": "1.3.1"}


DEFAULT_WORKSPACE = os.path.expanduser("~/javascript")


@mcp.tool("initialize_repo")
def initialize_repo(
    projectName: Annotated[
        str, "Name of the widget project. Use the name of the current directory"
    ] = None,
    projectDir: Annotated[
        str, "Base directory for projects. Must be a fully qualified path"
    ] = None,
):
    """
    Initialize a new FileMaker widget repository with the basic file structure.

    Args:
        projectName: Name of the widget project. Use the name of the current directory.
        projectDir: Base directory for projects. Uses the fully qualified path to the current directory.

    Returns:
        A dictionary containing the result of the operation.
    """
    # Get current directory information
    current_dir = os.path.basename(os.getcwd())

    # Use provided values or defaults
    projectName = projectName or current_dir

    # Validate project name
    if not projectName:
        return {
            "error": "Project name is required and could not be determined automatically"
        }

    # projectDir must be provided now (fully qualified path)
    if not projectDir:
        return {"error": "Project directory (fully qualified path) is required"}

    # Target directory is the project directory
    target_dir = projectDir

    # Check if target directory is a git repo already
    if os.path.exists(os.path.join(target_dir, ".git")):
        return {
            "error": f"Directory '{target_dir}' is already a git repository. Cannot initialize a new repository here."
        }

    try:
        # Get the parent directory
        parent_dir = os.path.dirname(target_dir)

        # Store the original directory to return to later
        original_dir = os.getcwd()

        # Change to the parent directory
        os.chdir(parent_dir)

        # Clone the repository directly to the target directory
        clone_cmd = [
            "git",
            "clone",
            "https://github.com/Nuosis/js-ai-dev-environment.git",
            os.path.basename(target_dir),
        ]
        process = subprocess.run(clone_cmd, capture_output=True, text=True, check=True)

        # Change back to the widget directory
        os.chdir(target_dir)

        # Install npm dependencies
        npm_cmd = ["npm", "install"]
        npm_process = subprocess.run(
            npm_cmd, capture_output=True, text=True, check=True
        )

        # Create FileMakerService.js if it doesn't exist
        fm_service_path = os.path.join(
            target_dir, "src", "services", "FileMakerService.js"
        )
        os.makedirs(os.path.dirname(fm_service_path), exist_ok=True)

        if not os.path.exists(fm_service_path):
            with open(fm_service_path, "w") as f:
                f.write("""import FMGofer from 'fm-gofer';

/**
 * FileMaker Service for executing FileMaker scripts
 *
 * This service provides a method to execute FileMaker scripts either synchronously
 * or asynchronously based on the method parameter.
 */
const FileMakerService = {
  /**
   * Execute a FileMaker script
   *
   * @param {Object} props - Properties for script execution
   * @param {string} props.method - Method type ('async' or any other value for sync)
   * @param {string} props.script - Name of the FileMaker script to execute
   * @param {string|Object} props.params - Parameters to pass to the FileMaker script (will be stringified if object)
   * @returns {Promise<string>|void} - Returns a promise if method is async, otherwise void
   */
  executeScript({ method, script = "JS * fetch", params }) {
    // Convert params to string if it's an object
    const paramString = typeof params !== 'string' ? JSON.stringify(params) : params;

    // Check if method is async
    if (method === 'async') {
      return FMGofer.PerformScript(script, paramString);
    } else {
      // Use synchronous method
      return FileMaker.PerformScript(script, paramString);
    }
  }
};

export default FileMakerService;
""")

        # Create coding_prompts directory
        prompts_dir = os.path.join(target_dir, "coding_prompts")
        os.makedirs(prompts_dir, exist_ok=True)

        # Change back to the original directory
        os.chdir(original_dir)

        return {
            "result": f"Widget project '{projectName}' initialized successfully at {target_dir}. "
            "You should now open the filemaker file. "
            "Then you should use the get_prompt tool to generate the prompt. You MUST ask the user the following question in sequential oder: \n"
            f"1. {REQUIRED_INPUTS[0]['question']}\n"
            f"2. {REQUIRED_INPUTS[1]['question']}\n"
            f"3. {REQUIRED_INPUTS[2]['question']}\n"
            f"4. {REQUIRED_INPUTS[3]['question']}\n"
            f"5. {REQUIRED_INPUTS[4]['question']}\n"
            f"6. {REQUIRED_INPUTS[5]['question']}\n"
            "Once completed, use these user responses for the get_prompt tools props.",
            "project_path": target_dir,
        }

    except subprocess.CalledProcessError as e:
        # Change back to the original directory before returning error
        if "original_dir" in locals():
            os.chdir(original_dir)
        return {"error": f"Command failed: {e.cmd}. Error: {e.stderr}"}
    except Exception as e:
        # Change back to the original directory before returning error
        if "original_dir" in locals():
            os.chdir(original_dir)
        return {"error": f"Failed to initialize widget project: {str(e)}"}


# Register get_prompt from prompt_tool as a tool
mcp.tool("get_prompt")(get_prompt)


if __name__ == "__main__":
    mcp.run()
