# Vietnam Driver License Test Anki Generator

This project scrapes the 600 theoretical questions for the Vietnamese driver's license test from a public website and formats them into an Anki-compatible CSV file for easy studying.

## Features

- **Scrapes all 600 questions**: Extracts question text, all answer options, the correct answer, and any associated images.
- **Generates Anki-compatible CSV**: Creates a CSV file ready for direct import into Anki.
- **Handles Images**: Downloads images and links them correctly in the Anki cards.
- **Modular and Robust**: Refactored for better organization, error handling, and logging.
- **Command-Line Interface**: Allows running the scraper and generator separately or together.

## Setup and Usage

This project uses `uv` for fast dependency management.

### 1. Initial Setup

First, install `uv` if you haven't already:

```bash
pip install uv
```

Next, create a virtual environment and install the required packages:

```bash
# Create a virtual environment
uv venv

# Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# Install dependencies
uv pip install -r requirements.txt
```

### 2. Running the Script

The main entry point is `run.py`. You can choose to run the full process (scrape and generate) or individual steps.

**To run the entire process (recommended for first use):**

```bash
python run.py --step all
```

This will:
1. Scrape the data from the website and save it to `quiz_data.json`.
2. Download all question images into the `quiz_images/` directory.
3. Generate the Anki deck `anki_quiz_deck.csv`.

**To only scrape the data:**

```bash
python run.py --step scrape
```

**To only generate the CSV from existing `quiz_data.json`:**

```bash
python run.py --step generate
```

A log file `run.log` will be created to record the process.

### 3. How to Import into Anki

1. **Open Anki** on your desktop.
2. Go to **File -> Import...** and select the generated `anki_quiz_deck.csv` file.
3. In the Anki Import window, ensure the settings are correct:
    - **Note Type**: `Basic`
    - **Deck**: Choose the deck you want to add the cards to (or create a new one).
    - **Fields separated by**: `Semicolon`
    - **IMPORTANT**: Make sure **"Allow HTML in fields"** is **checked**.
    - The field mapping should be `Front (Question)` -> `Front` and `Back (Answer & Explanation)` -> `Back`.
4. Click **Import**.
5. **Copy Media**:
    - Open the `quiz_images` folder created by the script.
    - In Anki, go to **Tools -> Add-ons**. Click "View Files" on any add-on to open the `addons21` folder.
    - Go up one directory level to your `Anki2` profile folder (e.g., `User 1`).
    - Open the `collection.media` folder.
    - Copy all the images from the `quiz_images` folder and paste them into the `collection.media` folder.

Your deck is now ready for studying!
