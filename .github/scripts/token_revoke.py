"""노출된 옛 토큰의 앱 권한을 철회해 무효로 만든다 (값은 출력하지 않음)."""
import json, os, urllib.request, urllib.parse
G = "https://graph.facebook.com/v23.0"
old = os.environ["OLD"]
req = urllib.request.Request(f"{G}/me/permissions?" + urllib.parse.urlencode({"access_token": old}), method="DELETE")
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        print("철회 응답:", r.read().decode()[:200])
except urllib.error.HTTPError as e:
    print("철회 오류:", e.code, json.loads(e.read() or b"{}").get("error", {}).get("message", "")[:200])
