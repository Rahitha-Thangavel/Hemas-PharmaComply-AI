import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path
import streamlit as st
import json

class NMRAWatcher:
    def __init__(self, config):
        self.config = config
        self.data_dir = Path(config["paths"]["data_dir"])
        self.legislation_url = config["paths"]["nmra_legislation_url"]
        self.price_controls_url = config["paths"]["nmra_price_controls_url"]
        
        # Ensure data dir exists
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def sync(self):
        """
        Main sync method: Scrapes URLs, identifies new PDFs, and downloads them.
        Returns a dictionary with status and found file details.
        """
        results = {
            "found": 0,
            "downloaded": 0,
            "new_files": [],
            "errors": []
        }

        urls_to_scrape = [
            ("Legislation/Gazettes", self.legislation_url),
            ("Price Controls/MRP", self.price_controls_url)
        ]

        # Load processed filenames from metadata to avoid duplicates
        processed_files = self._get_processed_original_names()

        for category, url in urls_to_scrape:
            try:
                found_links = self._get_pdf_links(url)
                results["found"] += len(found_links)
                
                for link in found_links:
                    filename = self._get_filename_from_url(link)
                    target_path = self.data_dir / filename
                    
                    # Check if file exists OR if it was already processed/renamed
                    if not target_path.exists() and filename not in processed_files:
                        if self._download_file(link, target_path):
                            results["downloaded"] += 1
                            results["new_files"].append(filename)
                            # Add to tracking set to avoid downloading same file twice in one sync session
                            processed_files.add(filename)
            except Exception as e:
                results["errors"].append(f"Error scraping {category}: {str(e)}")

        return results

    def _get_processed_original_names(self):
        """
        Loads the list of already processed 'original_names' from metadata.json,
        but ONLY if the corresponding file actually exists on disk.
        """
        processed = set()
        metadata_path = Path("data/metadata.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    meta_data = json.load(f)
                    for filename, entry in meta_data.items():
                        # Check if the renamed file actually exists in data/raw
                        if (self.data_dir / filename).exists() and "original_name" in entry:
                            processed.add(entry["original_name"])
            except Exception as e:
                print(f"Metadata read error in watcher: {e}")
        return processed

    def _get_pdf_links(self, url):
        """
        Scrapes a page for links pointing to PDFs, specifically from the Webflow CDN.
        """
        links = set()
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all <a> tags
            for a in soup.find_all('a', href=True):
                href = a['href']
                # Check for PDF extension and Webflow CDN domain
                if '.pdf' in href.lower() or 'cdn.prod.website-files.com' in href:
                    # Resolve relative URLs
                    full_url = urljoin(url, href)
                    links.add(full_url)
            
            # Also find links inside scripts or data-attributes if necessary (Webflow sometimes does dynamic loading)
            # For NMRA, most direct PDF links are in <a> or data-attributes
        except Exception as e:
            raise Exception(f"Failed to fetch {url}: {e}")
            
        return list(links)

    def _get_filename_from_url(self, url):
        """
        Extracts a clean filename from the URL, handling URL encoding and Webflow's unique ID prefixes.
        """
        import urllib.parse
        
        # Get the last part of the URL
        raw_name = url.split('/')[-1]
        
        # Decode URL encoding (e.g., %20 -> space)
        decoded_name = urllib.parse.unquote(raw_name)
        
        # Webflow prefixes often look like: [random_id]_[real_filename].pdf
        # We try to strip the hash prefix if it's there
        if '_' in decoded_name and len(decoded_name.split('_')[0]) > 20: # Long random hash
            parts = decoded_name.split('_')
            # Join the rest in case the original filename had underscores
            name_without_hash = '_'.join(parts[1:])
            # Prepend 'NMRA_' for consistency
            return f"NMRA_{name_without_hash}"
            
        return f"NMRA_{decoded_name}"

    def _download_file(self, url, path):
        """
        Downloads a file from a URL to a local path.
        """
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(url, headers=headers, stream=True, timeout=30)
            response.raise_for_status()
            
            with open(path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            return True
        except Exception as e:
            st.error(f"Failed to download {url}: {e}")
            return False

if __name__ == "__main__":
    # Test script
    import yaml
    with open("config/config.yaml", "r") as f:
        cfg = yaml.safe_load(f)
    watcher = NMRAWatcher(cfg)
    print("Syncing with NMRA...")
    results = watcher.sync()
    print(results)
