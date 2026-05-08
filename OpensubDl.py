import requests
import json
import os
import sys
import re
import questionary

API_KEY = 'AKGTCkV28zejNm3kvn6DaKVtyLsybEiW'
USER_AGENT = 'MySubBot v1.0'
BASE_URL = "https://api.opensubtitles.com/api/v1"

HEADERS = {
    'Api-Key': API_KEY,
    'User-Agent': USER_AGENT,
    'Content-Type': 'application/json'
}

def get_languages():
    # Fetch available languages for the selector
    try:
        res = requests.get(f"{BASE_URL}/infos/languages", headers=HEADERS)
        return {l['language_name']: l['language_code'] for l in res.json()['data']}
    except:
        return {"English": "en", "Hindi": "hi", "Spanish": "es"}

def search_subtitles(query, lang="en"):
    # Detect Season/Episode (e.g., "The Boys S01E01")
    series_match = re.search(r'(.*)\s+S(\d+)E(\d+)', query, re.IGNORECASE)
    params = {"languages": lang}
    
    if series_match:
        params["query"] = series_match.group(1).strip()
        params["season_number"] = int(series_match.group(2))
        params["episode_number"] = int(series_match.group(3))
    else:
        params["query"] = query

    response = requests.get(f"{BASE_URL}/subtitles", headers=HEADERS, params=params)
    return response.json().get('data', [])

def download_sub(file_id):
    res = requests.post(f"{BASE_URL}/download", headers=HEADERS, json={"file_id": file_id})
    data = res.json()
    
    link = data.get('link')
    name = data.get('file_name')
    
    print(f"📥 Downloading {name}...")
    content = requests.get(link).content
    with open(name, 'wb') as f:
        f.write(content)
    print("✅ Done!")

def main():
    query = questionary.text("What are we watching?").ask()
    if not query: return

    results = search_subtitles(query)
    
    if not results:
        print("❌ No subtitles found.")
        return

    # Create the "Choosing Layer"
    options = []
    for sub in results:
        attr = sub['attributes']
        trusted = "⭐ " if attr['from_trusted'] else ""
        label = f"{trusted}[{attr['language']}] {attr['release']} ({attr['download_count']} downloads)"
        options.append(questionary.Choice(title=label, value=attr['files'][0]['file_id']))

    # Let the user pick
    selected_file_id = questionary.select(
        "Select the best match:",
        choices=options
    ).ask()

    if selected_file_id:
        download_sub(selected_file_id)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
