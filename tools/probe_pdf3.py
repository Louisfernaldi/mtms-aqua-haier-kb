import requests, sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
S = requests.Session(); S.headers.update({"User-Agent": UA})
fid = "1f6p4JWm1EyBVTdb9C4dgrkSeFpE-MCEc"
r = S.get(f"https://drive.google.com/thumbnail?id={fid}&sz=w1000", timeout=60)
print("thumbnail:", r.status_code, r.headers.get("Content-Type"), len(r.content))
r2 = S.get(f"https://drive.google.com/file/d/{fid}/view", timeout=60)
pats = [
    r'"size":\s*"?(\d+)"?',
    r'\\"size\\":\s*\\"?(\d+)\\"?',
    r"fileSize[^,]{0,40}",
    r"bytes[^,]{0,30}",
]
for p in pats:
    m = re.findall(p, r2.text)
    if m:
        print(p[:30], "->", m[:5])
r3 = S.get(f"https://drive.google.com/uc?id={fid}", timeout=60)
print("uc noexport:", r3.status_code, r3.headers.get("Content-Type"), len(r3.content))
