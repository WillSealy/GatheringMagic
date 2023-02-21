import requests
import cv2
import pytesseract
from PIL import Image
import time

# API endpoint to update working memory
WORKING_MEMORY_ENDPOINT = "https://example.com/update_working_memory"

# Scryfall API endpoint to query card information
SCRYFALL_API_ENDPOINT = "https://api.scryfall.com/cards/search"

# Function to query Scryfall API for card information
def get_card_info(card_title):
    params = {'q': '!"{}"'.format(card_title)} # Format query string to search for exact card title
    response = requests.get(SCRYFALL_API_ENDPOINT, params=params)
    if response.status_code == 200:
        data = response.json()
        if data['total_cards'] > 0:
            return data['data'][0] # Return first matching card
    return None

# Function to update working memory
def update_working_memory(working_memory):
    response = requests.post(WORKING_MEMORY_ENDPOINT, json=working_memory)
    if response.status_code != 200:
        print("Error updating working memory: ", response.text)

# Load image from file and convert to grayscale
img = cv2.imread("card_image.jpg")
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

# Apply threshold to remove noise and improve text recognition
thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

# Perform text recognition using Tesseract OCR engine
card_titles = pytesseract.image_to_string(Image.fromarray(thresh), lang='eng', config='--psm 6')

# Split card titles by newline character and remove leading/trailing whitespace
card_titles = [title.strip() for title in card_titles.split('\n')]

# Initialize working memory and tapped variable for each card
working_memory = {}
for title in card_titles:
    working_memory[title] = {'card_info': None, 'tapped': False}

# Continuously update working memory while player_turn is True
player_turn = True
while player_turn:
    for title in list(working_memory.keys()):
        # Check if card title is still visible in camera feed
        if title not in card_titles:
            del working_memory[title]
            continue
        
        # Check if card title is oriented vertically
        if 'VERTICAL' in pytesseract.image_to_osd(Image.fromarray(thresh), lang='eng'):
            working_memory[title]['tapped'] = True
        else:
            working_memory[title]['tapped'] = False
        
        # Query Scryfall API for card information
        if working_memory[title]['card_info'] is None:
            card_info = get_card_info(title)
            if card_info is not None:
                working_memory[title]['card_info'] = card_info
        
        # Update working memory through API once per second
        if time.time() - working_memory[title].get('last_updated', 0) > 1:
            update_working_memory({title: working_memory[title]})
            working_memory[title]['last_updated'] = time.time()
