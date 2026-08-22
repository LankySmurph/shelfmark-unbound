import logging
import requests
from bs4 import BeautifulSoup
from typing import List
from shelfmark.release_sources import BrowseRecord
from shelfmark.core.models import SearchFilters

logger = logging.getLogger(__name__)

def search_libgen(query: str, filters: SearchFilters = None) -> List[BrowseRecord]:
    """Scrapes Library Genesis for direct download book results."""
    logger.info(f"Searching LibGen directly for: {query}")
    results = []
    
    # Use standard LibGen mirror; you can map this to config.MIRRORS later if desired
    search_url = "https://libgen.is/search.php"
    params = {
        "req": query,
        "res": "25",
        "view": "simple",
        "column": "def"
    }
    
    try:
        response = requests.get(search_url, params=params, timeout=15)
        response.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"LibGen connection failed: {e}")
        return results

    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table', class_='c')
    
    if not table:
        logger.warning("No results table found on LibGen.")
        return results

    # Skip header row
    for row in table.find_all('tr')[1:]:
        cols = row.find_all('td')
        if len(cols) < 10:
            continue
            
        try:
            # Extract MD5 hash
            mirror_link = cols[9].find('a', href=True)
            if not mirror_link:
                continue
            href = mirror_link['href']
            md5_hash = href.split('md5=')[-1] if 'md5=' in href else None
            
            if not md5_hash:
                continue

            title = cols[2].get_text(strip=True)
            file_format = cols[8].get_text(strip=True).lower()
            
            # Format as Shelfmark's native BrowseRecord
            results.append(BrowseRecord(
                id=md5_hash,
                title=title,
                source="direct_download",
                author=cols[1].get_text(strip=True),
                publisher=cols[3].get_text(strip=True),
                year=cols[4].get_text(strip=True),
                language=cols[6].get_text(strip=True),
                size=cols[7].get_text(strip=True),
                format=file_format,
                content="ebook"
            ))
        except Exception as e:
            logger.debug(f"Skipping malformed LibGen row: {e}")
            continue
            
    return results
