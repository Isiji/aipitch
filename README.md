# Pitch Craft AI

## Overview
The **Pitch Craft AI** is a web application designed to help users create professional business pitches using AI. The application takes user input about their business and generates a compelling pitch, which can be downloaded as a PDF.

## Features
- **User-friendly web interface** for inputting business details.
- **AI-powered pitch generation** using the Gemini API.
- **PDF generation and download** functionality.
- **Logging** for debugging and monitoring.

---

## Project Structure
```
.vscode/
app.py
codealike.json
env/
    Include/
    Lib/
        site-packages/
    pyvenv.cfg
    Scripts/
        activate
        activate.bat
        Activate.ps1
        chardetect.exe
        deactivate.bat
        flask.exe
        normalizer.exe
        pip.exe
        pip3.12.exe
        pip3.exe
        pyrsa-decrypt.exe
        pyrsa-encrypt.exe
        pyrsa-keygen.exe
        pyrsa-priv2pub.exe
        pyrsa-sign.exe
        pyrsa-verify.exe
        python.exe
        pythonw.exe
        tqdm.exe
generated_pitches/
    EduSmart_AI_pitch.pdf
static/
    pitches/
        ...
    script.js
    styles.css
templates/
    index.html
```

---

## Installation
1. **Clone the repository:**  
   ```bash
   git clone <repository-url>
   cd ai-business-pitch-generator
   ```

2. **Set up a virtual environment:**  
   ```bash
   python -m venv env
   source env/bin/activate  # On macOS/Linux
   env\Scripts\activate  # On Windows
   ```

3. **Install dependencies:**  
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up the Gemini API key:**  
   Replace the placeholder API key in `app.py` with your actual Gemini API key:
   ```python
   genai.configure(api_key="YOUR_ACTUAL_API_KEY")
   ```

---

## Usage
1. **Run the application:**  
   ```bash
   python app.py
   ```

2. **Open your web browser** and navigate to:  
   ```
   http://127.0.0.1:5000/
   ```

3. **Fill out the form** with your business details and click **"Generate Pitch"**.
4. **Download the generated pitch** as a PDF.

---

## File Descriptions
### `app.py`
This is the main application file that:
- Sets up the Flask server.
- Handles routes.
- Integrates with the Gemini API to generate business pitches.

**Key functions and routes:**
- `index()`: Renders the main HTML page.
- `generate_pitch()`: Handles form submission, validates input, generates the pitch using the Gemini API, and creates a PDF.
- `create_pdf(text, filepath)`: Helper function to create a PDF from the generated pitch text.
- `download_pdf(filename)`: Endpoint to download the generated PDF.

### `templates/index.html`
This is the main HTML file providing the user interface for inputting business details and generating the pitch.

**Key elements:**
- Form fields for business name, industry, problem statement, target market, revenue model, and optional competitor analysis.
- Error alert and pitch result sections.
- JavaScript file inclusion for handling form submission and displaying results.

### `static/script.js`
Handles the form submission, displays error messages, and shows the generated pitch.

### `static/styles.css`
Contains styles for the HTML elements to ensure a user-friendly interface.

---

## Logging
The application uses Python's built-in `logging` module to log information and errors. Logs are configured to display at the `DEBUG` level for detailed output.

---

## Dependencies
- **Flask**: Web framework for Python.
- **google.generativeai**: SDK for interacting with the Gemini API.
- **reportlab**: Library for generating PDFs.

---

## Contributing
1. **Fork the repository.**
2. **Create a new branch:**  
   ```bash
   git checkout -b my-feature-branch
   ```
3. **Make your changes and commit them:**  
   ```bash
   git commit -m "Add some feature"
   ```
4. **Push to the branch:**  
   ```bash
   git push origin my-feature-branch
   ```
5. **Submit a pull request.**

---

## License
This project is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

---

## Acknowledgements
- **Flask**
- **ReportLab**
- **Google Gemini API**

---

