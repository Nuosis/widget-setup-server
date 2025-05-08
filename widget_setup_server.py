import base64
import os
import subprocess
from typing import Annotated, List

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("widget-setup")
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
            "result": f"Widget project '{projectName}' initialized successfully at {target_dir}",
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


@mcp.tool("get_prompt")
def get_prompt(
    widgetIntention: Annotated[
        str, "Description of the widget's purpose and functionality"
    ],
    projectName: Annotated[
        str, "Name of the widget project, defaults to current directory name"
    ] = None,
    fileMakerPath: Annotated[
        str, "FileMaker file URL or path for database connection"
    ] = "",
    fileName: Annotated[str, "Name of the FileMaker database file (.fmp12)"] = "",
    scriptName: Annotated[
        str, "Name of the FileMaker script to execute for HTML upload"
    ] = "",
    techStack: Annotated[
        List[int], "List of tech stack choices (1=CommonJS, 2=React, 3=Next.js)"
    ] = None,
    useTypeScript: Annotated[bool, "Whether to enable TypeScript support"] = False,
    stateLibrary: Annotated[
        str, "State management library to use (Redux, MobX, Zustand, None)"
    ] = "",
    stylePaths: Annotated[List[str], "Paths to CSS files or image examples"] = None,
):
    """
    Receive instructions for the agent to use to finish the widget setup after the repo has been initialized.
    Every argument must be clarified by the user. The agent should collect the information one by one.

    Args:
        widgetIntention (str): Description of the widget's intended purpose.
            Format: A detailed text description
            Example: "Create a widget that displays JSON data in a table format"
            Required: Yes
            Ask: "What is the widget's intended purpose? The more detail you provide the better"

        projectName (str, optional): Name of the widget project.
            Format: String, defaults to current directory name
            Example: "json-table-widget"
            Required: No
            Note: Does not require user input, automatically uses current directory name if not provided

        fileName (str): FileMaker file name.
            Format: String ending with .fmp12
            Example: "MyDatabase.fmp12"
            Required: Yes
            Ask: "What is the FileMaker file name? Make sure to include .fmp12"

        fileMakerPath (str): FileMaker file path or URL.
            Format: URL or file path
            Example: "fmp://$/MyDatabase" or "/path/to/file"
            Required: Yes
            Ask: "Where is the FileMaker file located? Provide a url or path."

        scriptName (str): FileMaker script name to run.
            Format: String
            Example: "UploadToHTML"
            Default: "JS * fetch"
            Ask: "What is the name of the FileMaker script to run to upload the html code? default is 'UploadToHTML'"

        techStack (list): Tech stack options.
            Format: List of integers [1, 2, or 3]
            Values: 1=CommonJS, 2=React, 3=Next.js
            Example: [1] for CommonJS, [2] for React
            Required: Yes
            Ask: "What is the tech stack? (1=CommonJS, 2=React, 3=Next.js)"

        useTypeScript (bool): Whether to use TypeScript.
            Format: Boolean
            Example: True or False
            Default: False
            Ask: "Do you want to use TypeScript? (yes/no)"

        stateLibrary (str): Name of the state management library.
            Format: String
            Example: "Redux", "MobX", "Zustand", "None"
            Default: ""
            Ask: "What state management library do you want to use? (e.g., Redux, MobX, Zustand, None)"

        stylePaths (list): List of paths to style/example images.
            Format: List of strings (file paths or URLs)
            Example: ["styles/example.css", "https://example.com/style.css"]
            Default: []
            Ask: "What styles/examples do you want to use? Provide paths or URLs to images or example CSS."

    Returns:
        dict: A dictionary containing the prompt for the agent.
            Success: {"result": "prompt text"}
            Error: {"error": "error message"}
    """
    # Get current directory information if project name not provided
    if not projectName:
        projectName = os.path.basename(os.getcwd())

    # Validate required parameters
    if not widgetIntention:
        return {"error": "Widget intention is required"}

    # Set default values
    if techStack is None:
        techStack = []

    if stylePaths is None:
        stylePaths = []

    # Convert tech stack numbers to names
    tech_stack_names = []
    for tech in techStack:
        if tech == 1:
            tech_stack_names.append("CommonJS")
        elif tech == 2:
            tech_stack_names.append("React")
        elif tech == 3:
            tech_stack_names.append("Next.js")

    # Set default values if empty
    if not fileName:
        fileName = "(default)"

    if not scriptName:
        scriptName = "JS * fetch"

    if not fileMakerPath:
        fileMakerPath = "(use repo default)"

    # Format TypeScript status
    ts_status = "enabled" if useTypeScript else "disabled"

    # Process style paths to convert files to base64
    processed_styles = []
    for style_path in stylePaths:
        try:
            # Check if the path is a file that exists
            if os.path.isfile(style_path):
                # Read the file and convert to base64
                with open(style_path, "rb") as f:
                    file_content = f.read()
                    base64_content = base64.b64encode(file_content).decode("utf-8")
                processed_styles.append(f"<<{base64_content}>>")
            else:
                # If not a file or doesn't exist, keep the original path
                processed_styles.append(style_path)
        except Exception:
            # If there's an error, keep the original path
            processed_styles.append(style_path)

    # Generate the prompt
    prompt = f"""
## CONTEXT
This is a widget project named '{
        projectName
    }' that the user described in the following: "{widgetIntention}".
The widget is intended to be used in a FileMaker webviewer. The widget is being
developed in a JavaScript environment with the following specifications:
– FileMaker file: {fileName}
– Styles/examples: {", ".join(processed_styles) if processed_styles else "(none)"}
– Tech stack: {", ".join(tech_stack_names)}, TypeScript: {
        ts_status
    }, State management: {stateLibrary or "none"}.

/service/FileMakerService.js is a service that provides a method to execute FileMaker
scripts either synchronously or asynchronously based on the method parameter. This is
the widget's primary means of communicating with FileMaker. The service is designed to be
used in a JavaScript environment.

### Plain text example of the filemaker script JS * Fetch Data
```
# Purpose:   Backend filemaker service execution
# Context:   universal
# Change Log: @history 2024.Nov.14 marcus@claritybusinesssolutions.ca – created
# Uses:      FMGofer

Set Error Capture [ On ]

If [ IsEmpty ( Get ( ScriptParameter ) ) ]
    # — EXAMPLES
          # — UPDATE PARAMS (for testing in absence of ScriptParameter)
            {"action": "update",
              "version": "vLatest",
              "layout": "devTasks",
              "action": "update",
              "recordId": "9",
              "fieldData": {"f_completed": 1
                ...
              }
            }

          # — READ PARAMS (example)
            {"action": "read",
              "version": "vLatest",
              "layout": "devTasks",
              "action": "read",
              "query": [
                {"f_active": 1}
              ]
            }
          
          # — CREATE PARAMS (commented out)
            {"action": "ceate",
              "version": "vLatest",
              "layouts": "devTasks",
              "action": "create",
              "fieldData": [
                {"f_completed": 1},
                {"task": "pick up pills"}
                ...
              ]
            }
          # — DELETE PARAMS
            {"action": "delete",
              "version": "vLatest",
              "layouts": "devTasks",
              "recordId": "9"
            }
          # — RETURN CONTEXT PARAMS
            {"action": "returnContext"
            } 
Else
  
  Set Variable [ $payload ; Value: JSONGetElement ( Get ( ScriptParameter ) ; "parameter" ) ]
  
  If [ IsEmpty ( $payload ) ]
    # Proxy through FileMaker.PerformScript (FMGofer) when no payload
    Set Variable [ $payload ; Value: Get ( ScriptParameter ) ]
    Perform Script on Server with Callback [
      Specified: From list:     “JS * performSearch” ;
      Parameter:                $payload ;
      Callback script specified: From list: “JS * returnResult” ;
      Parameter:                Get ( ScriptResult ) ;
      State:                    Continue
    ]
    Exit Script [ Text Result:
      JSONSetElement (
        "" ;
        ["messages[0].message" ; "fetch sent for processing" ; JSONString] ;
        ["messages[0].code"    ; 0                     ; JSONNumber]
      )
    ]
  End If
  
End If


# — Grab callback info from FMGofer payload
Set Variable [ $callbackName ; Value: JSONGetElement ( Get ( ScriptParameter ) ; "callbackName" ) ]
Set Variable [ $promiseID    ; Value: JSONGetElement ( Get ( ScriptParameter ) ; "promiseID"    ) ]

# — Find the Web Viewer object on the current layout
Set Variable [ $webViewer ; Value:
  While (
    [ input     = LayoutObjectNames ( Get ( FileName ) ; Get ( LayoutName ) ) ;
      N         = ValueCount ( input ) ;
      theResult = "" ;
      X         = 1
    ] ;
    X ≤ N ;
    [
      thisResult = GetValue ( input ; X ) ;
      test       = PatternCount ( thisResult ; "WV" ) ;
      theResult  = If ( test ; List ( theResult ; thisResult ) ; theResult ) ;
      X          = X + 1
    ] ;
    theResult
  )
]


# — Validate that an “action” was passed
If [ IsEmpty ( JSONGetElement ( $payload ; "action" ) ) ]
  Set Variable [ $error ; Value: "action is required." ]
  Perform JavaScript in Web Viewer [
    Object Name:   $webViewer ;
    Function Name: $callbackName ;
    Parameters:    $promiseID ; $responseJSON ; $error
  ]
  Exit Script [ Text Result: "" ]
End If


# — Branch by action type
Set Variable [ $action ; Value: JSONGetElement ( $payload ; "action" ) ]
Set Variable [ $layout ; Value: JSONGetElement ( $payload ; "layout" ) ]

If [ $action = "read" ]
  
  Set Variable [ $query ; Value: JSONGetElement ( $payload ; "query" ) ]
  Set Variable [ $data  ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "query" ; $query ; JSONArray ]
        ;[ "dateformats" ; 1 ; JSONString ]
        ;[ "limit" ; 1000 ; JSONString ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "update" ]
  
  Set Variable [ $recordId  ; Value: JSONGetElement ( $payload ; "recordId"  ) ]
  Set Variable [ $fieldData ; Value: JSONGetElement ( $payload ; "fieldData" ) ]
  Set Variable [ $data      ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "recordId" ;$recordID; JSONString ]
        ;[ "fieldData" ; $fieldData ; JSONObject ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "create" ]
  
  Set Variable [ $fieldData ; Value: JSONGetElement ( $payload ; "fieldData" ) ]
  Set Variable [ $data      ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "fieldData" ; $fieldData ; JSONObject ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "delete" ]
  
  Set Variable [ $recordId ; Value: JSONGetElement ( $payload ; "recordId" ) ]
  Set Variable [ $data     ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "recordId" ; $recordId ; JSONString ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "returnContext" ]
  
  Set Variable [ $data         ; Value:
    GetTableDDL (
      JSONMakeArray (
        TableNames ( Get ( FileName ) ) ; "" ; JSONString ; ""
      )
    )
  ]
  Set Variable [ $responseJSON ; Value:
    JSONSetElement (
      "" ;
      ["userName" ; Get ( UserName ) ; JSONString] ;
      ["dbModel"  ; $data           ; JSONString]
    )
  ]
  
End If


# — Error handling
Set Variable [ $errorNum ; Value: Get ( LastError ) ]
If [ $errorNum ≠ 0 and $errorNum ≠ 401 ]
  Set Variable [ $error ; Value: ErrorText ( $errorNum ) ]
End If


# — Return result to the Web Viewer callback
Perform JavaScript in Web Viewer [
  Object Name:   $webViewer ;
  Function Name: $callbackName ;
  Parameters:    $promiseID ; $responseJSON ; $error
]
```

### Plain text example of the filemaker script JS * performSearch
```
# Purpose:   sync process to manage FileMaker backend calls
# Context:   universal
# Change Log: @history 2024.Nov.14 marcus@claritybusinesssolutions.ca – created

Set Error Capture [ On ]

If [ IsEmpty ( Get ( ScriptParameter ) ) ]
    # — EXAMPLES
          # — UPDATE PARAMS (for testing in absence of ScriptParameter)
            {"action": "update",
              "version": "vLatest",
              "layout": "devTasks",
              "action": "update",
              "recordId": "9",
              "fieldData": {"f_completed": 1
                ...
              }
            }

          # — READ PARAMS (example)
            {"action": "read",
              "version": "vLatest",
              "layout": "devTasks",
              "action": "read",
              "query": [
                {"f_active": 1}
              ]
            }
          
          # — CREATE PARAMS (commented out)
            {"action": "ceate",
              "version": "vLatest",
              "layouts": "devTasks",
              "action": "create",
              "fieldData": [
                {"f_completed": 1},
                {"task": "pick up pills"}
              ]
            }
          # — DELETE PARAMS
            {"action": "delete",
              "version": "vLatest",
              "layouts": "devTasks",
              "recordId": "9"
            }
          # — RETURN CONTEXT PARAMS
            {"action": "returnContext"
            } 
Else
  
  Set Variable [ $payload ; Value: Get ( ScriptParameter ) ]
  
End If


# — Locate the Web Viewer on the current layout
Set Variable [ $webViewer ; Value:
  While (
    [ input     = LayoutObjectNames ( Get ( FileName ) ; Get ( LayoutName ) ) ;
      N         = ValueCount ( input ) ;
      theResult = "" ;
      X         = 1
    ] ;
    X ≤ N ;
    [
      thisResult = GetValue ( input ; X ) ;
      theResult  = If ( PatternCount ( thisResult ; "WV" ) ; List ( theResult ; thisResult ) ; theResult ) ;
      X = X + 1
    ] ;
    theResult
  )
]


# — Dispatch by action
Set Variable [ $action ; Value: JSONGetElement ( $payload ; "action" ) ]
Set Variable [ $layout ; Value: JSONGetElement ( $payload ; "layout" ) ]

If [ $action = "read" ]
  
  Set Variable [ $query ; Value: JSONGetElement ( $payload ; "query" ) ]
  Set Variable [ $data  ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "query" ; $query ; JSONArray ]
        ;[ "dateformats" ; 1 ; JSONString ]
        ;[ "limit" ; 1000 ; JSONString ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "update" ]
  
  Set Variable [ $recordId  ; Value: JSONGetElement ( $payload ; "recordId"  ) ]
  Set Variable [ $fieldData ; Value: JSONGetElement ( $payload ; "fieldData" ) ]
  Set Variable [ $data      ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "recordId" ;$recordID; JSONString ]
        ;[ "fieldData" ; $fieldData ; JSONObject ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "create" ]
  
  Set Variable [ $fieldData ; Value: JSONGetElement ( $payload ; "fieldData" ) ]
  Set Variable [ $data      ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "fieldData" ; $fieldData ; JSONObject ]
    )
  ]
  Execute FileMaker Data API [ Select ; Target: $responseJSON ; $data ]
  
Else If [ $action = "returnContext" ]
  
  # Gather context info via ExecuteSQL
  Set Variable [ $userID    ; Value: /* ExecuteSQL("SELECT ...") */ ]
  Set Variable [ $teamIDs   ; Value: /* JSONMakeArray( ExecuteSQL("SELECT ...") ) */ ]
  Set Variable [ $responseJSON ; Value:
    JSONSetElement ( "" 
        ;[ "action" ;JSONGetElement($_payload;"action"); JSONString ] //read, metaData, create, update, delete, and duplicate
        ;[ "version" ;"vLatest"; JSONString ]
        ;[ "layouts" ;$layout; JSONString ]
        ;[ "recordId" ; $recordId ; JSONString ]
    )
  ]
  
End If


# — Return combined payload + response
Exit Script [ Text Result:
  JSONSetElement (
    $payload ;
    ["responseJSON" ; $responseJSON ; JSONObject]
  )
]
```

### Plain text example of the filemaker script JS * returnResult
```
# Purpose:   filemaker sync process callback
# Context:   universal
# Change Log: @history 2024.Nov.14 marcus@claritybusinesssolutions.ca – created

Set Error Capture [ On ]

If [ IsEmpty ( Get ( ScriptParameter ) ) ]
    Set Variable [ $payload ; Value: JSONGetElement ( Get ( ScriptResult ) ; "" ) ]
Else
    Set Variable [ $payload ; Value: JSONGetElement ( Get ( ScriptParameter ) ; "" ) ]
End If

Set Variable [ $callBackName     ; Value: JSONGetElement ( Get ( ScriptResult ) ; "callbackName" ) ]
Set Variable [ $callBackID       ; Value: JSONGetElement ( $payload ; "callbackID" ) ]
Set Variable [ $callBackFunction ; Value: JSONGetElement ( $payload ; "callbackFunction" ) ]
Set Variable [ $responseJSON     ; Value: JSONGetElement ( Get ( ScriptResult ) ; "responseJSON" ) ]

Set Variable [ $data ; Value:
  JSONSetElement (
    "" ;
    ["callbackId"       ; $callBackID       ; JSONString] ;
    ["callbackFunction" ; $callBackFunction ; JSONString] ;
    ["response"         ; JSONGetElement ( $responseJSON ; "response" ) ; JSONObject]
  )
]

Set Variable [ $webViewer ; Value:
  While (
    [ input     = LayoutObjectNames ( Get ( FileName ) ; Get ( LayoutName ) ) ;
      N         = ValueCount ( input ) ;
      theResult = "" ;
      X         = 1
    ] ;
    X ≤ N ;
    [
      thisResult = GetValue ( input ; X ) ;
      test       = PatternCount ( thisResult ; "WV" ) ;
      theResult  = If ( test ; List ( theResult ; thisResult ) ; theResult ) ;
      X          = X + 1
    ] ;
    theResult
  )
]

Perform JavaScript in Web Viewer [ 
  Object Name:   $webViewer ; 
  Function Name: $callBackName ; 
  Parameters:    $data 

```

### Plain text example of the filemaker script UploadToHTML
```
Set Variable [ $params     ; Value: Get ( ScriptParameter ) ]
Set Variable [ $path       ; Value: JSONGetElement ( $params ; "thePath" ) ]
Set Variable [ $widgetName ; Value: JSONGetElement ( $params ; "widgetName" ) ]

If [ IsEmpty ( $path ) ]
  Exit Script [ Text Result: "" ]
End If

If [ Get ( SystemPlatform ) = -2 ]
  Set Variable [ $Format ; Value: WinPath ]
Else
  Set Variable [ $Format ; Value: PosixPath ]
End If

Set Variable [ $path ; Value: ConvertToFileMakerPath ( $path ; $Format ) ]

New Window [ Style: Document ; Using layout: “HTML” (HTML) ]

Enter Find Mode [ Pause: Off ]
Set Field [ HTML::Name ; "==" & $widgetName ]
Perform Find []

If [ Get ( FoundCount ) = 0 ]
  New Record/Request
  Set Field [ HTML::Name ; $widgetName ]
  Set Variable [ $message ; Value: $widgetName & " has been added." ]
Else
  Set Variable [ $message ; Value: $widgetName & " has been updated." ]
End If

Open Data File [ $path ; Target: $fileId ]
Read from Data File [ File ID: $fileId ; Target: HTML::HTML ; Read as: UTF‑8 ]
Close Data File [ File ID: $fileId ]

Commit Records/Requests [ With dialog: On ]
Close Window [ Current Window ]

Show Custom Dialog [ “New version uploaded” ; $message ]

### Additional Information

Widgets do **not** typically include testing, but you may include it if you feel it
is necessary with permission. Setting up sample data so the widget can be tested in a browser is appreciated.
Simply trap for the absense of the FileMaker object to utilize sample data.

## IMPORTANT
The repo uses common JS file extensions. If you are using React or Next.js you must
convert the files to .jsx or .tsx respectively. You must also update the package.json
file to include the necessary dependencies and scripts for React or Next.js.

## TASKS
1) Complete the set up by updating 'widget.config.cjs'
module.exports = {{
  widgetName: "{projectName}" || "jsDev",
  server: "{fileMakerPath}" || "$",
  file: "{fileName}" || "jsDev",
  uploadScript: "{scriptName}" || "UploadToHTML",
}}

2) Then consider the user's intended purpose for the widget. If any aspect of its development remains unclear
you should ask the user for clarification. Document the steps and stages of development in the
/docs/development_tasks.md file. This file should include:
2.1. A description of the widget's intended purpose.
2.2. libraries and frameworks to install including FMGofer
2.3. Styles to implement referencing url/path provided by the user and instructions to create CSS files based on those image/examples
2.4. State management to implement (if any)
2.5. Services to create (if any)
2.6. Components to create
2.7. Pages to create, (if any)
2.8. Any other relevant information

3) You should then ask the user to paste 'GetTableDDL ( JSONMakeArray ( TableNames ( Get(FileName) ) ; "" ; JSONString ) ; "" )' into their
data view and provide you with the result. This will be used to create the widget's data model. The result should be placed in /docs/data_model.md
This data model can then be used with the FileMakerService to get the data from FileMaker.

With the user's permission you may proceed to develop the widget's intended features and functionality

When you are finished you should: 
1) remove unused example files and folders
2) run the project using 'npm start' and ensure everything works as expected.
3) open jsDev.fmp12 by running in terminal open and then the path to the file
4) provide the user with a summary of the development process and any
additional steps they need to take to complete the widget.

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
    - CSS must be as DRY as possible
    - CSS should comply with the example provided. If none is provided then implement a modern elegent consistent style
5. You must not use any non-standard FileMaker features or APIs.
"""

    # Create the prompt file in the project directory
    try:
        # If we're in a directory with the same name as the project, use the current directory
        # Otherwise, use the DEFAULT_WORKSPACE
        current_dir = os.getcwd()
        if projectName == os.path.basename(current_dir):
            project_dir = current_dir
        else:
            project_dir = os.path.join(DEFAULT_WORKSPACE, projectName)

        prompt_file_path = os.path.join(project_dir, "coding_prompts", "llm_prompt.md")

        # Ensure the directory exists
        os.makedirs(os.path.dirname(prompt_file_path), exist_ok=True)

        # Write the prompt to the file
        with open(prompt_file_path, "w") as f:
            f.write(f"# LLM Prompt\n{prompt}")

        return {
            "result": f"Prompt generated and saved to {prompt_file_path}",
            "prompt": prompt,
        }
    except Exception as e:
        return {"error": f"Failed to save prompt: {str(e)}", "prompt": prompt}


if __name__ == "__main__":
    mcp.run()
