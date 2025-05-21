# Folder Tree Viewer

A Python GUI application that displays the structure of a selected folder in multiple formats, including Raw, Plaintext, Markdown, JSON, CSV, HTML, and XML.

## Features

- Visual folder selection via GUI.
- Outputs folder structure in various formats:
  - Raw (list of paths)
  - Plaintext (ASCII tree view)
  - Markdown (nested bullet points)
  - JSON (nested dictionary)
  - CSV (newline-separated paths)
  - HTML (unordered list)
  - XML (structured tags)
- Real-time auto-refresh when folder content changes.
- Tooltips for guidance.
- Copy output to clipboard.
- Save output to file.

## Requirements

- Python 3.x
- Built-in libraries only: `tkinter`, `os`, `json`, `hashlib`

## How to Use

1. Run the script:
    ```bash
    python folder_tree_viewer.py
    ```
2. Click "Select Folder" to choose a directory.
3. Choose an output format from the options.
4. View the folder structure in the text area.
5. Use:
   - "Copy to Clipboard" to copy the output.
   - "Save to File" to export the output as a `.txt` file.

## Output Formats

| Format     | Description                         |
|------------|-------------------------------------|
| Raw        | List of all file and folder paths   |
| Plaintext  | ASCII-style tree layout             |
| Markdown   | Markdown nested list                |
| JSON       | JSON object with nested folders     |
| CSV        | Comma-separated values (newline)    |
| HTML       | HTML unordered list of structure    |
| XML        | XML-style tagged folder/file tree   |

## Notes

- The tree auto-refreshes every 5 seconds if changes are detected.
- The script uses file modification time and size to detect changes.
- Tooltips offer brief descriptions of buttons and options.
