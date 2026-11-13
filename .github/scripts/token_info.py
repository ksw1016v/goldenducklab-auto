import json, os, sys, time, urllib.request, urllib.parse
G = "https://graph.facebook.com/v23.0"
def get(path, **p):
    try:
        with urllib.request.urlopen(f"{G}/{path}?" + urllib.parse.urlencode(p), timeout=30) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read() or b"{}")
new, old = os.environ["IG_TOKEN"], os.environ["OLD"]
for nm, t in (("옛", old), ("새", new)):
    me = get("me", fields="id,name", access_token=t)
    d = get("debug_token", input_token=t, access_token=new).get("data", {})
    f = lambda k: time.strftime("%Y-%m-%d %H:%M", time.gmtime(d[k])) if d.get(k) else "없음"
    print(f"{nm} 토큰: 주인={me.get('name')} ({me.get('id')}) 오류={me.get('error', {}).get('message', '-')[:60]} | 종류={d.get('type')} 앱={d.get('application')} 유효={d.get('is_valid')} 발급={f('issued_at')} 만료={f('expires_at')}")
