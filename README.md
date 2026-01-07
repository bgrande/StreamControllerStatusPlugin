# Status Plugin for StreamController

The **Status Plugin** for StreamController allows you to monitor the status of websites, APIs, or local scripts directly from your Stream Deck. Based on the result of these checks, you can dynamically change the button's appearance, including background color, text color, label, and image.

## Features
- **Web & API Monitoring**: Check HTTP status codes or response content from any URL.
- **Local Script Execution**: Run local scripts or commands and react to their output or exit status.
- **Advanced Matching**: Use various modes to evaluate results:
    - **Status Code**: Match against HTTP response codes (e.g., 200).
    - **Contains**: Check if the result contains a specific string.
    - **Equals**: Check for an exact string match.
    - **Success**: Match based on whether the request or script succeeded (boolean).
    - **Regex**: Use regular expressions for complex matching logic.
- **Dynamic UI Updates**: Define separate behaviors for "Match" and "No Match" states:
    - Background Color
    - Text Color
    - Label Text
    - (tbd. Background Image)
- **Periodic or Manual Checks**: Configure checks to run automatically at set intervals or manually on button press.
- **Asynchronous Execution**: Checks run in the background to keep the UI responsive.

## Configuration
Add the **Status Checker** action to a button and configure the following settings:

### Check Settings
- **Target Type**: Choose between `web` or `local`.
- **Target**: Enter the URL (for API/Website) or the full path/command (for Local Script).
- **Header**: JSON (key/value) formatted string containing HTTP headers to send with the request.
- **Auto Interval (seconds)**: Set how often the periodic check should run.

### Match Settings
- **Result Handling Type**: Select how the result should be evaluated (`Status Code`, `Contains`, `Equals`, `Success`, `Regex`).
- **Expected Value**: The value to compare the result against.

### Behavior Settings (Match & No Match)
Expand these sections to define how the button should look when the condition is met (Match) or not met (No Match):
- **Success Background Color**: The button's background when the match was positive.
- **Error Background Color**: The button's background when the match was negative.
- **Success Text Color**: The color of the label text when the match was positive.
- **Error Text Color**: The color of the label text when the match was negative.

### Default Behavior
- **Label Text**
  - the label text will either be Error or OK depending on the match result and if there was a recognized result like:
    - empty string
    - true|false
    - no result
    - 1|0
  - otherwise the return text will be shown capped at 30 characters 

## Usage
1. Install the plugin into StreamController.
2. Drag the **Status Checker** action onto a button.
3. Configure your target (e.g., `https://api.github.com`).
4. Set the **Result Handling Type** to `Status Code` and **Expected Value** to `200`.
5. Customize the **Match Behavior** (e.g., Green background, "OK" label) and **No Match Behavior** (e.g., Red background, "ERROR" label).
6. The button will now update its state based on the API response!

## License
This plugin is developed for use with [StreamController](https://github.com/StreamController/StreamController).

---
*Initial draft by Junie.*
