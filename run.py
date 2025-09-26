import argparse
import logging
import os
import json
from config import QUIZ_URL, JSON_OUTPUT_PATH, CSV_OUTPUT_PATH, IMAGE_DIR
from scraper import QuizScraper
from anki_generator import AnkiDeckGenerator

# --- Setup Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("run.log"),
        logging.StreamHandler()
    ]
)

def run_scraper(url, output_path, image_dir):
    """Runs the quiz data scraper and saves the data to a JSON file."""
    logging.info(f"Starting scraper for URL: {url}")
    scraper = QuizScraper(url, image_dir)
    try:
        extracted_data = scraper.scrape_all_questions()
        if not extracted_data:
            logging.warning("Scraper finished but no data was extracted.")
            return

        logging.info(f"Successfully extracted data for {len(extracted_data)} questions.")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(extracted_data, f, ensure_ascii=False, indent=4)
        logging.info(f"Data successfully saved to {output_path}")

    except Exception as e:
        logging.critical(f"A critical error occurred during scraping: {e}", exc_info=True)
    finally:
        scraper.close()
        logging.info("Scraper resources have been cleaned up.")

def run_generator(input_path, output_path, image_dir):
    """Runs the Anki deck generator from a JSON file."""
    if not os.path.exists(input_path):
        logging.error(f"Input file not found: {input_path}. Cannot generate Anki deck.")
        logging.error("Please run the scraper first using '--step scrape' or '--step all'.")
        return

    logging.info(f"Starting Anki deck generation from {input_path}")
    generator = AnkiDeckGenerator(input_path, output_path, image_dir)
    try:
        generator.generate_csv()
    except Exception as e:
        logging.critical(f"A critical error occurred during Anki deck generation: {e}", exc_info=True)

def main():
    """Main function to parse arguments and run selected steps."""
    parser = argparse.ArgumentParser(description="Scrape quiz data and generate an Anki deck.")
    parser.add_argument(
        '--step',
        choices=['scrape', 'generate', 'all'],
        default='all',
        help="Specify which step to run: 'scrape' data, 'generate' Anki deck, or 'all' (default)."
    )
    args = parser.parse_args()

    if args.step in ['scrape', 'all']:
        run_scraper(QUIZ_URL, JSON_OUTPUT_PATH, IMAGE_DIR)

    if args.step in ['generate', 'all']:
        run_generator(JSON_OUTPUT_PATH, CSV_OUTPUT_PATH, IMAGE_DIR)

if __name__ == "__main__":
    main()
