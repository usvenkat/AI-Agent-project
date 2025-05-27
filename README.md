# AI-AGENT-Project


---

# Topic Search & Image Viewer GUI

## 💡 Overview

This Python application provides a graphical user interface (GUI) to search for information and display relevant images based on a user-provided topic. It combines web scraping for textual content with a robust API integration for image search, all presented in an intuitive Tkinter window.

## ✨ Features

* **Topic-Based Search:** Enter any topic to get summarized textual information.
* **Image Retrieval & Display:** Searches for and displays the top relevant images for the given topic directly within the GUI.
* **Image Navigation:** Easily browse through multiple found images using "Previous" and "Next" buttons.
* **Intuitive GUI:** Built with Tkinter for a straightforward user experience.
* **API-Powered Image Search:** Leverages the Google Custom Search API for reliable image search results.
* **Textual Information Scraping:** Extracts important points from general web search results using `requests` and `BeautifulSoup`.
* **Responsive Design:** Images are resized to fit the display area, maintaining aspect ratio.

## 🛠️ Technologies Used

* **Python 3.x:** The core programming language.
* **Tkinter:** Python's built-in GUI toolkit for creating the user interface.
* **Pillow (PIL Fork):** For image processing, including loading, resizing, and displaying images in the GUI.
* **Google Custom Search API (API Key & CSE ID):** For programmatic access to Google's image search results.
* **`google-api-python-client`:** Python client library for interacting with Google APIs.
* **`requests`:** For making HTTP requests to download web page content and image data.
* **`BeautifulSoup4`:** For parsing HTML content and extracting textual information.
* **`googlesearch-python`:** A simple library to perform basic Google web searches for text content.

## 🚀 Setup and Installation

Follow these steps to get the application up and running on your local machine.

### Prerequisites

* Python 3.7 or higher installed on your system.
* An active internet connection.

### 1. Clone the Repository

First, clone this repository to your local machine:

```bash
git clone https://github.com/Vathsav56/AI-AGENT-Project.git
cd AI_AGENT_PROJECT
```

(Remember to replace `Vathsav` and `AI_AGENT_SEARCH` with your actual GitHub details.)

### 2. Install Dependencies

Install all required Python libraries using pip:

```bash
pip install google-api-python-client requests beautifulsoup4 googlesearch-python Pillow
```

### 3. Google Custom Search API Configuration (Crucial!)

To enable image search, you need to set up a Google Cloud Project, enable the Custom Search API, create a Custom Search Engine, and obtain an API Key and a Search Engine ID (`cx`).

Follow these detailed steps carefully:

#### a. Create/Select a Google Cloud Project:
   * Go to the [Google Cloud Console](https://console.cloud.google.com/).
   * Create a new project or select an existing one.

#### b. Enable the Custom Search API:
   * In the Google Cloud Console, navigate to `APIs & Services` > `Library`.
   * Search for "Custom Search API" and enable it for your project.

#### c. Get Your API Key:
   * In the Google Cloud Console, go to `APIs & Services` > `Credentials`.
   * Click "Create Credentials" > "API Key."
   * **Copy this API Key.** This will be your `GOOGLE_API_KEY`. **Keep it secure!**

#### d. Create/Configure Your Custom Search Engine (CSE):
   * Go to the [Google Programmable Search Engine control panel](https://programmablesearchengine.google.com/controlpanel/all).
   * Click "Add new search engine."
   * **In "Sites to search":** Enter `*` (an asterisk) to search the entire web for images, or specify particular domains (e.g., `wikipedia.org`).
   * Give your search engine a name (e.g., "My GUI Image Search").
   * Click "Create."
   * **Crucial Step: Enable Image Search!**
     * After creation, click on your new search engine in the list.
     * In the left-hand menu, go to **"Search features."**
     * Scroll down to the **"Image search"** section and ensure the toggle is **ON**.
   * **Get Your Search Engine ID (cx):**
     * In the left-hand menu, go to **"Overview."**
     * You will see your **"Search engine ID" (cx)** listed there. **Copy this ID.** This will be your `GOOGLE_CSE_ID`.

### 4. Update the Python Code

Open the main Python script (`your_script_name.py` - assuming you saved it) and replace the placeholder values with your actual API Key and Custom Search Engine ID:

```python
# --- Configuration: REPLACE THESE WITH YOUR ACTUAL KEYS ---
GOOGLE_API_KEY = "YOUR_GOOGLE_API_KEY_HERE" # Paste your API Key here
GOOGLE_CSE_ID = "YOUR_CUSTOM_SEARCH_ENGINE_ID_HERE" # Paste your CSE ID (cx) here
```

## 🚀 Usage

To run the application, simply execute the Python script:

```bash
python your_script_name.py
```

1.  A GUI window will appear.
2.  Enter the topic you want to search for in the input field.
3.  Click the "Search" button or press `Enter`.
4.  The application will display important textual points on the left and relevant images on the right.
5.  Use the "< Prev" and "Next >" buttons to navigate through the found images.


## 💡 Future Enhancements

* **Error Handling Improvements:** More specific error messages for different network or API issues.
* **Loading Indicators:** Show a "Loading..." or progress bar while searching.
* **Image Saving:** Add an option to save displayed images.
* **Customizable Image Count:** Allow users to specify how many images to fetch.
* **Advanced Text Summarization:** Implement more sophisticated text summarization techniques.
* **Better UI Layout:** Refine the Tkinter layout for more complex content or larger displays
