"""Fasa 8: penerangan pencapaian dirahsiakan sebelum dibuka; kad pengurus (PNG + QR)."""
import subprocess, sys, time, os, base64
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8819'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []
def check(n, ok, d=''):
    print(('PASS ' if ok else 'FAIL ') + n, d if not ok else ''); 
    if not ok: fails.append(n)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1200, 'height': 900}); errs = []
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto('http://localhost:8819/index.html'); pg.wait_for_function("typeof newWorld==='function'", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'"); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Zonan Uji';ACT.startgame()}")
    pg.evaluate("()=>{S.ach={};ACT.nav('ach')}")
    txt = pg.evaluate("()=>document.getElementById('app').innerText")
    d0 = pg.evaluate("()=>ACH.map(a=>a.d)")
    check('tiada penerangan terdedah bila belum dibuka', not any(d in txt for d in d0))
    pg.evaluate("()=>{achGive('hat','x');closeModal();ACT.nav('ach')}")
    txt = pg.evaluate("()=>document.getElementById('app').innerText")
    d = pg.evaluate("()=>ACH.find(a=>a.id==='hat').d")
    others = pg.evaluate("()=>ACH.filter(a=>a.id!=='hat').map(a=>a.d)")
    check('penerangan dibuka selepas dicapai', d in txt)
    check('yang lain kekal rahsia', not any(o in txt for o in others))
    pg.evaluate("()=>{closeModal();S.job.wdl=[12,5,7];S.job.rep=40;ACT.nav('profile')}")
    check('butang kad dikongsi ada', pg.evaluate("()=>!!document.querySelector('[data-act=mgrcard]')"))
    pg.evaluate("()=>mMgrCard()"); pg.wait_for_function("document.getElementById('cardimg')&&document.getElementById('cardimg').src.startsWith('data:image/png')", timeout=10000)
    dim = pg.evaluate("()=>[UI.cardCv.width,UI.cardCv.height,cardFile()]")
    check('kad 1080x1350 dan nama fail kad-pengurus', dim[0] == 1080 and dim[1] == 1350 and dim[2].startswith('kad-pengurus-'), dim)
    # QR region has dark pixels
    dark = pg.evaluate("()=>{const x=UI.cardCv.getContext('2d');const d=x.getImageData(914,1214,124,124).data;let n=0;for(let i=0;i<d.length;i+=4)if(d[i]<40)n++;return n}")
    check('QR dilukis', dark > 1500, dark)
    open('/tmp/claude-0/-home-claude/7fc64f2f-22b2-5147-8052-ef8c7da90f0a/scratchpad/mgrcard.png', 'wb').write(base64.b64decode(pg.evaluate("()=>UI.cardCv.toDataURL('image/png')").split(',')[1]))
    pg.evaluate("()=>{closeModal();mCard(S.user)}"); time.sleep(1.5)
    check('kad kelab masih guna nama fail kelab', pg.evaluate("()=>cardFile()").startswith('kad-kelab-'))
    check('tiada ralat halaman', not errs, errs)
    b.close()
srv.terminate(); print('SEMUA LULUS' if not fails else 'GAGAL', fails); sys.exit(1 if fails else 0)
