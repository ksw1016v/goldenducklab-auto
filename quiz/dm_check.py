"""진단: 최근 DM 대화 목록과 마지막 메시지 확인 (읽기 전용)"""
import json, sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from publish import call, IG_USER_ID, api_base  # noqa: E402

print("API", api_base())
for path, p in [(f"{IG_USER_ID}/conversations", dict(platform="instagram", fields="updated_time,participants,messages.limit(3){message,from,to,created_time}", limit=5)),
                ("me/conversations", dict(platform="instagram", fields="updated_time,participants,messages.limit(3){message,from,created_time}", limit=5))]:
    try:
        r = call("GET", path, **p)
        for c in r.get("data", []):
            print("대화", c.get("updated_time"), [x.get("username") for x in c.get("participants", {}).get("data", [])])
            for m in c.get("messages", {}).get("data", []):
                print("   ", m.get("created_time"), (m.get("from") or {}).get("username"), (m.get("message") or "")[:60].replace("\n", " / "))
        break
    except SystemExit as ex:
        print("실패", path, str(ex)[:300])
