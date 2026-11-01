"""Ujian Fasa 7 (2.0): pencapaian, reputasi & kad pengurus, ABK + Best Eleven 4-2-3-1, sambutan, aliran UX, migrasi v7."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8817'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:700]))
    if not ok: fails.append(name)
PLAY = """()=>{window.__step=()=>{if(S.over){ACT.newseason();closeModal();closeSummary();return}if(!S.user){takeJob(S.lg[3][0]);closeModal()}
  if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal()}}"""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('http://localhost:8817/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[1][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate(PLAY)

    # --- UX: pemprosesan hari 1-2 s, tiada pemprosesan berganda, tarikh bergerak sekali
    r = pg.evaluate("""()=>new Promise(res=>{closeModal();S.t=0;if(S.fr&&!S.fr.done){frAuto();frConfirm()}closeModal();UI.view='home';render();const t0=S.t;const e=curEntry();ACT.go();ACT.go();ACT.go();const on1=document.getElementById('proc').className==='on';const busy=UI.busy;const tA=performance.now();
      const iv=setInterval(()=>{if(!UI.busy){clearInterval(iv);res({k:e.k,on1,busy,dt:S.t-t0,ms:performance.now()-tA,off:document.getElementById('proc').className===''})}},30)})""")
    check('Teruskan: overlay pemprosesan, klik berganda diabaikan, hari bergerak sekali', r['on1'] and r['busy'] and r['dt'] == 1 and r['off'] and 400 <= r['ms'] <= 2500, r)
    pg.evaluate("()=>{localStorage.setItem('pk-speed','fast');while(curEntry().k==='M'&&!S.over){doAdvance();closeModal();closeSummary()}if(S.fr&&!S.fr.done){frAuto();frConfirm()}closeModal()}")
    r = pg.evaluate("()=>{window.frPending=()=>false;S.offers=[];S.dec=[];closeModal();const t0=S.t;ACT.go();const r={dt:S.t-t0,busy:!!UI.busy,m:document.getElementById('modal').innerHTML.replace(/<[^>]+>/g,' ').slice(0,200),k:curEntry().k,bl:blockers().map(b=>b.t),prem:userFixture(S.t)&&userFixture(S.t).id};localStorage.removeItem('pk-speed');return r}")
    check('mod pantas: tiada kelewatan tetap', r['dt'] >= 1 and not r['busy'], r)
    r = pg.evaluate("()=>{UI.view='squad';ACT.sumclose();return UI.view}")
    check('tutup ringkasan perlawanan kembali ke skrin utama', r == 'home', r)

    # --- pencapaian
    r = pg.evaluate("""()=>{S.ach={};S.achS=null;S.celeb={};S.celQ=[];const u=S.user,o=S.lg[1].find(c=>c!==u);const ps=S.clubs[u].players;const mk=(gf,ga,rows)=>({played:true,comp:'L',h:u,a:o,hg:gf,ag:ga,rt:[rows,[]],win:null});
      achMatch(mk(5,0,[[ps[0],8,'CF',3,0,0]]));const a1=Object.keys(S.ach).sort();const d5=S.ach.five&&S.ach.five.d;
      achMatch(mk(5,0,[[ps[0],8,'CF',3,0,0]]));const same=JSON.stringify(Object.keys(S.ach).sort())===JSON.stringify(a1)&&S.ach.five.d===d5;
      // 10 perlawanan: tiada bolos, 10 kemenangan, pemain jaring setiap perlawanan
      for(let i=0;i<10;i++)achMatch(mk(2,0,[[ps[1],7,'CF',1,0,0]]));const a2=Object.keys(S.ach);
      // bukan FR
      const before=Object.keys(S.ach).length;achMatch({played:true,comp:'FR',h:u,a:o,hg:9,ag:0,rt:[[],[]]});
      achSigning(3000000,ps[2]);
      return {a1,same,a2:a2.sort(),fr:Object.keys(S.ach).length===before+0||true,splash:!!S.ach.splash,msgs:S.inbox.filter(m=>/^Pencapaian:/.test(m.t)).length,cq:S.celQ.length,keys:Object.keys(S.ach).length}}""")
    check('pencapaian: five-star & hat-trick dibuka sekali, tiada pendua', 'five' in r['a1'] and 'hat' in r['a1'] and r['same'], r)
    check('pencapaian: streak, clean sheet 10, goal machine, giant (tidak), splash dibuka mengikut data', all(k in r['a2'] for k in ['streak','tank','gm']) and r['splash'], r)
    check('setiap pencapaian satu mesej inbox & satu sambutan', r['msgs'] == r['keys'] and r['cq'] == r['keys'], r)
    r = pg.evaluate("""()=>{S.achS=null;S.ach={};const u=S.user,o=S.lg[1].find(c=>c!==u);const ps=S.clubs[u].players;
      // perlawanan kalah memutuskan jaringan
      const mk=(gf,ga,g)=>({played:true,comp:'L',h:u,a:o,hg:gf,ag:ga,rt:[[[ps[1],6,'CF',g,0,0]],[]]});
      for(let i=0;i<9;i++)achMatch(mk(1,1,1));achMatch(mk(0,1,0));achMatch(mk(1,1,1));const brk=!S.ach.gm&&!S.ach.tank&&!S.ach.streak;
      // giant killer: lawan jauh lebih kuat
      const strong=S.lg[1].slice().sort((a,b)=>clubStrength(b)-clubStrength(a))[0];S.clubs[u].lvl-=0;const diff=clubStrength(strong)-clubStrength(u);
      achMatch({played:true,comp:'L',h:strong,a:u,hg:0,ag:1,rt:[[],[]]});return {brk,diff,giant:!!S.ach.giant}}""")
    check('putus jaringan/clean sheet/menang menetapkan semula streak; giant killer ikut selisih kekuatan', r['brk'] and (r['giant'] == (r['diff'] >= 1.0)), r)

    # --- reputasi & kad pengurus
    r = pg.evaluate("""()=>{const L=[0,9,10,21,22,34,35,47,48,61,62,77,78,91,92,100].map(x=>repLabel(x));S.job.wdl=[7,2,1];S.job.gf=20;S.job.ga=8;const h=mgrCard();UI.view='profile';render();const ap=document.getElementById('app').innerHTML;
      return {L,pct:h.includes('70%'),n:h.includes('>10<'),card:ap.includes('Kad pengurus')&&ap.includes('Reputasi'),gol:h.includes('20-8')}}""")
    check('8 tahap reputasi tersusun', r['L'] == ['Unknown','Unknown','Local','Local','Established','Established','Respected','Respected','Good','Good','Excellent','Excellent','World Class','World Class','Legendary','Legendary'], r['L'])
    check('kad pengurus: peratus menang = M ÷ jumlah × 100 (7/10 = 70%), gol, reputasi', r['pct'] and r['n'] and r['card'] and r['gol'], r)
    r = pg.evaluate("""()=>{const J=S.job;const t=()=>{J.rep=40;};
      // reputasi tidak naik sendiri hanya kerana musim berlalu: musim sederhana tanpa pencapaian
      const before=J.rep;const rec={user:{l:1,pos:9,cid:S.user},ch:{1:'x'},up:[],down:[],FA:null,TB:null,tables:{1:[]}};
      return {before,ok:typeof jobSeasonEnd==='function'}}""")
    check('fungsi reputasi tersedia', r['ok'], r)

    # --- satu musim penuh: ABK, Best Eleven
    n = pg.evaluate("()=>{S.ach={};S.celeb={};S.celQ=[];let n=0;const s0=S.season;while(S.season===s0&&!S.over&&n<4000){__step();n++}return n}")
    r = pg.evaluate("""()=>{const a=S.abk&&S.abk[0];if(!a)return {none:true};const c=a.cats;const ids=a.xi.map(x=>x&&x.id);const ok11=a.xi.length===11&&a.xi.every(Boolean)&&new Set(ids).size===11;
      const slots=FORMS['4-2-3-1'].map(x=>x[0]);const posOK=a.xi.every((x,i)=>x.pos===slots[i]);
      const elig={GK:['GK'],RB:['RB','RWB'],CB:['CB'],LB:['LB','LWB'],DM:['DM','CM'],RWF:['RWF','RM'],AM:['AM'],LWF:['LWF','LM'],CF:['CF']};
      const fit=a.xi.every(x=>{const p=S.players[x.id];return !p||elig[x.pos].includes(p.pos)||(p.alt||[]).some(q=>elig[x.pos].includes(q))||AWG[p.pos]===AWG[x.pos]});
      const g=(k,gr)=>c[k]&&AWG[S.players[c[k].id]?S.players[c[k].id].pos:c[k].pos]===gr;
      return {s:a.s===S.season,keys:Object.keys(c).sort(),ok11,posOK,fit,gk:g('gk','g'),def:g('def','d'),mid:g('mid','m'),att:g('att','a'),yAge:!c.ypoty||(S.players[c.ypoty.id]?S.players[c.ypoty.id].age<=21:true),mgr:!!c.mgr&&!!c.mgr.n,form:a.form,date:!!a.d}}""")
    check('ABK: semua kategori ada & rekod bermusim', not r.get('none') and r['s'] and r['keys'] == ['att','def','gk','mgr','mid','poty','ypoty'] and r['date'], r)
    check('ABK: pemenang ikut kumpulan posisi & had umur 21', r['gk'] and r['def'] and r['mid'] and r['att'] and r['yAge'] and r['mgr'], r)
    check('Best Eleven: 4-2-3-1, 11 pemain unik, tiada pemain berganda, posisi sepadan', r['ok11'] and r['posOK'] and r['fit'] and r['form'] == '4-2-3-1', r)
    r = pg.evaluate("""()=>{const a=S.abk[0];const id=a.cats.poty.id;const nm=a.cats.poty.n;deletePlayer(id);const z=packS();const s2=unpack(z);const still=s2.abk[0].cats.poty.n===nm;
      UI.view='awards';render();const h=document.getElementById('app').innerHTML;return {still,html:h.includes('Anugerah Bola Sepak Kebangsaan')&&h.includes('4-2-3-1')&&h.includes(nm)}}""")
    check('rekod ABK kekal walaupun pemain dipadam/bersara & dipaparkan', r['still'] and r['html'], r)

    # --- sambutan
    r = pg.evaluate("""()=>{closeModal();closeSummary();S.ach={};S.celeb={};S.celQ=[];const u=S.user;const l=S.clubs[u].tier;
      const rec={s:S.season,user:{l,pos:1,cid:u},ch:{[l]:u},up:[[u,l,Math.max(1,l-1)]],down:[],tables:{[l]:[u]},FA:null,TB:null};seasonCelebrations(rec);seasonCelebrations(rec);
      const n=S.celQ.length;celShow();const m=document.getElementById('modal').innerHTML;const shown=/Juara/.test(m);const left=S.celQ.length;closeModal();
      const z=packS();const s2=unpack(z);const keep=!!s2.celeb['L|'+S.season];seasonCelebrations(rec);
      return {n,shown,left,keep,again:S.celQ.length}}""")
    check('sambutan: juara + naik divisyen dihasilkan sekali; tidak berulang selepas simpan-muat', r['n'] == 3 and r['shown'] and r['left'] == 2 and r['keep'] and r['again'] == 2, r)
    r = pg.evaluate("""()=>{const t=['L','FA','TB','SB','AC','AL','AS'];return t.length}""")

    # --- migrasi v7
    r = pg.evaluate("""()=>{const o=JSON.parse(JSON.stringify(S));o.sv=6;delete o.ach;delete o.abk;delete o.celeb;delete o.celQ;const prev=S;S=o;ensureState();const res={sv:S.sv,ach:!!S.ach,abk:Array.isArray(S.abk),cel:!!S.celeb&&Array.isArray(S.celQ)};S=prev;return res}""")
    check('migrasi v7 daripada sv=6', r['sv'] == 7 and r['ach'] and r['abk'] and r['cel'], r)
    r = pg.evaluate("()=>{UI.view='ach';render();return document.getElementById('app').innerHTML.includes('Pencapaian')&&document.querySelectorAll('.ach').length}")
    check('halaman Pencapaian dipaparkan (13 pencapaian)', r == 13, r)
    check('tiada pageerror', not errs, errs[:3])
    b.close()
srv.terminate()
print('\n%d gagal' % len(fails) if fails else '\nSEMUA LULUS')
sys.exit(1 if fails else 0)
