import os
import time
import requests
import json
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from googletrans import Translator
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

# Replace these with your BrowserStack credentials
BROWSERSTACK_USERNAME="vileenaranigoyar_XxRP47"
BROWSERSTACK_ACCESS_KEY="PsBBBag8STAET2C5AzHn"

# Ensure output folder exists
os.makedirs("article_images", exist_ok=True)

translator = Translator()

def get_chrome_driver_path():
    """Helper function to get the correct ChromeDriver path"""
    chrome_driver_path = ChromeDriverManager().install()
    if chrome_driver_path.endswith("chromedriver-win32/THIRD_PARTY_NOTICES.chromedriver"):
        chrome_driver_path = chrome_driver_path.replace("THIRD_PARTY_NOTICES.chromedriver", "chromedriver.exe")
    elif not chrome_driver_path.endswith("chromedriver.exe"):
        # If the path doesn't end with .exe, try to find the chromedriver.exe in the same directory
        import os
        if os.path.isdir(chrome_driver_path):
            chrome_driver_path = os.path.join(chrome_driver_path, "chromedriver.exe")
        else:
            # Check if chromedriver.exe exists in the same directory
            driver_dir = os.path.dirname(chrome_driver_path)
            potential_driver = os.path.join(driver_dir, "chromedriver.exe")
            if os.path.exists(potential_driver):
                chrome_driver_path = potential_driver
    return chrome_driver_path

def save_articles_to_file(articles_data, filename="scraped_articles.json"):
    """Save scraped articles data to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(articles_data, f, ensure_ascii=False, indent=2)
        print(f"[INFO] Articles data saved to {filename}")
    except Exception as e:
        print(f"[ERROR] Failed to save articles data: {e}")

def scrape_article(driver, url, index):
    try:
        driver.get(url)
        time.sleep(3)

        # Try to handle cookie banner if present
        try:
            cookie_button = WebDriverWait(driver, 3).until(
                EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Aceptar") or contains(text(),"Accept")]'))
            )
            cookie_button.click()
            time.sleep(2)
            print(f"[INFO] Cookie banner handled for article {index}")
        except:
            pass  # No cookie banner or already handled

        soup = BeautifulSoup(driver.page_source, "html.parser")

        # Try multiple selectors for the article title
        title_elem = None
        title_selectors = [
            "h1.c_t",  # Main title with class
            "h1",      # Any h1
            ".headline h1",  # Headline container
            "[data-dtm-region='articulo_apertura'] h1",  # Article opening section
            ".article-header h1"  # Article header
        ]
        
        for selector in title_selectors:
            try:
                title_elem = soup.select_one(selector)
                if title_elem and title_elem.text.strip():
                    break
            except:
                continue

        title = title_elem.text.strip() if title_elem else "No title found"
        
        # Get article content, avoiding cookie consent and navigation content
        content_selectors = [
            "div.c_d",  # Main content div
            ".article-body",  # Article body
            ".c_d p",  # Paragraphs in content div
            "div[data-dtm-region='articulo_cuerpo']",  # Article body region
            ".a_b p"  # Alternative paragraph selector
        ]
        
        content_divs = []
        for selector in content_selectors:
            try:
                elements = soup.select(selector)
                if elements:
                    content_divs = elements
                    break
            except:
                continue
        
        # If no specific content found, try general paragraphs but filter out cookie/navigation content
        if not content_divs:
            all_paragraphs = soup.find_all("p")
            content_divs = [p for p in all_paragraphs 
                           if p.text.strip() and 
                           not any(keyword in p.text.lower() for keyword in 
                                  ['cookie', 'configuración', 'configuration', 'consentimiento', 'consent', 
                                   'suscripción', 'subscription', 'premium', 'política', 'policy'])]
        
        # Extract clean content
        content_parts = []
        for div in content_divs:
            text = div.text.strip()
            if text and len(text) > 50:  # Only include substantial text
                # Skip cookie-related content
                if not any(keyword in text.lower() for keyword in 
                          ['cookie', 'configuración', 'configuration', 'consentimiento', 'consent', 
                           'suscripción', 'subscription', 'premium', 'política', 'policy']):
                    content_parts.append(text)
        
        content = " ".join(content_parts) if content_parts else ""

        # Debug content extraction - let's be more aggressive in finding content
        if not content:
            print(f"[DEBUG] No content found with primary selectors, trying alternative methods...")
            
            # Try to find the main article content more aggressively
            article_selectors = [
                "article",
                ".c_d",
                ".article-content",
                ".story-body",
                ".entry-content",
                "div[data-dtm-region='articulo_cuerpo']",
                ".a_c .a_c_t",  # Alternative content selectors
                ".a_b"  # Article body
            ]
            
            for selector in article_selectors:
                try:
                    article_container = soup.select_one(selector)
                    if article_container:
                        # Get all text from paragraphs within this container
                        paragraphs = article_container.find_all('p')
                        if paragraphs:
                            content_parts = []
                            for p in paragraphs:
                                text = p.get_text(strip=True)
                                if (text and len(text) > 30 and 
                                    not any(keyword in text.lower() for keyword in 
                                           ['cookie', 'configuración', 'configuration', 'consentimiento', 'consent', 
                                            'suscripción', 'subscription', 'premium', 'política', 'policy', 
                                            'suscríbete', 'subscribe', 'ya soy suscriptor'])):
                                    content_parts.append(text)
                            
                            if content_parts:
                                content = " ".join(content_parts[:10])  # Limit to first 10 good paragraphs
                                print(f"[DEBUG] Found content using selector: {selector}")
                                break
                except Exception as e:
                    print(f"[DEBUG] Selector {selector} failed: {e}")
                    continue
            
            # If still no content, try getting all paragraphs and filter aggressively
            if not content:
                print(f"[DEBUG] Still no content, trying all paragraphs...")
                all_paragraphs = soup.find_all('p')
                content_parts = []
                for p in all_paragraphs:
                    text = p.get_text(strip=True)
                    if (text and len(text) > 50 and 
                        not any(keyword in text.lower() for keyword in 
                               ['cookie', 'configuración', 'configuration', 'consentimiento', 'consent', 
                                'suscripción', 'subscription', 'premium', 'política', 'policy', 
                                'suscríbete', 'subscribe', 'ya soy suscriptor', 'términos y condiciones',
                                'quieres añadir otro usuario', 'continúas leyendo', 'modalidad premium'])):
                        content_parts.append(text)
                        if len(content_parts) >= 5:  # Stop after finding 5 good paragraphs
                            break
                
                if content_parts:
                    content = " ".join(content_parts)
                    print(f"[DEBUG] Found content using all paragraphs filter")

        # Re-add image extraction without linter errors
        image_url = None
        image_filename = None
        
        # Find meta tags with og:image property using CSS selector
        og_image_tags = soup.select('meta[property="og:image"]')
        if og_image_tags:
            for meta_tag in og_image_tags:
                img_content = meta_tag.get("content")
                if img_content:
                    image_url = img_content
                    break

        if image_url and isinstance(image_url, str):
            try:
                img_data = requests.get(image_url).content
                image_filename = f"article_{index}.jpg"
                with open(f"article_images/{image_filename}", "wb") as f:
                    f.write(img_data)
                print(f"Image saved: {image_filename}")
            except Exception as img_error:
                print(f"Error downloading image for article {index}: {img_error}")

        print(f"\n[Article {index}] Title (Spanish): {title}")
        print(f"[Content] Length: {len(content)} characters")
        print(f"[Content] Snippet: {content[:300]}...\n")

        # Translate title
        translated_title = ""
        if title and title != "No title found":
            translated_title = translator.translate(title, src='es', dest='en').text
            print(f"[Translated] Title: {translated_title}")
        
        # Translate content snippet (first 500 chars to avoid API limits)
        translated_content = ""
        if content and isinstance(content, str) and len(content) > 50:
            content_snippet = content[:500] if len(content) > 500 else content
            try:
                translated_content = translator.translate(content_snippet, src='es', dest='en').text
                print(f"[Translated] Content snippet: {translated_content[:200]}...")
            except Exception as e:
                print(f"[WARNING] Could not translate content: {e}")

        # Return complete article data
        return {
            "index": index,
            "url": url,
            "title_spanish": title,
            "title_english": translated_title,
            "content_spanish": content,
            "content_english": translated_content,
            "image_filename": image_filename,
            "image_url": image_url
        }

    except Exception as e:
        print(f"Error scraping article {index}: {e}")
        return {
            "index": index,
            "url": url,
            "title_spanish": "",
            "title_english": "",
            "content_spanish": "",
            "content_english": "",
            "image_filename": None,
            "image_url": None,
            "error": str(e)
        }

def run_on_browserstack(url, index, capabilities):
    from selenium.webdriver.remote.webdriver import WebDriver
    from selenium.webdriver.remote.remote_connection import RemoteConnection

    print(f"[INFO] Connecting to BrowserStack for article {index} with capabilities: {capabilities}")
    remote_url = f"http://{BROWSERSTACK_USERNAME}:{BROWSERSTACK_ACCESS_KEY}@hub-cloud.browserstack.com/wd/hub"
    
    try:
        # Create options object and set capabilities
        options = webdriver.ChromeOptions()
        for key, value in capabilities.items():
            options.set_capability(key, value)
        
        print(f"[INFO] Creating remote WebDriver session for article {index}...")
        driver = webdriver.Remote(
            command_executor=remote_url,
            options=options
        )
        print(f"[INFO] BrowserStack session established for article {index}")
        
        article_data = scrape_article(driver, url, index)
        
        print(f"[INFO] Closing BrowserStack session for article {index}")
        driver.quit()
        return article_data
    except Exception as e:
        print(f"[ERROR] BrowserStack connection failed for article {index}: {e}")
        raise e

def main(local=True, use_browserstack=False):
    base_url = "https://elpais.com/opinion/"
    print("[INFO] Visiting:", base_url)

    # Get ChromeDriver path using helper function
    chrome_driver_path = get_chrome_driver_path()
    service = Service(chrome_driver_path)
    driver = webdriver.Chrome(service=service)
    driver.get(base_url)
    time.sleep(5)

    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.XPATH, '//button[contains(text(),"Aceptar")]'))
        ).click()
        print("[INFO] Cookie banner accepted")
    except:
        print("[INFO] No cookie banner found or already accepted")

    # Try multiple selectors to find articles
    article_elements = []
    selectors = [
        "//a[contains(@class, 'c_t')]",  # Original selector
        "//article//a[contains(@href, '/opinion/')]",  # Articles with opinion URLs
        "//h2//a[contains(@href, '/opinion/')]",  # Headlines with opinion URLs
        "//a[contains(@href, '/opinion/') and contains(@class, 'c_t')]",  # Combined selector
        "//a[contains(@href, '/opinion/')]",  # Any link with opinion URL
        "//article//h2//a",  # Article headlines
        "//div[contains(@class, 'article')]//a",  # Articles with article class
    ]
    
    for selector in selectors:
        try:
            article_elements = driver.find_elements(By.XPATH, selector)
            if article_elements:
                print(f"[INFO] Found {len(article_elements)} articles using selector: {selector}")
                break
        except Exception as e:
            print(f"[DEBUG] Selector failed: {selector} - {e}")
            continue
    
    if not article_elements:
        print("[WARNING] No articles found with any selector. Trying to find any links on the page...")
        try:
            all_links = driver.find_elements(By.TAG_NAME, "a")
            opinion_links = []
            for link in all_links:
                href = link.get_attribute("href")
                if href and "/opinion/" in href:
                    opinion_links.append(link)
            if opinion_links:
                article_elements = opinion_links
                print(f"[INFO] Found {len(article_elements)} opinion links as fallback")
        except Exception as e:
            print(f"[ERROR] Fallback search failed: {e}")

    # Take first 10 articles, but filter out editorial column pages and ensure we get unique individual articles
    article_elements = article_elements[:15]  # Get more initially to filter
    article_urls = []
    seen_urls = set()  # Track URLs we've already added to avoid duplicates
    
    for element in article_elements:
        href = element.get_attribute("href")
        if href and "/opinion/" in href:
            # Filter out editorial column pages and ensure we get individual articles
            if (not href.endswith("/editoriales/") and 
                not href.endswith("/opinion/") and 
                not "/editoriales/" in href and
                "2025" in href and  # Ensure it's a dated article
                href not in seen_urls):  # Avoid duplicates
                article_urls.append(href)
                seen_urls.add(href)
                if len(article_urls) >= 5:  # Stop when we have 5 unique articles
                    break

    driver.quit()

    print(f"[INFO] Found {len(article_urls)} individual articles to scrape")
    for i, url in enumerate(article_urls, 1):
        print(f"[INFO] Article {i}: {url}")

    articles_data = []

    if local and not use_browserstack:
        print("[INFO] Running locally with Chrome...")
        # Get ChromeDriver path using helper function
        chrome_driver_path = get_chrome_driver_path()
        service = Service(chrome_driver_path)
        driver = webdriver.Chrome(service=service)
        for i, url in enumerate(article_urls, 1):
            article_data = scrape_article(driver, url, i)
            articles_data.append(article_data)
        driver.quit()
    elif use_browserstack and not local:
        print("[INFO] Executing on BrowserStack with 5 parallel sessions...")
        capabilities_list = [
            {"browserName": "Chrome", "os": "Windows", "os_version": "10", "name": "Test1"},
            {"browserName": "Firefox", "os": "OS X", "os_version": "Big Sur", "name": "Test2"},
            {"device": "iPhone 12", "realMobile": "true", "os_version": "14", "name": "Test3"},
            {"device": "Samsung Galaxy S21", "realMobile": "true", "os_version": "11.0", "name": "Test4"},
            {"browserName": "Edge", "os": "Windows", "os_version": "11", "name": "Test5"},
        ]

        print(f"[INFO] Starting {len(capabilities_list)} parallel BrowserStack sessions...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            results = [
                executor.submit(run_on_browserstack, article_urls[i], i+1, capabilities_list[i])
                for i in range(min(len(article_urls), len(capabilities_list)))
            ]
            print("[INFO] Waiting for BrowserStack sessions to complete...")
            for i, res in enumerate(results):
                try:
                    article_data = res.result()
                    articles_data.append(article_data)
                    print(f"[INFO] BrowserStack session {i+1} completed successfully")
                except Exception as e:
                    print(f"[ERROR] BrowserStack session {i+1} failed: {e}")
                    articles_data.append({
                        "index": i+1,
                        "error": f"BrowserStack execution failed: {e}"
                    })
    else:
        print(f"[ERROR] Invalid configuration: local={local}, use_browserstack={use_browserstack}")
        print("[ERROR] Must set either local=True OR use_browserstack=True, not both or neither")
        return

    # Save all articles data to file
    save_articles_to_file(articles_data)

    # Repeated Word Analysis
    print("\n[ANALYSIS] Repeated Words in Translated Titles:")
    word_list = []
    for article in articles_data:
        title = article.get('title_english', '')
        if title:  # Check if title is not empty
            word_list.extend(title.lower().split())

    word_counts = Counter(word_list)
    repeated_words_found = False
    for word, count in word_counts.items():
        if count > 2:
            print(f"{word}: {count}")
            repeated_words_found = True
    
    if not repeated_words_found:
        print("No words repeated more than twice found.")

if __name__ == "__main__":
    # BrowserStack testing mode - will run on 5 parallel browser sessions
    print("[INFO] Starting BrowserStack parallel testing...")
    main(local=False, use_browserstack=True)
