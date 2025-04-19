#!/usr/bin/env bash
set -uo pipefail
# Removed the -e flag to prevent the script from exiting on non-zero return codes
# 1) Verify VS Code CLI
if ! command -v code &>/dev/null; then
  read -p "VS Code CLI ('code') not found. Install it now? [y/N]: " yn
  if [[ $yn =~ ^[Yy]$ ]]; then
    if [[ -e "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" ]]; then
      echo "Installing 'code' to /usr/local/bin..."
      sudo ln -sf "/Applications/Visual Studio Code.app/Contents/Resources/app/bin/code" /usr/local/bin/code
      echo "✅ 'code' installed."
    else
      echo "❌ Can't find VS Code.app. Please open VS Code, press ⇧⌘P and run 'Shell Command: Install \"code\" command in PATH'."
      exit 1
    fi
  else
    echo "❌ VS Code CLI is required. Exiting."
    exit 1
  fi
fi
# 2) Project name
read -p "Project name: " PROJECT_NAME
# 3) FileMaker file details
read -p "FileMaker file path or URL (leave blank to use default recommended): " FILEMAKER_PATH

if [[ -z "$FILEMAKER_PATH" ]]; then
  # Use default
  FILEMAKER_PATH="(use repo default)"
  FILE_NAME="(default)"
  SCRIPT_NAME="(default)"
  echo "Using default FileMaker configuration."
else
  # Get additional details
  read -p "FileMaker file name: " FILE_NAME
  read -p "FileMaker script name to run (to set the HTML): " SCRIPT_NAME
  
  # Set defaults if empty
  FILE_NAME=${FILE_NAME:-"unknown"}
  SCRIPT_NAME=${SCRIPT_NAME:-"JS * fetch"}
fi
# 4) Widget intention
read -p "What is the widget's intended purpose? " WIDGET_INTENTION
# 5) Styles example images
read -p "Do you have style/example images? [y/N]: " has_styles
STYLE_PATHS=()
if [[ $has_styles =~ ^[Yy]$ ]]; then
  echo "Enter all image paths (space‑separated):"
  read -a STYLE_PATHS
fi
# 6) Project directory
DEFAULT_DIR="$HOME/javascript"
read -p "Base directory for projects [$DEFAULT_DIR]: " PROJECT_DIR
PROJECT_DIR=${PROJECT_DIR:-$DEFAULT_DIR}
# ——————————————————————————————
# Tech‑stack questions
# ——————————————————————————————
echo
echo "Select tech‑stack options (comma‑separated numbers):"
echo "  1) CommonJS"
echo "  2) React"
echo "  3) Next.js"
read -p "Choice: " CHOICES
TECH=()
for c in ${CHOICES//,/ }; do
  case $c in
    1) TECH+=("CommonJS") ;;
    2) TECH+=("React")    ;;
    3) TECH+=("Next.js")  ;;
    *) echo "⚠️  Unknown: $c" ;;
  esac
done
read -p "Use TypeScript? [y/N]: " use_ts
USE_TS=$([[ $use_ts =~ ^[Yy]$ ]] && echo "enabled" || echo "disabled")
read -p "Use state management? [y/N]: " use_state
STATE_LIB="none"
if [[ $use_state =~ ^[Yy]$ ]]; then
  read -p "Preferred state library (e.g. Redux, MobX) or leave blank to decide later: " slib
  STATE_LIB=${slib:-"none"}
fi
# ——————————————————————————————
# Scaffold & install
# ——————————————————————————————
TARGET="$PROJECT_DIR/$PROJECT_NAME"
mkdir -p "$PROJECT_DIR"

# Check if target directory exists and is not empty
if [ -d "$TARGET" ] && [ "$(ls -A "$TARGET" 2>/dev/null)" ]; then
  read -p "Directory '$TARGET' already exists and is not empty. Overwrite? [y/N]: " overwrite
  if [[ $overwrite =~ ^[Yy]$ ]]; then
    echo "Removing existing directory..."
    rm -rf "$TARGET"
  else
    echo "Aborting. Please choose a different project name or location."
    exit 1
  fi
fi

git clone https://github.com/integrating-magic/js-dev-environment-new.git "$TARGET"
cd "$TARGET"
npm install

# Check if FileMakerService.js exists and create it if it doesn't
FM_SERVICE_PATH="$TARGET/src/services/FileMakerService.js"
if [ ! -f "$FM_SERVICE_PATH" ]; then
  echo "Creating FileMakerService.js..."
  mkdir -p "$TARGET/src/services"
  cat > "$FM_SERVICE_PATH" <<EOF
import FMGofer from 'fm-gofer';

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
EOF
  echo "✅ FileMakerService.js created."
fi

PROMPT="
## CONTEXT
This is a widget project named '$PROJECT_NAME' that the user described in the following: "$WIDGET_INTENTION". 
The widget is intended to be used in a FileMaker webviewer. The widget is being 
developed in a JavaScript environment with the following specifications:
– FileMaker file: $FILE_NAME
– Styles/examples: ${STYLE_PATHS[*]:-(none)}
– Tech stack: ${TECH[*]}, TypeScript: $USE_TS, State management: $STATE_LIB.

/service/FileMakerService.js is a service that provides a method to execute FileMaker 
scripts either synchronously or asynchronously based on the method parameter. This is 
the widget's primary means of communicating with FileMaker. The service is designed to be
used in a JavaScript environment, and it uses the FMGofer library to perform the script execution.

Widgets do not typically include testing, but you may include it if you feel it 
is necessary with permission. 

## TASKS
Complete the set up by updating 'widget.config.cjs'
module.exports = {
  widgetName: "$PROJECT_NAME" || "jsDev",
  server: "$FILEMAKER_PATH" || "$",
  file: "$FILE_NAME" || "jsDev",
  uploadScript: "$SCRIPT_NAME" || "UploadToHTML",
}

Then consider the user's intended purpose for the widget. If any aspect of its development remains unclear 
you should ask the user for clarification. Document the steps and stages of development in the 
/coding_prompts/development_tasks.md file. This file should include:
1. A description of the widget's intended purpose.
2. libraries and frameworks to install including FMGofer
3. State management to implement (if any)
4. Services to create (if any)
5. Components to create
6. Pages to create, (if any)

With the user's permission you may proceed to develop the widget's intended features and functionality

## CONSTRAINTS
Follow the directions provided in development_guidelines.md. If the file does not exist then use the following:
1. You may use third-party libraries under the following conditions.
   - You must not use any third-party libraries or frameworks without user consent.
   - You must not use any third-party libraries or frameworks that are not compatible with FileMaker.
   - You must not use any third-party libraries or frameworks that are not compatible with the user's intended purpose for the widget.
   - You may not use libraries if one already exists that completes the same functionality.
2. You must not use any deprecated or obsolete JavaScript features.
3. You must not use any non-standard JavaScript features or APIs.
4. You must not use any non-standard HTML or CSS features or APIs.
    - CSS must remain grouped and organized in a single file.
    - CSS must be a DRY as possible
    - CSS should comply with the example provided. If none is provided then implement a modern elegent consistent style
5. You must not use any non-standard FileMaker features or APIs.
"

# Write the prompt to a file for reference
mkdir -p "$TARGET/coding_prompts"
echo "Writing prompt to $TARGET/coding_prompts/llm_prompt.md..."

PROMPT_FILE="$TARGET/coding_prompts/llm_prompt.md"
cat > "$PROMPT_FILE" <<EOF
# LLM Prompt
$PROMPT
EOF

# ——————————————————————————————
# Open VS Code in new window
# ——————————————————————————————
echo "Opening VS Code in new window..."
code -n "$TARGET"

echo
echo "🎉 Project '$PROJECT_NAME' has been set up in $TARGET"