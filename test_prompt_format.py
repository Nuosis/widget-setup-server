#!/usr/bin/env python3
import os

from widget_setup_server import get_prompt


def test_get_prompt():
    # Set up test environment
    os.environ["PROJECT_DIR"] = os.getcwd()

    # Test with minimal required parameters
    result = get_prompt(
        widgetIntention="Create a date picker widget that allows users to select a date from a calendar interface. The widget will display a calendar with month/year navigation, highlight the current date, and allow selection of dates. It will integrate with FileMaker to pass the selected date back to the database.",
        fileName="DatePicker.fmp12",
        fileMakerPath="fmp://$/DatePicker",
        scriptName="UploadToHTML",
        techStack=[2],
        useTypeScript=True,
        stateLibrary="None",
        stylePaths=[],
    )

    if isinstance(result, dict) and "error" in result:
        print("Error:", result["error"])
    else:
        print("Success!")
        print(result)


if __name__ == "__main__":
    test_get_prompt()
