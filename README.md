# Google Takeout Mbox Parser

A simple, powerful Python script to extract emails from a Google Takeout `.mbox` file. 
It organizes emails into folders by **Sender**, extracts **attachments** into corresponding subdirectories, and creates readable text files for each message.

## Features
- **Organized Output**: Creates a folder for each Sender.
- **Attachment Support**: Extracts attachments to `Sender/attachments/` and links them in the email text file.
- **Readable Format**: Converts emails to clean text files with metadata (Subject, From, Date).
- **Sanitization**: Handles encoded headers and messy filenames automatically.

## Usage

1. **Prerequisites**
   - Python 3.x
   - No external dependencies required (uses standard library `mailbox`, `email`).

2. **Run the Script**
   ```bash
   python extract_emails.py "path/to/your.mbox"
   ```
   This will create a `output/` directory by default.

3. **Options**
   - `--out [directory]`: Specify a custom output directory.
   - `--limit [number]`: Extract only the first N emails (useful for testing).
   - `--keyword [word]`: Filter emails by keyword in Subject or From.

   **Example:**
   ```bash
   python extract_emails.py "Mydata.mbox" --out "MyEmails" --limit 100
   ```

## Output Structure
```
output/
  Amazon.com/
    001_Order_Confimation.txt
    attachments/
      0001/
        invoice.pdf
  Google/
    002_Security_Alert.txt
```

## License
MIT
