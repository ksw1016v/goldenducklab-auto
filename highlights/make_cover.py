"""하이라이트 표지(1080x1920, 가운데 원 안에 핵심) 만들기: python highlights/make_cover.py"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from playwright.sync_api import sync_playwright
from render import uri

HTML = """<html><head><meta charset="utf-8"><style>
body{margin:0;width:1080px;height:%(h)dpx;background:radial-gradient(circle at 50%% 50%%,#FFF9EA 0,#FFF1CC 55%%,#FBE3A6 100%%);
font-family:'Noto Sans CJK KR',sans-serif;overflow:hidden;position:relative}
.wrap{position:absolute;left:0;top:%(top)dpx;width:1080px;height:1080px}
.dots{position:absolute;inset:0;background-image:radial-gradient(#F5B800 3.5px,transparent 4px);background-size:34px 34px;opacity:.28;
 -webkit-mask-image:radial-gradient(circle at 50%% 50%%,transparent 0,transparent 300px,#000 520px)}
.panel{position:absolute;left:250px;top:270px;width:560px;height:560px;background:#fff;border:16px solid #5C2E0E;border-radius:56px;
 transform:rotate(-4deg);box-shadow:22px 22px 0 #F5B800;overflow:hidden}
.panel img{position:absolute;left:-62px;top:-40px;width:660px;height:660px}
.panel .line{position:absolute;left:0;right:0;top:0;height:0}
.bub{position:absolute;left:618px;top:150px;width:300px;height:210px;background:#fff;border:14px solid #5C2E0E;border-radius:50%%;
 display:flex;align-items:center;justify-content:center;font-size:118px;font-weight:900;color:#E2A800;transform:rotate(6deg)}
.tail{position:absolute;left:640px;top:318px;width:0;height:0;border-left:34px solid transparent;border-right:34px solid transparent;
 border-top:70px solid #5C2E0E;transform:rotate(28deg)}
.tail2{position:absolute;left:655px;top:314px;width:0;height:0;border-left:22px solid transparent;border-right:22px solid transparent;
 border-top:50px solid #fff;transform:rotate(28deg)}
.burst{position:absolute;color:#F5B800;font-size:90px;font-weight:900}
.pen{position:absolute;left:150px;top:690px;width:90px;height:300px;transform:rotate(-38deg)}
</style></head><body><div class="wrap"><div class="dots"></div>
<div class="panel"><img src="%(duck)s"></div>
<div class="tail"></div><div class="bub">!?</div><div class="tail2"></div>
<div class="burst" style="left:185px;top:205px;transform:rotate(-15deg)">✦</div>
<div class="burst" style="left:840px;top:760px;font-size:70px">✦</div>
<div class="burst" style="left:205px;top:770px;font-size:56px;color:#F06A8A">♥</div>
</div></body></html>"""

out = pathlib.Path(__file__).parent
with sync_playwright() as p:
    b = p.chromium.launch()
    for name, h, top in (("goldentoon_cover_1080x1920.png", 1920, 420), ("goldentoon_cover_1080x1080.png", 1080, 0)):
        pg = b.new_page(viewport={"width": 1080, "height": h})
        pg.set_content(HTML % {"h": h, "top": top, "duck": uri("duck.png")}, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.screenshot(path=str(out / name))
    b.close()
print("ok")
