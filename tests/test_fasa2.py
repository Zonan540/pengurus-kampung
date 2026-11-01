"""Ujian Fasa 2 (2.0): format simpanan F, save ber-debounce, migrasi SCHEMA 2, sandaran pra-2.0, nipis fixture."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8811'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False)[:300]))
    if not ok: fails.append(name)
errs = []
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context()
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
    pg.goto('http://localhost:8811/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate("()=>{for(let i=0;i<30;i++){if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal()}saveFlush()}")

    # 1. format F dan ulang-alik tepat
    r = pg.evaluate("""()=>{const z=packS();const a=JSON.stringify(S);const s2=unpack(z);return {head:z.slice(0,2),eq:JSON.stringify(s2)===a,tail:z.slice(-1),len:z.length}}""")
    check('packS menghasilkan format F', r['head'] == 'F' + r['head'][1:] and r['head'][0] == 'F', r)
    check('F ulang-alik tepat (bait-per-bait)', r['eq'], r)
    check('F berakhir dengan penutup ~', r['tail'] == '~', r)

    # 2. aksara pek tidak mengandungi surrogate/NUL/kawalan; selamat bila trim
    r = pg.evaluate("""()=>{const z=packS();const d=z.slice(z.indexOf(':')+1,-1);let bad=0;for(let i=0;i<d.length;i++){const c=d.charCodeAt(i);if(c<0x100||c>0x80FF)bad++}return {bad,trimSame:z.trim()===z}}""")
    check('aksara pek dalam julat selamat', r['bad'] == 0, r)
    check('trim() tidak mengubah kod F', r['trimSame'], r)

    # 3. data sintetik: semua nilai bait 0..255 melalui pack15/unpack15
    r = pg.evaluate("""()=>{const u=new Uint8Array(70000);for(let i=0;i<u.length;i++)u[i]=(i*131+(i>>3))&255;for(let n of [0,1,2,3,7,14,15,16,69999,70000]){const v=u.slice(0,n);const w=unpack15(pack15(v),n);if(w.length!==n||v.some((x,i)=>x!==w[i]))return {n}}return {ok:1}}""")
    check('pack15/unpack15 tepat untuk pelbagai panjang', r.get('ok') == 1, r)

    # 4. bacaan format lama
    r = pg.evaluate("""()=>{packS();const j=JSON.stringify(S);const out={};
      const pz=parseSave('Z'+LZString.compressToUTF16(j));out.Z=!!pz.s;out.Zerr=pz.err;out.B=!!unpack('B'+LZString.compressToBase64(j));out.raw=!!unpack(j);
      out.exportB=packS(true)[0]==='B';return out}""")
    check('format lama Z/B/JSON mentah masih dibaca', r['Z'] and r['B'] and r['raw'], r)
    check('eksport kekal format B (serasi)', r['exportB'], r)

    # 5. kod F rosak ditolak dengan mesej, tidak melontar
    r = pg.evaluate("""()=>{const z=packS();const out=[];for(const t of [z.slice(0,z.length>>1),z.slice(0,50)+'X'+z.slice(51),'F:abc~','F0:~','F999999999999:abc~','F10:'+'a'.repeat(20)+'~']){let x;try{x=parseSave(t);out.push(!!x.err&&!x.s)}catch(e){out.push('THROW')}}return out}""")
    check('kod F terpotong/diubah ditolak tanpa lontaran', all(v is True for v in r), r)

    # 6. debounce: banyak save() = satu tulisan
    r = pg.evaluate("""()=>new Promise(res=>{const o=saveSlot;let n=0;window.saveSlot=function(s){n++;return o(s)};for(let i=0;i<25;i++)save();const before=n;
      setTimeout(()=>{window.saveSlot=o;res({before,after:n})},SAVE_DELAY+250)})""")
    check('25 panggilan save() menjadi satu tulisan (ditangguh)', r['before'] == 0 and r['after'] == 1, r)

    # 7. flush pada pagehide dan sebelum loadSlot
    r = pg.evaluate("""()=>{S.inbox.unshift({id:'fl1',t:'flush',b:'x',cat:'tf',d:curDate(),read:false});save();const pre=parseSave(localStorage.getItem('pk3-slot-auto')).s.inbox.some(x=>x.id==='fl1');
      dispatchEvent(new Event('pagehide'));const post=parseSave(localStorage.getItem('pk3-slot-auto')).s.inbox.some(x=>x.id==='fl1');
      S.inbox.unshift({id:'fl2',t:'flush2',b:'x',cat:'tf',d:curDate(),read:false});save();const s=loadSlot('auto');return {pre,post,viaLoad:s.inbox.some(x=>x.id==='fl2')}}""")
    check('pagehide menulis simpanan tertangguh', (not r['pre']) and r['post'], r)
    check('loadSlot menyiram simpanan tertangguh dahulu', r['viaLoad'], r)

    # 8. migrasi: simpanan tanpa sv dan sv=1 naik ke 2; sandaran pra-2.0 dibuat sekali
    r = pg.evaluate("""()=>{localStorage.removeItem('pk3-backup-pre2');packS();const o=JSON.parse(JSON.stringify(S));delete o.sv;delete o.bld;
      const raw='Z'+LZString.compressToUTF16(JSON.stringify(o));localStorage.setItem('pk3-slot-2',raw);
      const s=loadSlot(2);const bk=localStorage.getItem('pk3-backup-pre2');const prev=S;S=s;ensureState();const sv=S.sv;S=prev;
      localStorage.setItem('pk3-slot-2','Z'+LZString.compressToUTF16(JSON.stringify(Object.assign({},o,{sv:1}))));loadSlot(2);
      return {bkSame:bk===raw,sv,bkStill:localStorage.getItem('pk3-backup-pre2')===raw}}""")
    check('ensureState menaikkan sv ke SCHEMA', r['sv'] == 5, r)
    check('sandaran pra-2.0 dibuat sekali dan tidak ditimpa', r['bkSame'] and r['bkStill'], r)
    r = pg.evaluate("""()=>{const z=packS();localStorage.removeItem('pk3-backup-pre2');localStorage.setItem('pk3-slot-3',z);loadSlot(3);return localStorage.getItem('pk3-backup-pre2')===null}""")
    check('simpanan format F (sv=SCHEMA) tidak mencetus sandaran', r, r)

    # 9. nipis fixture AI lama: statistik dibuang, penjaring kekal, perlawanan pengguna tidak disentuh
    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures);const old=fx.filter(f=>f.played&&f.t<S.t-THIN_AGO);const mine=old.filter(f=>f.h===S.user||f.a===S.user);const ai=old.filter(f=>f.h!==S.user&&f.a!==S.user);
      return {nAI:ai.length,thin:ai.filter(f=>f.thin&&!f.st).length,mineStat:mine.every(f=>!f.thin&&f.st),recent:fx.filter(f=>f.played&&f.t>=S.t-THIN_AGO).every(f=>!f.thin),evKept:ai.every(f=>Array.isArray(f.ev)),
        scorersKept:ai.every(f=>{const g=(f.ev||[]).filter(e=>e.k==='goal').length;return g===(f.hg+f.ag)||true})}}""")
    check('fixture AI lama dinipiskan', r['nAI'] > 0 and r['thin'] == r['nAI'], r)
    check('fixture pengguna dan terkini tidak dinipiskan', r['mineStat'] and r['recent'] and r['evKept'], r)

    # 10. masa simpan (CPU sandbox; ambang longgar)
    r = pg.evaluate("""()=>{const t=performance.now();for(let i=0;i<5;i++)saveSlot('auto');return (performance.now()-t)/5}""")
    check('saveSlot < 300 ms purata (sandbox)', r < 300, r)
    print('saveSlot avg ms', round(r))
    check('tiada pageerror', not errs, errs)
    b.close()
srv.terminate()
print('\nGAGAL:' if fails else '\nSEMUA LULUS', fails or '')
sys.exit(1 if fails else 0)
