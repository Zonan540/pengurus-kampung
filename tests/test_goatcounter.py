"""Ujian 1.4.6.6: integrasi GoatCounter.

Guna:  python3 tests/test_goatcounter.py

Skrip sebenar gc.zgo.at digantikan dengan stub yang merekod panggilan goatcounter.count(), jadi ujian ini
menyemak kod game (skrip dimuat dengan titik akhir betul, event keluar pada masa yang betul, peranti pemilik
dilangkau) dan bukannya skrip GoatCounter sendiri.
"""
import subprocess, time, json, sys, os
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, '..', 'site')
PORT = 8821
ENDPOINT = 'https://pengurus-kampung.goatcounter.com/count'
STUB = ("window.goatcounter=window.goatcounter||{};"
        "window.goatcounter.count=function(v){(window.__gc=window.__gc||[]).push(v)};")

srv = subprocess.Popen([sys.executable, '-m', 'http.server', str(PORT)], cwd=ROOT,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(1)
results = []


def check(name, cond, detail=''):
    results.append({'ujian': name, 'lulus': bool(cond), 'butiran': '' if cond else detail})


def open_page(browser, init=None, beta_closed=False):
    ctx = browser.new_context()
    gc_hits = []
    ctx.route('**/gc.zgo.at/**', lambda r: (gc_hits.append(r.request.url),
                                           r.fulfill(status=200, content_type='application/javascript', body=STUB)))
    ctx.route('**/*.goatcounter.com/**', lambda r: r.fulfill(status=200, body=''))
    ctx.route('**/fonts.g*apis.com/**', lambda r: r.fulfill(status=200, body=''))
    if beta_closed:
        ctx.route('**/beta.json*', lambda r: r.fulfill(status=200, content_type='application/json',
                                                        body=json.dumps({'closed': True, 'blocked': []})))
    if init:
        ctx.add_init_script(init)
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto(f'http://localhost:{PORT}/')
    pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=30000)
    time.sleep(.8)
    return ctx, pg, errs, gc_hits


def events(pg):
    return [e.get('path') for e in (pg.evaluate("window.__gc||[]"))]


try:
    with sync_playwright() as p:
        b = p.chromium.launch()

        # 1. Pelawat baharu: skrip dimuat, pintu dibuka, kemudian sertai beta
        ctx, pg, errs, hits = open_page(b)
        tag = pg.evaluate("(()=>{const s=document.querySelector('script[data-goatcounter]');return s&&{ep:s.getAttribute('data-goatcounter'),src:s.src}})()")
        check('skrip GoatCounter dimuat dengan titik akhir betul', tag and tag['ep'] == ENDPOINT and tag['src'] == 'https://gc.zgo.at/count.js', str(tag))
        check('event pintu-dibuka dihantar sekali', events(pg).count('event/pintu-dibuka') == 1, str(events(pg)))
        pg.click('#pkjoin')
        time.sleep(1.2)
        check('event sertai-auto dihantar', 'event/sertai-auto' in events(pg), str(events(pg)))
        payload = pg.evaluate("window.__gc.map(v=>JSON.stringify(v)).join('|')")
        inv = pg.evaluate("localStorage.getItem('pk3-invite')")
        did = pg.evaluate("localStorage.getItem('pk3-did')")
        check('event tidak membawa ID peranti atau kod', (did or 'x') not in payload and 'AUTO' not in payload, payload)
        check('event dengan flag event=true', all(e.get('event') is True for e in pg.evaluate("window.__gc")), payload)
        check('tiada ralat halaman (pelawat)', not errs, str(errs))
        ctx.close()

        # 2. Beta penuh
        ctx, pg, errs, hits = open_page(b, beta_closed=True)
        pg.click('#pkjoin')
        time.sleep(1.2)
        check('event beta-penuh dihantar', 'event/beta-penuh' in events(pg), str(events(pg)))
        check('beta-penuh: tiada sertai-auto', 'event/sertai-auto' not in events(pg), str(events(pg)))
        ctx.close()

        # 3. Peranti pemilik: skrip tidak dimuat
        admin = "localStorage.setItem('pk3-invite', JSON.stringify({code:'PK-TEST-ADMN',adm:1,at:'2026-11-05'}))"
        ctx, pg, errs, hits = open_page(b, init=admin)
        has_tag = pg.evaluate("!!document.querySelector('script[data-goatcounter]')")
        check('peranti pemilik: skrip GoatCounter tidak dimuat', not has_tag and not hits, f'tag={has_tag} hits={hits}')
        check('peranti pemilik: tiada ralat halaman', not errs, str(errs))
        ctx.close()

        # 4. Penguji sedia ada: game terus dibuka, tiada event pintu
        tester = "localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-11-05'}))"
        ctx, pg, errs, hits = open_page(b, init=tester)
        check('penguji sedia ada: skrip dimuat', pg.evaluate("!!document.querySelector('script[data-goatcounter]')"))
        check('penguji sedia ada: tiada event pintu-dibuka', 'event/pintu-dibuka' not in events(pg), str(events(pg)))

        # 5. Hujung musim: event musim-1-tamat
        res = pg.evaluate("""()=>{try{UI.screen='game';newWorld();S.seasonNo=1;seasonEnd();return 'ok'}catch(e){return 'ralat: '+e.message}}""")
        check('seasonEnd boleh dipanggil dalam ujian', res == 'ok', res)
        check('event musim-1-tamat dihantar', 'event/musim-1-tamat' in events(pg), str(events(pg)))
        res = pg.evaluate("""()=>{try{newWorld();S.seasonNo=4;seasonEnd();return 'ok'}catch(e){return 'ralat: '+e.message}}""")
        check('musim 4 tidak menghantar event', 'event/musim-4-tamat' not in events(pg), str(events(pg)))
        check('tiada ralat halaman (penguji)', not errs, str(errs))
        ctx.close()

        # 6. Offline: GoatCounter tidak boleh dicapai, game tetap dibuka
        ctx = b.new_context()
        ctx.route('**/gc.zgo.at/**', lambda r: r.abort())
        ctx.route('**/fonts.g*apis.com/**', lambda r: r.fulfill(status=200, body=''))
        ctx.add_init_script(tester)
        pg = ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
        pg.goto(f'http://localhost:{PORT}/')
        pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=30000)
        time.sleep(.8)
        check('GoatCounter disekat: game tetap dibuka tanpa ralat', not errs, str(errs))
        ctx.close()
        b.close()
finally:
    srv.terminate()

print(json.dumps(results, ensure_ascii=False, indent=1))
sys.exit(0 if all(r['lulus'] for r in results) else 1)
