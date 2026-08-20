import requests, re, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA})
fid = "1f6p4JWm1EyBVTdb9C4dgrkSeFpE-MCEc"
r = S.get(f"https://drive.google.com/file/d/{fid}/view", timeout=60)
print("status", r.status_code, "len", len(r.text))
pats = [
    r'itemprop="name" content="([^"]+)"',
    r'itemprop="contentSize" content="([^"]+)"',
    r'"totalBytes":(\d+)',
    r"<title>([^<]+)</title>",
    r"application/pdf",
]
for p in pats:
    m = re.findall(p, r.text)
    if m:
        print(p[:40], "->", m[:4])
r2 = S.get(f"https://drive.google.com/file/d/{fid}/preview", timeout=60)
print("preview status", r2.status_code, "len", len(r2.text))
m2 = re.findall(r'"totalBytes":(\d+)', r2.text)
print("preview totalBytes:", m2[:3])
m3 = re.findall(r"<meta property=\"og:image\" content=\"([^\"]+)\"", r2.text)
print("og:image:", m3[:1])
m4 = re.findall(r"<meta property=\"og:title\" content=\"([^\"]+)\"", r2.text)
print("og:title:", m4[:1])
m5 = re.findall(r"<meta property=\"og:description\" content=\"([^\"]+)\"", r2.text)
print("og:desc:", m5[:1])
