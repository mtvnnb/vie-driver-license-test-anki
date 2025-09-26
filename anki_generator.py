import json
import csv
import os
import re
import logging

class AnkiDeckGenerator:
    """
    Generates an Anki-compatible CSV file from scraped quiz data in JSON format.
    """
    def __init__(self, input_json_path, output_csv_path, image_base_dir):
        self.input_path = input_json_path
        self.output_path = output_csv_path
        self.image_dir = image_base_dir
        self.quiz_data = self._load_json()

    def _load_json(self):
        """Loads quiz data from the input JSON file."""
        try:
            with open(self.input_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            logging.info(f"Successfully loaded {len(data)} questions from {self.input_path}")
            return data
        except FileNotFoundError:
            logging.error(f"JSON file not found at {self.input_path}.")
            raise
        except json.JSONDecodeError:
            logging.error(f"Could not decode JSON from {self.input_path}. Check file integrity.")
            raise

    def _format_front(self, q_data):
        """Formats the front of the Anki card (Question)."""
        question_text = q_data.get('question_text', f"Question {q_data.get('question_number', 'N/A')}")
        image_path = q_data.get('image_local_path')
        all_options = q_data.get('all_answer_options_text', [])

        parts = [question_text]

        if image_path and os.path.exists(image_path):
            image_filename = os.path.basename(image_path)
            parts.append(f'<br><img src="{image_filename}">')
        elif image_path:
            logging.warning(f"Image file not found at {image_path} for Q{q_data.get('question_number')}. Skipping.")

        if all_options:
            parts.append("<br><br><b>Options:</b>")
            formatted_options = []
            for idx, option in enumerate(all_options):
                cleaned_option = re.sub(r'^\d+\.\s*', '', option.replace('✔️', '').strip())
                formatted_options.append(f"{idx + 1}. {cleaned_option}")
            parts.append("<br>".join(formatted_options))
        
        return "<br>".join(parts)

    def _format_back(self, q_data):
        """Formats the back of the Anki card (Answer)."""
        correct_answer = q_data.get('correct_answer_text', '')
        explanation = q_data.get('explanation', '')

        parts = []
        if correct_answer:
            # Clean the checkmark from the correct answer text itself
            cleaned_answer = correct_answer.replace('✔️', '').strip()
            parts.append(f"<b>Correct Answer:</b> {cleaned_answer}")
        
        if explanation:
            if parts: parts.append("<br>")
            parts.append(f"<b>Explanation:</b> {explanation}")
        
        if not parts:
            return "No correct answer or explanation found."
            
        return "<br>".join(parts)

    def generate_csv(self):
        """Creates and writes the Anki-compatible CSV file."""
        if not self.quiz_data:
            logging.error("No quiz data loaded. Aborting CSV generation.")
            return

        csv_rows = [["Front (Question)", "Back (Answer & Explanation)"]]
        for q_data in self.quiz_data:
            front = self._format_front(q_data)
            back = self._format_back(q_data)
            csv_rows.append([front, back])

        try:
            with open(self.output_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile, delimiter=';', quotechar='"', quoting=csv.QUOTE_MINIMAL)
                writer.writerows(csv_rows)
            logging.info(f"Anki CSV deck successfully created at {self.output_path}")
            self._print_instructions()
        except IOError as e:
            logging.error(f"An error occurred while writing the CSV file: {e}")

    def _print_instructions(self):
        """Prints next steps for the user to import the deck into Anki."""
        instructions = f"""
--- Next Steps for Anki Import ---
1. Open Anki.
2. Go to File -> Import.
3. Select the file: '{self.output_path}'.
4. In the Anki Import window:
   - Note Type: 'Basic'
   - Fields separated by: '; Semicolon'
   - CHECK 'Allow HTML in fields'
5. Copy all images from the '{self.image_dir}' folder into your Anki media folder.
   (In Anki: Tools -> Add-ons -> Open Add-ons Folder -> go up one level to 'Anki2' -> open 'collection.media')
6. Click 'Import'.
"""
        print(instructions)
