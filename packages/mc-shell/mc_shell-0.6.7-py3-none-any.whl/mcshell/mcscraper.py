import urllib.request
import urllib.robotparser
import pickle
import time
import re
import yarl
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Optional

from mcshell.constants import *

# --- Configuration & Setup ---
# USER_AGENT = "MinecraftCommandDocBot/1.0"
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Initialize robots.txt parser once
rp = urllib.robotparser.RobotFileParser()
rp.set_url("https://minecraft.fandom.com/robots.txt")
rp.read()

# Try to import Playwright
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: Playwright is not installed. Browser fetching will fail.")


def fetch_with_browser(url,robots_txt_check=False):
    """
    Fetches HTML using Playwright (headless browser) with robots.txt compliance 
    and local caching.
    """
    # Ensure url is a yarl.URL object for consistent handling (accessing .name)
    if not isinstance(url, (yarl.URL, Path)):
        url_obj = yarl.URL(str(url))
    else:
        url_obj = url

    _pkl_path = MC_WEBPAGE_CACHE.joinpath(f"{url_obj.name}.pkl")

    # 1. Local Cache Check
    if _pkl_path.exists():
        print(f'Loading from cache: {_pkl_path.name}')
        with _pkl_path.open('rb') as f:
            return pickle.load(f)

    # 2. Robots.txt Check
    url_str = str(url_obj)
    if robots_txt_check and  not rp.can_fetch(USER_AGENT, url_str):
        print(f'Skipping (Blocked by robots.txt): {url_str}')
        return None

    # 3. Etiquette: Crawl Delay
    delay = rp.crawl_delay(USER_AGENT) or 1
    time.sleep(delay)

    # 4. Fetch with Playwright
    if not PLAYWRIGHT_AVAILABLE:
        print(f"Cannot fetch {url_str}: Playwright not installed.")
        return None

    print(f"Navigating to {url_str}...")
    try:
        html_content = None
        with sync_playwright() as p:
            # Launch a real browser (headless=True means no window pops up)
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=USER_AGENT)
            page = context.new_page()

            page.goto(url_str)

            # Wait a moment to ensure JS-heavy wiki content loads
            time.sleep(2)

            # Get the rendered HTML source
            html_content = page.content()
            browser.close()

        # 5. Save to Cache
        if html_content:
            with _pkl_path.open('wb') as f:
                pickle.dump(html_content, f)
        
        return html_content

    except Exception as e:
        print(f"Failed to fetch {url_str} with browser: {e}")
        return None


def make_docs():
    # Fetch the main list page
    main_html = fetch_with_browser(MC_DOC_URL)
    if not main_html:
        return {}

    _soup_data = BeautifulSoup(main_html, 'html.parser')
    _tables = _soup_data.find_all('table', attrs={'class': 'stikitable'})

    if not _tables:
        print("Could not find the commands table.")
        return {}

    _code_elements = _tables[0].select('code')
    _doc_dict = {}

    for _code_element in _code_elements:
        _cmd = _code_element.text.strip().lstrip('/') # Clean command name
        _parent = _code_element.find_parent()

        # Guard against index errors if the table structure shifts
        siblings = _parent.find_next_siblings()
        if not siblings: continue
        _doc_line = siblings[0].text.strip()

        try:
            anchor = _code_element.find_all('a')
            if not anchor: continue

            _doc_url_stub = yarl.URL(anchor[0].attrs['href'])
            # Ensure we are joining paths correctly with yarl
            _doc_url = MC_DOC_URL.origin().joinpath(str(_doc_url_stub).lstrip('/'))
        except (IndexError, KeyError):
            continue

        # Recursive Fetch using Browser
        sub_html = fetch_with_browser(_doc_url)
        if not sub_html:
            continue

        _doc_soup_data = BeautifulSoup(sub_html, 'html.parser')

        try:
            # More robust way to find the Syntax header
            _syntax_span = _doc_soup_data.find('span', id='Syntax') or \
                           _doc_soup_data.find('span', string='Syntax')

            if _syntax_span:
                _h2_parent = _syntax_span.find_parent('h2')
                _dl_block = _h2_parent.find_next_sibling('dl')
                _doc_code_elements = _dl_block.find_all('code')

                _doc_code_lines = [
                    code.text.strip() for code in _doc_code_elements
                    if code.text.strip().startswith(_cmd)
                ]
            else:
                _doc_code_lines = []
        except Exception:
            _doc_code_lines = []

        _doc_dict[_cmd] = (_doc_line, str(_doc_url), _doc_code_lines)

    # Save final results
    with MC_DOC_PATH.open('wb') as f:
        pickle.dump(_doc_dict, f)

    return _doc_dict


def make_materials():
    html_content = fetch_with_browser(MC_MATERIAL_URL)
    if not html_content:
        return []

    _soup_data = BeautifulSoup(html_content, 'html.parser')
    material_names = []

    enum_summary_section = _soup_data.find('section', id='enum-constant-summary')
    if not enum_summary_section:
        print(f"Error: Could not find the section with id 'enum-constant-summary' on the page {MC_MATERIAL_URL}")
        return material_names

    code_tags_in_section = enum_summary_section.select('code')
    for code_tag in code_tags_in_section:
        link_tags_in_code = code_tag.find_all('a')
        for link_tag in link_tags_in_code:
            text = link_tag.string
            if text and text.upper() == text:
                if text.strip() not in material_names: # Avoid duplicates from broader search
                     material_names.append(text.strip())

    pickle.dump(material_names, MC_MATERIALS_PATH.open('wb'))

    return sorted(list(set(material_names))) # Return sorted unique names


def make_entity_id_map() -> Optional[dict[str, int]]:
    """
    Fetches and parses the implemented Bukkit EntityType.java file to create a mapping
    from the Bukkit enum name string to its legacy numerical ID.
    """
    java_code_html = fetch_with_browser(MC_ENTITY_TYPE_URL)
    
    if not java_code_html:
        return None

    # Playwright returns rendered HTML. Depending on if the URL is raw or a view page,
    # we might need to parse it. Assuming it's the raw text content or wrapped in pre.
    # We treat the string result as the content to parse.
    
    # Capture enum constant name and its ID.
    pattern = re.compile(r"^\s*([A-Z_]+)\(.*?,\s*(-?\d+).*?\),?$")

    entity_id_map = {}
    lines = java_code_html.splitlines()
    is_deprecated = False

    for line in lines:
        stripped_line = line.strip()

        # Check for @Deprecated annotation
        if stripped_line == "@Deprecated":
            is_deprecated = True
            continue

        try:
            match = pattern.match(stripped_line)
        except TypeError:
             # Fallback if type issues occur, though stripped_line is str
            match = pattern.match(str(stripped_line))

        if match and not is_deprecated:
            enum_name = match.group(1)
            entity_id = int(match.group(2))

            if enum_name != 'UNKNOWN' and entity_id != -1:
                entity_id_map[enum_name] = entity_id
        
        # Reset the deprecated flag
        is_deprecated = False

    pickle.dump(entity_id_map, MC_ENTITY_ID_MAP_PATH.open('wb'))
    return entity_id_map
