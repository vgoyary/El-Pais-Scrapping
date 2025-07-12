# El País Opinion Article Scraper with BrowserStack

A comprehensive web scraping project that demonstrates Selenium automation, BrowserStack integration, and text processing for scraping Spanish opinion articles with automatic translation and analysis.

## Features

- **Web Scraping**: Scrapes articles from El País Opinion section using Selenium
- **Cross-Browser Testing**: Runs parallel tests across 5 different browser/OS combinations using BrowserStack
- **Translation**: Translates article titles and content snippets from Spanish to English using Google Translate
- **Text Analysis**: Analyzes translated titles for repeated words (>2 occurrences)
- **Image Downloading**: Downloads and saves article cover images
- **Parallel Processing**: Executes scraping across multiple browser sessions simultaneously

## Project Structure

```
browserstack/
├── scrapper.py            # Main scraper script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── scraped_articles.json # Output file with scraped data
└── article_images/       # Directory for downloaded images
```

## Requirements

- Python 3.7+
- BrowserStack account (for cross-browser testing)
- Internet connection

## Installation

1. **Clone/Download the project** and navigate to the directory

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up BrowserStack credentials**:
   - Edit `scrapper.py` and replace the placeholder credentials with your actual BrowserStack credentials:
   ```python
   BROWSERSTACK_USERNAME="your_browserstack_username"
   BROWSERSTACK_ACCESS_KEY="your_browserstack_access_key"
   ```

## BrowserStack Setup

1. **Create a BrowserStack account** at [browserstack.com](https://www.browserstack.com/)
2. **Get your credentials**:
   - Login to BrowserStack
   - Go to Account Settings
   - Copy your Username and Access Key
3. **Add credentials to `scrapper.py`**

## Usage

The script can run in two modes:

### Local Mode (using local Chrome)
```bash
# Edit scrapper.py and change the last line to:
# main(local=True, use_browserstack=False)
python scrapper.py
```

### BrowserStack Mode (parallel testing)
```bash
# Default mode - runs on BrowserStack
python scrapper.py
```

The script will:
1. Visit El País Opinion section
2. Extract article URLs
3. Scrape each article for title, content, and images
4. Download cover images to `article_images/`
5. Translate titles and content snippets to English
6. Analyze repeated words in translations
7. Save all data to `scraped_articles.json`

## Browser Configurations (BrowserStack Mode)

The script tests across these browser/OS combinations:
- Chrome on Windows 10
- Firefox on macOS Big Sur
- iPhone 12 (mobile)
- Samsung Galaxy S21 (mobile)
- Edge on Windows 11

## Output Files

After running, you'll find:
- `scraped_articles.json` - All scraped articles with metadata
- `article_images/` - Downloaded article images (named as `article_1.jpg`, `article_2.jpg`, etc.)

## Data Extracted

For each article:
- **Title** (Spanish and English)
- **Content snippet** (Spanish and English)
- **Cover image** (downloaded locally)
- **URL** of the article
- **Index** number

## Text Processing

The script analyzes translated titles and identifies:
- Words appearing more than 2 times across all titles
- Provides frequency count for each repeated word
- Displays results in the console

## Error Handling

The script includes robust error handling for:
- Network timeouts
- Browser session failures
- Image download errors
- Translation API failures
- BrowserStack connection issues

## Troubleshooting

### Common Issues:

1. **BrowserStack credentials error**:
   - Ensure credentials are correctly set in `scrapper.py`
   - Check BrowserStack account status

2. **Scraping errors**:
   - El País may have updated their HTML structure
   - Check console output for specific error messages

3. **Translation errors**:
   - Google Translate API may have rate limits
   - Script includes automatic retry logic

4. **Image download failures**:
   - Some images may not be accessible
   - Script continues processing other articles

## Configuration

Modify `scrapper.py` to adjust:
- Number of articles to scrape (currently set to 5)
- Browser capabilities for BrowserStack
- Target URLs
- Output file names

## Dependencies

- `selenium` - Web automation
- `requests` - HTTP requests for image downloads
- `beautifulsoup4` - HTML parsing
- `googletrans==4.0.0-rc1` - Translation services
- `webdriver-manager` - Automatic ChromeDriver management

## Security Note

**Important**: The current implementation has BrowserStack credentials hardcoded in the script. For production use, consider:
- Using environment variables
- Creating a separate config file (not committed to version control)
- Using BrowserStack's secure credential management

## Legal Notice

This scraper is for educational and research purposes. Please respect:
- El País' robots.txt and terms of service
- Rate limiting to avoid overwhelming servers
- Copyright laws regarding content usage

## License

This project is for educational demonstration purposes.

## Support

For issues or questions:
1. Check the console output for error messages
2. Verify BrowserStack credentials and account status
3. Ensure all dependencies are properly installed
4. Check that ChromeDriver is properly installed (handled automatically by webdriver-manager) 