
import requests

urls = [
    "https://agendas-medicas.onrender.com/radioterapia/feed",
    "https://agendas-medicas.onrender.com/plantillas/" # Another new endpoint likely missing
]

for url in urls:
    try:
        resp = requests.get(url, timeout=10)
        print(f"URL: {url} -> Status: {resp.status_code}")
    except Exception as e:
        print(f"URL: {url} -> Error: {e}")
