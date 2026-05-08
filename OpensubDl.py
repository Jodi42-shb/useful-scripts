# /// script
# dependencies = [
#   "requests",
#   "questionary",
# ]
# ///

import requests
import questionary
import sys
import re
import os

# --- Configuration ---
API_KEY = "AKGTCkV28zejNm3kvn6DaKVtyLsybEiW"  # The key you used successfully
USER_AGENT = "MySubBot v1.0"
BASE_URL = "https://api.opensubtitles.com/api/v1"

HEADERS = {
    "Api-Key": "AKGTCkV28zejNm3kvn6DaKVtyLsybEiW",
    "User-Agent": USER_AGENT,
    "Content-Type": "application/json"
}

def search_subtitles(query, lang_code):
    # Regex for Series (e.g., "The Boys S05E01")
    series_pattern = re.compile(r"(.*)\s+[sS](\d+)[eE](\d+)")
    match = series_pattern.search(query)
    
    params = {"languages": lang_code}
    if match:
        params["query"] = match.group(1).strip()
        params["season_number"] = int(match.group(2))
        params["episode_number"] = int(match.group(3))
    else:
        params["query"] = query

    try:
        res = requests.get(f"{BASE_URL}/subtitles", headers=HEADERS, params=params)
        
        # --- THE FIX: Check HTTP Status before parsing JSON ---
        if not res.ok:
            if res.status_code == 429:
                print("\n⏳ Rate limit hit! (More than 5 requests/sec). Wait a moment and try again.")
            elif res.status_code == 403:
                print("\n🛑 Cloudflare blocked the request. (HTTP 403 Forbidden)")
            else:
                print(f"\n❌ API Error ({res.status_code}): {res.text}")
            return []
            
        return res.json().get('data', [])
        
    except requests.exceptions.JSONDecodeError:
        print(f"\n❌ The API returned an unreadable response. (Server hiccup)")
        return []
    except Exception as e:
        print(f"\n❌ Network error: {e}")
        return []

def main():
    # 1. Select Language
    lang_map = {"English": "en", "Hindi": "hi", "French": "fr", "Spanish": "es"}
    lang_name = questionary.select(
        "Select subtitle language:",
        choices=list(lang_map.keys()),
        default="English"
    ).ask()
    
    if not lang_name: return # Exits if user hits Ctrl+C or ESC
    lang_code = lang_map[lang_name]

    # 2. Input Search
    query = questionary.text(
        "Search (Tip: Use 'Movie Name' or 'Show Name S01E01'):",
        validate=lambda text: True if len(text) > 0 else "Please enter a name"
    ).ask()
    
    if not query: return

    # 3. Search and Handle Results
    results = search_subtitles(query, lang_code)
    if not results:
        return 

    # 4. Interactive Choosing Layer
    choices = []
    for item in results:
        attr = item['attributes']
        trusted = "⭐ " if attr.get('from_trusted') else ""
        hi = " [CC]" if attr.get('hearing_impaired') else ""
        label = f"{trusted}{attr['release']}{hi} ({attr['download_count']} DLs)"
        
        choices.append(questionary.Choice(title=label, value=item))

    selected_item = questionary.select(
        "Choose the version that matches your file:",
        choices=choices
    ).ask()

    if not selected_item: return

    # 5. Download the file
    file_id = selected_item['attributes']['files'][0]['file_id']
    
    try:
        dl_res = requests.post(f"{BASE_URL}/download", headers=HEADERS, json={"file_id": file_id})
        
        # Check download API status
        if not dl_res.ok:
            print(f"\n❌ Failed to get download link. Error {dl_res.status_code}: {dl_res.text}")
            return
            
        dl_data = dl_res.json()
        
        print(f"\n📥 Downloading: {dl_data['file_name']}...")
        content = requests.get(dl_data['link']).content
        
        save_path = os.path.join(os.getcwd(), dl_data['file_name'])
        with open(save_path, 'wb') as f:
            f.write(content)
        print(f"✅ Successfully downloaded to {save_path}")
        
    except Exception as e:
        print(f"\n❌ Failed during download process: {e}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(0)
