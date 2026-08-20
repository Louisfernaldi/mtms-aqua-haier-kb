import requests, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA})
fid = "1f6p4JWm1EyBVTdb9C4dgrkSeFpE-MCEc"
r = S.get(f"https://drive.google.com/file/d/{fid}/view", timeout=60)
t = r.text
pats = [
    r'downloadUrl[^,]{0,200}',
    r'https://[a-z0-9\-\.]*googleusercontent\.com[^"\\]{0,150}',
    r'"size":(\d+)',
    r'"mimeType":"([^"]+)"',
    r'contentUrl[^,]{0,150}',
]
for p in pats:
    m = re.findall(p, t)
    if m:
        print(p[:50], "->", m[:3])
print("done")
