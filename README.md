# Agentverse Sample Projects

A collection of sample projects demonstrating the capabilities of the Agentverse platform for building autonomous agents. These projects serve as examples and starting points for developers and content creators interested in building with Agentverse.

## Overview

This repository contains a sample project that showcases a multi-agent system for content translation, image generation, and social media scheduling using the Agentverse platform. The project demonstrates how to extract text from images, translate it into multiple languages, generate new images with translated text, and schedule posts across social media platforms, providing a foundation for automated multilingual content creation.

## Sample Projects

### 1. Content Translator Agent

**Track**: Creator Economy

A multi-agent system that automates the process of extracting text from images, translating it into multiple languages, generating new images with translated text, and scheduling social media posts on platforms like Instagram and Twitter. It includes a specialized agent for generating quote-based images with translated text.

**Key Features**:
- Multi-agent architecture for text extraction, translation, and post scheduling
- Text extraction from images using Tesseract OCR
- Translation into multiple languages (English, Spanish, French, etc.) using Google Translate and ASI1 LLM API
- Image generation with translated quotes using Pollinations API
- Support for complex scripts like Hindi and Arabic with proper font handling
- Automated post scheduling with time zone support

[View Project →](./content-translator)

## Getting Started

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Git
- Tesseract OCR installed (with `tessdata` for language support)
- API keys for Google Translate, ASI1 LLM, and Pollinations (optional for image generation)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/content-translator-agent.git
   cd content-translator-agent
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   Ensure you have the required packages: `pytesseract`, `googletrans`, `pillow`, `uagents`, `arabic-reshaper`, `python-bidi`, etc.

3. Set up environment variables by copying the `.env.template` to `.env` and filling in your API keys:
   ```bash
   cp .env.template .env
   ```
   Required keys:
   - `AGENT_SEED`, `AGENT_PORT`, `CONTENT_TRANSLATOR_ADDRESS`: For agent configuration
   - `CLIENT_SEED`, `CLIENT_PORT`: For client configuration
   - `ASI1_LLM_API_KEY`: For translation via ASI1 LLM API
   - `HINDI_FONT_URL`, `ARABIC_FONT_URL`: URLs for Noto fonts (Hindi and Arabic)

4. Configure Tesseract OCR:
   - Set the `TESSDATA_PREFIX` environment variable to the path of your Tesseract `tessdata` directory.
   - Update `pytesseract.pytesseract.tesseract_cmd` to the path of your Tesseract executable in `Image_processor.py`.

5. Run the agents:
   - Start the Content Translator Agent: `python content_translator.py`
   - Start the Client Agent: `python client.py`
   - Optionally, start the Image Quote Agent: `python image_quote_agent.py`

## Project Structure

The project follows a modular structure:

```
content-translator/
├── README.md                 # Project documentation
├── .env.template             # Template for environment variables
├── requirements.txt          # Dependencies
├── client.py                 # Client agent for sending requests
├── content_translator.py     # Main agent for processing images and scheduling posts
├── Image_processor.py        # Handles text extraction, translation, and image generation
├── image_quote_agent.py      # Specialized agent for generating quote-based images
├── models.py                 # Data models and enums for the system
├── scheduler.py              # Post scheduling logic with time zone support
└── [generated files]         # Output images (e.g., canvas_*.png, output_with_text_*.png)
```

## Extending the Project

This sample project is designed to be a starting point. Here are some ways you can extend it:

1. **Add Support for More Languages**: Expand the `Language` enum and Tesseract language mappings in `models.py` to support additional languages.
2. **Integrate with More Platforms**: Add support for other social media platforms (e.g., LinkedIn) in the `Platform` enum and `scheduler.py`.
3. **Enhance Image Generation**: Incorporate more advanced image generation models or allow for custom image styles in `image_quote_agent.py`.
4. **Improve Translation Accuracy**: Use alternative translation APIs or fine-tune the ASI1 LLM for better translations.
5. **Add Analytics**: Integrate performance tracking for scheduled posts to analyze engagement metrics.

## Acknowledgments

- [Fetch.ai](https://fetch.ai/) for the uAgents framework
- Google for the Google Translate API
- Pollinations for their AI image generation API
- ASI1 for their LLM API
- All contributors who have helped improve this sample project# content_translator
