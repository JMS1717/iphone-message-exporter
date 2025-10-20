# iPhone Message Exporter

This project extracts your iPhone's SMS and iMessage data from a local backup and formats it for use with Large Language Models (LLMs).

The scripts are designed to be easy to run and the output is chunked into smaller files to fit within the context window of models like GPT-3 (e.g., 1M tokens) or for use in training your own AI models.

## Features

- Extracts all SMS and iMessage conversations.
- Groups messages by conversation.
- Sorts messages chronologically.
- Converts phone numbers to contact names.
- Chunks the output into manageable file sizes.
- Extracts a separate file of only your sent messages.
- Filters out common phrases and empty messages from the sent messages file.

## Prerequisites

- Python 3.x
- An unencrypted iPhone backup located on your computer.

## How to Use

1.  **Locate your iPhone backup directory.** The default location is:
    -   Windows: `C:\Users\<Your_Username>\Apple\MobileSync\Backup`
    -   macOS: `~/Library/Application Support/MobileSync/Backup/`

2.  **Run the script.** Open a command prompt or terminal and run the `run.bat` file (on Windows) or execute the python scripts directly.

    **Using `run.bat` on Windows:**

    Double-click on `run.bat` and follow the on-screen prompts. You will be asked to enter the path to your iPhone backup directory.

    **Running the Python scripts directly:**

    ```bash
    # To extract all messages
    python extract_sms.py "C:\path\to\your\backup"

    # To extract only sent messages
    python extract_sent_texts.py "C:\path\to\your\backup"
    ```

3.  **Find your extracted messages.** The scripts will create new directories (`text_messages` and `sent_texts`) in the same folder as the scripts, containing your extracted messages.

## For LLMs

The output files are formatted and chunked to be easily used with LLMs. The `text_messages` are split into files of approximately 3.5 million characters, and the `sent_texts` are split into files of 750 thousand characters. This allows you to easily copy and paste the content into an LLM prompt or use the files for training.
