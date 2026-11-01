"""Ujian 1.4.6.4: amaran autosave gagal, semakan fail import, nombor versi skema, simpanan lama masih boleh dibuka.

Guna:  python3 tests/test_simpanan_1464.py [commit-build-lama]
Build lama (lalai HEAD~0 sebelum perubahan 1.4.6.4 ialah commit e7d74e9) diambil daripada git untuk menjana simpanan format lama.
"""
import subprocess, time, json, sys, os, tempfile, shutil
from playwright.sync_api import sync_playwright

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, '..')
NEW_ROOT = os.path.join(REPO, 'site')
OLD_REV = sys.argv[1] if len(sys.argv) > 1 else 'e7d74e9'

tmp = tempfile.mkdtemp(prefix='pk-old-')
subprocess.run(f'git -C "{REPO}" archive {OLD_REV} site | tar -x -C "{tmp}"', shell=True, check=True)
OLD_ROOT = os.path.join(tmp, 'site')

def serve(root, port):
    return subprocess.Popen([sys.executable, '-m', 'http.server', str(port)], cwd=root, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
srv_new, srv_old = serve(NEW_ROOT, 8812), serve(OLD_ROOT, 8813)
time.sleep(1)

results = []
def check(name, cond, detail=''):
    results.append({'ujian': name, 'lulus': bool(cond), 'butiran': detail if not cond else ''})

INIT = "localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')"

def boot(ctx, url):
    pg = ctx.new_page()
    errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto(url)
    pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=30000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=30000)
    time.sleep(.5)
    return pg, errs

def start_game(pg, steps):
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate("""(n)=>{for(let i=0;i<n;i++){if(S.fr&&!S.fr.done){frAuto();frConfirm()}S.job.conf=Math.max(S.job.conf,80);doAdvance();closeSummary();closeModal()}}""", steps)

with sync_playwright() as p:
    b = p.chromium.launch()

    # ---- 1. Jana simpanan format lama daripada build lama
    ctx_old = b.new_context(viewport={'width': 390, 'height': 844})
    ctx_old.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx_old.add_init_script(INIT)
    pg_old, errs_old = boot(ctx_old, 'http://localhost:8813/index.html')
    start_game(pg_old, 25)
    old_has_sv = pg_old.evaluate("()=>S.sv!==undefined")
    old_z = pg_old.evaluate("()=>packS()")
    old_b = pg_old.evaluate("()=>packS(true)")
    old_meta = {'seasonNo': pg_old.evaluate("()=>S.seasonNo"), 't': pg_old.evaluate("()=>S.t"), 'club': pg_old.evaluate("()=>S.clubs[S.user].name")}
    check('build lama tiada sv (andaian ujian)', old_has_sv is False)
    check('build lama tiada ralat semasa jana simpanan', not errs_old, errs_old)
    ctx_old.close()

    # ---- 2. Build baharu
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script(INIT)
    pg, errs = boot(ctx, 'http://localhost:8812/index.html')

    ver = pg.evaluate("()=>[VERSION,BUILD,SCHEMA]")
    import re
    check('label versi 1.4.3.x / b146x / SCHEMA 7', bool(re.fullmatch(r'Versi 1\.4\.3\.\d+', ver[0])) and bool(re.fullmatch(r'b146\d', ver[1])) and ver[2] == 7, ver)

    # ---- 3. Simpanan lama (tanpa sv) boleh dibuka
    r = pg.evaluate("""([z,bb])=>{const a=parseSave(z),c=parseSave(bb);return {z:!!a.s,zerr:a.err||null,b:!!c.s,berr:c.err||null,zsv:a.s&&a.s.sv,zseason:a.s&&a.s.seasonNo,zt:a.s&&a.s.t}}""", [old_z, old_b])
    check('simpanan lama (UTF16) lulus parseSave', r['z'], r)
    check('simpanan lama (base64) lulus parseSave', r['b'], r)
    check('simpanan lama tiada sv selepas parse', r['zsv'] is None, r)
    check('data simpanan lama utuh (musim/minggu)', r['zseason'] == old_meta['seasonNo'] and r['zt'] == old_meta['t'], [r, old_meta])
    # muat melalui slot auto seperti pemain sebenar
    pg.evaluate("""(z)=>{localStorage.setItem('pk3-slot-auto',z);const m=getMeta();m.auto={club:'x',kit:['#111','#eee'],mgr:'Uji',lg:3,season:2027,no:1,d:'x',ts:Date.now(),ver:'Versi 1.4.3.3 b1463'};setMeta(m)}""", old_z)
    pg.evaluate("()=>{ACT.loadslot('auto')}")
    after = pg.evaluate("()=>({user:!!S.user,club:S.clubs[S.user].name,seasonNo:S.seasonNo,t:S.t,screen:UI.screen,msg:UI.saveMsg})")
    check('loadslot auto dari simpanan lama berjaya', after['user'] and after['club'] == old_meta['club'] and after['t'] == old_meta['t'] and after['screen'] == 'game', after)
    # main satu langkah, lepas itu simpan mesti ada sv
    pg.evaluate("()=>{if(S.fr&&!S.fr.done){frAuto();frConfirm()}S.job.conf=Math.max(S.job.conf,80);doAdvance();closeSummary();closeModal();saveFlush()}")
    stored = pg.evaluate("()=>{const r=parseSave(localStorage.getItem('pk3-slot-auto'));return {ok:!!r.s,sv:r.s&&r.s.sv,bld:r.s&&r.s.bld,meta:getMeta().auto.ver}}")
    check('autosave baharu membawa sv=7 dan bld', stored['ok'] and stored['sv'] == 7 and stored['bld'] == ver[0] + ' ' + ver[1] and ver[1] in stored['meta'], stored)
    check('simpanan lama boleh dimainkan terus selepas dimuat', not errs, errs)

    # ---- 4. Putaran balik pack/unpack
    rt = pg.evaluate("()=>{const a=packS(),c=packS(true);const x=parseSave(a),y=parseSave(c);return {a:!!x.s,c:!!y.s,same:JSON.stringify(x.s)===JSON.stringify(y.s)&&x.s.seasonNo===S.seasonNo}}")
    check('pack/unpack ulang alik tepat', rt['a'] and rt['c'] and rt['same'], rt)

    # ---- 5. Semakan kandungan simpanan (checkSave)
    cases = pg.evaluate("""()=>{const good=JSON.parse(JSON.stringify(S));const out={};
      const t=(n,f)=>{const s=JSON.parse(JSON.stringify(good));f(s);out[n]=checkSave(s)};
      t('baik',s=>{});
      t('clubs kosong',s=>{s.clubs={}});
      t('tiada players',s=>{delete s.players});
      t('tiada tl',s=>{s.tl=[]});
      t('user hilang',s=>{s.user='tiada-kelab'});
      t('v salah',s=>{s.v=2});
      t('sv lebih baharu',s=>{s.sv=99});
      t('sv bukan nombor',s=>{s.sv='abc'});
      t('t bukan nombor',s=>{s.t='3'});
      out.minimum=checkSave({v:3,clubs:{}});
      out.tatasusunan=checkSave([1,2]);
      out.null=checkSave(null);
      return out}""")
    check('checkSave: simpanan baik diterima', cases['baik'] is None, cases['baik'])
    for k in ['clubs kosong', 'tiada players', 'tiada tl', 'user hilang', 'v salah', 'sv lebih baharu', 'sv bukan nombor', 't bukan nombor', 'minimum', 'tatasusunan', 'null']:
        check(f'checkSave menolak: {k}', isinstance(cases[k], str) and len(cases[k]) > 5, cases[k])
    check('mesej sv lebih baharu menyebut versi baharu', 'baharu' in (cases['sv lebih baharu'] or ''), cases['sv lebih baharu'])

    # ---- 6. Import melalui fail: tolak yang rosak, S tidak berubah, terima yang sah
    pg.evaluate("()=>{ACT.nav('saves')}")
    def snap():
        return pg.evaluate("()=>({season:S.seasonNo,t:S.t,club:S.user&&S.clubs[S.user].name,json:JSON.stringify(S).length,saveMsg:UI.saveMsg})")
    def import_file(name, data, mime='text/plain'):
        pg.evaluate("()=>{UI.saveMsg=null;ACT.nav('saves')}")
        pg.set_input_files('#impfile', files=[{'name': name, 'mimeType': mime, 'buffer': data if isinstance(data, bytes) else data.encode('utf-8')}])
        time.sleep(.6)
        return snap()
    base = snap()
    valid_text = pg.evaluate("()=>packS(true)")
    bad_cases = {
        'fail kosong': ('kosong.pksave', b''),
        'jenis salah (.png)': ('gambar.png', b'\x89PNG\r\n\x1a\n' + b'0' * 200),
        'jenis salah (.exe)': ('x.exe', b'MZ' + b'0' * 50),
        'terlalu besar (21 MB)': ('besar.pksave', b'B' + b'A' * (21 * 1024 * 1024)),
        'teks rambang': ('nota.txt', 'ini bukan simpanan langsung'),
        'JSON kosong {"v":3,"clubs":{}} (D4)': ('d4.pksave', '{"v":3,"clubs":{}}'),
        'JSON separa': ('separa.pksave', '{"v":3,"clubs":{"a":'),
        'terpotong (separuh kod sah)': ('potong.pksave', valid_text[:len(valid_text) // 2]),
        'kod B diubah': ('ubah.pksave', 'B' + valid_text[1:200] + '!!!' + valid_text[203:]),
        'sv 99': ('baharu.pksave', None),
    }
    # bina sv=99 daripada simpanan sah
    sv99 = pg.evaluate("()=>{const s=JSON.parse(JSON.stringify(S));s.sv=99;const j=JSON.stringify(s);return 'B'+LZString.compressToBase64(j)}")
    bad_cases['sv 99'] = ('baharu.pksave', sv99)
    for name, (fn, data) in bad_cases.items():
        s = import_file(fn, data)
        same = s['season'] == base['season'] and s['t'] == base['t'] and s['club'] == base['club'] and s['json'] == base['json']
        msg = s['saveMsg']
        check(f'import ditolak: {name}', msg and msg['ok'] is False and len(msg['msg']) > 5 and same, {'msg': msg, 'same': same})
    msgs = {}
    for name, (fn, data) in bad_cases.items():
        pass
    # mesej untuk kes tertentu spesifik
    s = import_file('kosong.pksave', b'')
    check('mesej fail kosong jelas', 'kosong' in s['saveMsg']['msg'].lower(), s['saveMsg'])
    s = import_file('besar.pksave', b'B' + b'A' * (21 * 1024 * 1024))
    check('mesej fail besar menyebut saiz', 'besar' in s['saveMsg']['msg'].lower(), s['saveMsg'])
    s = import_file('baharu.pksave', sv99)
    check('mesej sv 99 beritahu versi lebih baharu', 'baharu' in s['saveMsg']['msg'].lower(), s['saveMsg'])
    ok_after = pg.evaluate("()=>!!parseSave(localStorage.getItem('pk3-slot-auto')).s")
    check('autosave tidak tertimpa oleh import ditolak', ok_after)
    # input boleh dipilih semula selepas gagal (fail sama dua kali)
    s1 = import_file('d4.pksave', '{"v":3,"clubs":{}}')
    s2 = import_file('d4.pksave', '{"v":3,"clubs":{}}')
    check('fail sama boleh dipilih semula selepas ditolak', s2['saveMsg'] and s2['saveMsg']['ok'] is False, s2['saveMsg'])
    # fail sah diterima: guna simpanan LAMA (tanpa sv) sebagai fail .pksave
    pg.evaluate("()=>{UI.saveMsg=null;ACT.nav('saves')}")
    s = import_file('lama.pksave', old_b)
    check('import fail simpanan lama (tanpa sv) diterima', s['saveMsg'] and s['saveMsg']['ok'] is True and s['club'] == old_meta['club'] and s['t'] == old_meta['t'], s)
    s = import_file('baru.txt', valid_text)
    check('import fail simpanan baharu diterima (.txt)', s['saveMsg'] and s['saveMsg']['ok'] is True, s)
    # kod tampal (importText) juga ditolak jika rosak
    pg.evaluate("()=>importText('{\"v\":3,\"clubs\":{}}')")
    m = pg.evaluate("()=>UI.saveMsg")
    check('importText menolak JSON kosong tanpa TypeError', m and m['ok'] is False, m)
    # ensureState gagal -> S dipulihkan
    pg.evaluate("()=>{window.__oe=ensureState;window.__before=S;ensureState=function(){throw new Error('uji')}}")
    thrown = pg.evaluate("()=>{try{loadState(JSON.parse(JSON.stringify(S)));return 'tiada ralat'}catch(e){return e.message}}")
    same_ref = pg.evaluate("()=>{ensureState=window.__oe;return S===window.__before}")
    check('loadState pulihkan S bila ensureState gagal', thrown == 'uji' and same_ref, [thrown, same_ref])

    # ---- 7. Autosave gagal bila storan penuh
    pg.evaluate("()=>{UI.saveMsg=null;ACT.nav('home')}")
    q = pg.evaluate("""()=>{const chunk='y'.repeat(100000);let i=0;for(;i<300;i++){try{localStorage.setItem('zq-'+i,chunk)}catch(e){break}}let j=0;for(;j<3000;j++){try{localStorage.setItem('zs-'+j,'y'.repeat(1000))}catch(e){break}}
      window.__zq=[i,j];
      const before=localStorage.getItem('pk3-slot-auto');
      S.inbox.unshift({id:'zq',t:'uji',b:Array.from({length:40000},()=>Math.random().toString(36).slice(2)).join(''),cat:'tf',d:curDate(),read:false});
      let thr='tiada';try{(save(),saveFlush())}catch(e){thr=e.message}
      const el=document.getElementById('savewarn');
      const after=localStorage.getItem('pk3-slot-auto');
      return {chunks:i,thr,warnOn:!!el&&el.className==='on',visible:!!el&&getComputedStyle(el).display!=='none',txt:el?el.textContent.slice(0,160):'',autoIntact:!!parseSave(after).s,autoUnchanged:before===after}}""")
    check('storan penuh: (save(),saveFlush()) tidak melontar ralat', q['thr'] == 'tiada', q)
    check('storan penuh: bar amaran muncul', q['warnOn'] and q['visible'] and 'Autosave gagal' in q['txt'], q)
    check('storan penuh: simpanan lama kekal utuh', q['autoIntact'] and q['autoUnchanged'], q)
    shot = os.path.join(tempfile.gettempdir(), 'pk-savewarn.png')
    pg.screenshot(path=shot)
    # langkah permainan semasa storan penuh: amaran kekal, permainan tidak rosak
    step = pg.evaluate("""()=>{try{if(S.fr&&!S.fr.done){frAuto();frConfirm()}S.job.conf=Math.max(S.job.conf,80);doAdvance();closeSummary();closeModal();return {ok:true,warn:document.getElementById('savewarn').className}}catch(e){return {ok:false,err:e.message}}}""")
    check('storan penuh: Teruskan masih jalan, amaran kekal', step['ok'] and step['warn'] == 'on', step)
    # tutup -> diam 2 minit
    pg.evaluate("()=>ACT.savewarnx()")
    muted = pg.evaluate("()=>{const c=document.getElementById('savewarn').className;(save(),saveFlush());return {afterClose:c,afterSave:document.getElementById('savewarn').className}}")
    check('butang Tutup menyembunyi dan diam sementara', muted['afterClose'] == '' and muted['afterSave'] == '', muted)
    pg.evaluate("()=>{SAVEWARN.mute=0;(save(),saveFlush())}")
    on_again = pg.evaluate("()=>document.getElementById('savewarn').className")
    check('amaran muncul semula selepas tempoh diam', on_again == 'on', on_again)
    # butang Buka Save / Load
    pg.evaluate("()=>{ACT.nav('home')}")
    pg.click('#savewarn [data-act="savewarnopen"]')
    nav = pg.evaluate("()=>({view:UI.view,warn:document.getElementById('savewarn').className})")
    check('Buka Save / Load menuju skrin saves', nav['view'] == 'saves', nav)
    # pulih: kosongkan storan -> save berjaya -> amaran hilang
    rec = pg.evaluate("""()=>{const [i,j]=window.__zq;for(let k=0;k<i;k++)localStorage.removeItem('zq-'+k);for(let k=0;k<j;k++)localStorage.removeItem('zs-'+k);
      SAVEWARN.mute=0;const w=document.getElementById('savewarn');w.className='on';(save(),saveFlush());return {warn:w.className,ok:!!parseSave(localStorage.getItem('pk3-slot-auto')).s,sv:parseSave(localStorage.getItem('pk3-slot-auto')).s.sv}}""")
    check('selepas storan dikosongkan, simpanan berjaya dan amaran hilang', rec['warn'] == '' and rec['ok'] and rec['sv'] == 7, rec)

    # ---- 8. Tiada amaran palsu bila tiada permainan
    nogame = pg.evaluate("()=>{const sv=S;S=null;let r;try{(save(),saveFlush());r=document.getElementById('savewarn').className}catch(e){r='throw '+e.message}S=sv;return r}")
    check('(save(),saveFlush()) tanpa permainan tidak mencetus amaran/ralat', nogame == '', nogame)

    check('tiada pageerror sepanjang ujian', not errs, errs)
    b.close()

srv_new.terminate(); srv_old.terminate(); shutil.rmtree(tmp, ignore_errors=True)
fail = [r for r in results if not r['lulus']]
print(json.dumps({'jumlah': len(results), 'lulus': len(results) - len(fail), 'gagal': fail}, indent=1, ensure_ascii=False))
for r in results:
    print(('PASS ' if r['lulus'] else 'FAIL ') + r['ujian'])
sys.exit(1 if fail else 0)
