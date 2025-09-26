import time
import requests
import os
import logging
from urllib.parse import urljoin

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException

from config import TOTAL_QUESTIONS, SELENIUM_WAIT_TIMEOUT, SELENIUM_POLL_FREQUENCY

class QuizScraper:
    """
    A class to scrape quiz data from a given URL.
    It extracts questions, answers, explanations, and downloads associated images.
    """
    def __init__(self, url, image_dir):
        self.url = url
        self.image_dir = image_dir
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()))
        self.driver.maximize_window()
        os.makedirs(self.image_dir, exist_ok=True)
        logging.info(f"Image download directory: '{self.image_dir}' ensured.")

    def _get_element_text(self, by, value, default=""):
        """Safely gets text from an element."""
        try:
            return self.driver.find_element(by, value).text.strip()
        except NoSuchElementException:
            return default

    def _download_image(self, question_number):
        """Finds and downloads an image for the current question."""
        try:
            image_element = self.driver.find_element(By.CLASS_NAME, "question-image-huy")
            raw_src = image_element.get_attribute('src')
            if not raw_src:
                logging.warning(f"Q{question_number}: Image element found but 'src' is empty.")
                return None

            full_url = urljoin(self.url, raw_src)
            image_filename = os.path.basename(full_url)
            image_path = os.path.join(self.image_dir, f"q{question_number}_{image_filename}")

            response = requests.get(full_url, stream=True, timeout=10)
            response.raise_for_status()

            with open(image_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logging.info(f"Q{question_number}: Image downloaded to {image_path}")
            return image_path

        except NoSuchElementException:
            logging.info(f"Q{question_number}: No image found.")
            return None
        except requests.exceptions.RequestException as e:
            logging.error(f"Q{question_number}: Failed to download image from {full_url}. Error: {e}")
            return None
        except Exception as e:
            logging.error(f"Q{question_number}: An unexpected error occurred during image download: {e}")
            return None

    def _reveal_and_extract_answers(self, question_number):
        """
        Clicks through answer options to reveal the correct answer and explanation,
        then extracts all relevant answer and explanation text.
        """
        data = {
            'correct_answer_text': None,
            'incorrect_answer_texts': [],
            'all_answer_options_text': [],
            'explanation': None
        }
        try:
            answer_container = WebDriverWait(self.driver, SELENIUM_WAIT_TIMEOUT, SELENIUM_POLL_FREQUENCY).until(
                EC.presence_of_element_located((By.ID, "cautraloiquiz"))
            )
            answer_labels = answer_container.find_elements(By.TAG_NAME, "label")

            # Click each answer to ensure the correct one is revealed
            for i in range(len(answer_labels)):
                try:
                    # Re-find element to avoid staleness
                    label = WebDriverWait(self.driver, 1).until(
                        EC.element_to_be_clickable((By.XPATH, f'//*[@id="cautraloiquiz"]/label[{i + 1}]'))
                    )
                    label.click()
                    # Check if the correct answer has been revealed to stop early
                    if self.driver.find_elements(By.CSS_SELECTOR, ".answer-huy.correct-huy"):
                        logging.info(f"Q{question_number}: Correct answer revealed after clicking option {i+1}.")
                        break
                except (TimeoutException, StaleElementReferenceException):
                    logging.warning(f"Q{question_number}: Could not click answer option {i+1}. It might be stale or non-interactive.")
                    continue
            
            # Final extraction after all clicks
            data['correct_answer_text'] = self._get_element_text(By.CSS_SELECTOR, ".answer-huy.correct-huy")
            all_answers = self.driver.find_elements(By.CLASS_NAME, "answer-huy")
            data['all_answer_options_text'] = [el.text.strip() for el in all_answers if el.text.strip()]
            
            incorrect_answers = self.driver.find_elements(By.CLASS_NAME, "incorrect-huy")
            data['incorrect_answer_texts'] = [el.text.strip() for el in incorrect_answers if el.text.strip()]
            
            explanation_elements = self.driver.find_elements(By.CLASS_NAME, "explanation-text")
            data['explanation'] = " ".join([el.text.strip() for el in explanation_elements if el.text.strip()])

        except TimeoutException:
            logging.error(f"Q{question_number}: Timed out waiting for the answer container.")
        except Exception as e:
            logging.error(f"Q{question_number}: An error occurred revealing/extracting answers: {e}")
        
        return data

    def scrape_question(self, question_number):
        """Scrapes a single question by its number."""
        logging.info(f"Processing question {question_number}...")
        question_data = {'question_number': question_number}

        try:
            # Navigate to the question
            question_anchor = WebDriverWait(self.driver, SELENIUM_WAIT_TIMEOUT).until(
                EC.element_to_be_clickable((By.XPATH, f'//*[@id="cau{question_number}"]'))
            )
            question_anchor.click()
            time.sleep(SELENIUM_POLL_FREQUENCY) # Small pause for JS to render

            # Extract question text
            question_data['question_text'] = self._get_element_text(By.XPATH, '//*[@id="cauhoiquiz"]/h3', f'Question {question_number}')
            
            # Download image
            question_data['image_local_path'] = self._download_image(question_number)

            # Get answers and explanation
            answer_data = self._reveal_and_extract_answers(question_number)
            question_data.update(answer_data)

            return question_data

        except TimeoutException:
            logging.error(f"Timeout waiting for question anchor for Q{question_number}. Skipping.")
        except Exception as e:
            logging.error(f"An unexpected error occurred for Q{question_number}: {e}. Skipping.")
        
        return None

    def scrape_all_questions(self):
        """Iterates through all questions and scrapes their data."""
        all_quiz_data = []
        self.driver.get(self.url)
        logging.info(f"Navigating to {self.url}")
        try:
            WebDriverWait(self.driver, SELENIUM_WAIT_TIMEOUT).until(
                EC.presence_of_element_located((By.CLASS_NAME, "answer-huy"))
            )
            logging.info("Page loaded successfully.")
        except TimeoutException:
            logging.critical("Failed to load the main quiz page. Aborting.")
            return []

        for i in range(1, TOTAL_QUESTIONS + 1):
            data = self.scrape_question(i)
            if data:
                all_quiz_data.append(data)
        
        return all_quiz_data

    def close(self):
        """Closes the WebDriver."""
        if self.driver:
            self.driver.quit()
