import requests
import json
import os

API_KEY = 'AKGTCkV28zejNm3kvn6DaKVtyLsybEiW'
USER_AGENT = 'MySubBot v1.0'
HEADERS = {
    'Api-Key': API_KEY,
    'User-Agent': USER_AGENT,
    'Content-Type': 'application/json'
}

def search_subtitle(query):
    url = f"https://api.opensubtitles.com/api/v1/subtitles?query={query}&languages=en"
    response = requests.get(url, headers=HEADERS)
    data = response.json()
    
    if not data['data']:
        return None
    
    # Returning the first file_id from the first result
    return data['data'][0]['attributes']['files'][0]['file_id']

def download_subtitle(file_id):
    url = "https://api.opensubtitles.com/api/v1/download"
    payload = {"file_id": file_id}
    response = requests.post(url, headers=HEADERS, json=payload)
    
    dl_data = response.json()
    link = dl_data['link']
    file_name = dl_data['file_name']
    
    print(f"Downloading: {file_name}")
    r = requests.get(link, allow_redirects=True)
    with open(file_name, 'wb') as f:
        f.write(r.content)

if __name__ == "__main__":
    movie = input("Enter movie name: ")
    fid = search_subtitle(movie)
    if fid:
        download_subtitle(fid)
    else:
        print("Nothing found.")
