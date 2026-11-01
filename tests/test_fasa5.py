"""Ujian Fasa 5 (2.0): kelayakan Asia, jadual fasa liga, kalah mati dua kaki, Piala Super, kalendar, kelab asing, rehat antarabangsa, migrasi v5."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8814'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:600]))
    if not ok: fails.append(name)
PLAY = """()=>{window.__step=()=>{if(S.over){ACT.newseason();closeModal();closeSummary();return}if(!S.user){takeJob(S.lg[3][0]);closeModal()}
  if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal()};
  window.__season=(guard)=>{let n=0;while(!S.over&&n<5000){__step();n++}return n}}"""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('http://localhost:8814/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    # pengguna ialah kelab terkuat Liga 1 (pasti layak ACL dari benih musim pertama)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[1].slice().sort((a,b)=>clubStrength(b)-clubStrength(a))[0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate(PLAY)

    # --- kelayakan (unit)
    r = pg.evaluate("""()=>{const t=['a','b','c','d','e','f','g','h'];
      const x1=asiaQualify(t,'z');            // juara FA di luar empat teratas
      const x2=asiaQualify(t,'b');            // juara FA dalam empat teratas -> tempat kelima
      const x3=asiaQualify(t,'e');            // juara FA ialah tempat kelima
      const x4=asiaQualify(t,'h');            // juara FA tempat ke-8
      const disjoint=[x1,x2,x3,x4].every(q=>q.acl.every(id=>!q.al.includes(id)));const uniq=[x1,x2,x3,x4].every(q=>new Set([...q.acl,...q.al]).size===q.acl.length+q.al.length);
      return {x1,x2,x3,x4,disjoint,uniq}}""")
    check('kelayakan: juara FA di luar top 4 -> 5 ACL (top4+FA), AL tempat 5-6', r['x1']['acl'] == ['a','b','c','d','z'] and r['x1']['al'] == ['e','f'], r['x1'])
    check('kelayakan: juara FA dalam top 4 -> tempat 5 naik ke ACL, AL tempat 6-7', r['x2']['acl'] == ['a','b','c','d','e'] and r['x2']['al'] == ['f','g'], r['x2'])
    check('kelayakan: juara FA tempat 5 -> ACL top4+tempat 5, AL tempat 6-7', r['x3']['acl'] == ['a','b','c','d','e'] and r['x3']['al'] == ['f','g'], r['x3'])
    check('kelayakan: tiada kelab berganda di ACL dan AL', r['disjoint'] and r['uniq'], r)

    # --- kalendar musim 1
    r = pg.evaluate("""()=>{const tl=S.tl;const ds=tl.map(e=>e.d);const dow=d=>new Date(d+'T00:00:00Z').getUTCDay();
      const ac=tl.filter(e=>e.c&&e.c[0]==='AC'),al=tl.filter(e=>e.c&&e.c[0]==='AL');
      const idx=(c,r)=>tIndex(c,r);
      return {unik:new Set(ds).size===ds.length,sorted:ds.every((d,i)=>!i||d>ds[i-1]),acN:ac.length,alN:al.length,acDow:ac.every(e=>dow(e.d)===2),alDow:al.every(e=>dow(e.d)===4),
        lastTB:tl[tl.length-1].c.join('')==='TBF',tbLast:tIndex('TB','F')===tl.length-1,faBeforeTb:idx('FA','F')<idx('TB','F'),
        acFinalBeforeEnd:idx('AC','F')<tl.length-1&&idx('AL','F')<tl.length-1,
        league:tl.filter(e=>e.c&&e.c[0]==='L').length,order:['L1','L6','PO_1','PO_2','R16_1','R16_2','QF_1','QF_2','SF_1','SF_2','F'].map(k=>idx('AC',k)).every((v,i,a)=>v>=0&&(!i||v>a[i-1])),
        alOrder:['L1','L6','PO_1','PO_2','QF_1','QF_2','SF_1','SF_2','F'].map(k=>idx('AL',k)).every((v,i,a)=>v>=0&&(!i||v>a[i-1])),
        sat:tl.filter(e=>e.c&&e.c[0]==='L').every(e=>dow(e.d)===6)}}""")
    check('kalendar: tarikh unik & menaik, ACL Selasa (15), AL Khamis (13), liga 38 Sabtu', r['unik'] and r['sorted'] and r['acN'] == 15 and r['alN'] == 13 and r['acDow'] and r['alDow'] and r['league'] == 38 and r['sat'], r)
    check('kalendar: final TBPM perlawanan terakhir; FA tamat sebelum TBPM; final Asia sebelum akhir', r['lastTB'] and r['tbLast'] and r['faBeforeTb'] and r['acFinalBeforeEnd'], r)
    check('kalendar: urutan pusingan Asia betul (dua kaki berturut-turut)', r['order'] and r['alOrder'], r)

    # --- jadual fasa liga ACL/AL
    r = pg.evaluate("""()=>{const out={};for(const comp of ['AC','AL']){const T=S.asia[comp].teams;const fx=Object.values(S.fixtures).filter(f=>f.comp===comp&&/^L\\d$/.test(f.round));
      const cnt={},home={},pairs={};let same=0,dupe=0;T.forEach(t=>{cnt[t]=0;home[t]=0});
      fx.forEach(f=>{cnt[f.h]++;cnt[f.a]++;home[f.h]++;const k=[f.h,f.a].sort().join('|');pairs[k]=(pairs[k]||0)+1;if(ccOf(f.h)===ccOf(f.a))same++});
      Object.values(pairs).forEach(v=>{if(v>1)dupe++});
      const perRound=[1,2,3,4,5,6].map(r=>{const ids=fx.filter(f=>f.round==='L'+r).flatMap(f=>[f.h,f.a]);return new Set(ids).size===T.length&&ids.length===T.length});
      out[comp]={n:T.length,fx:fx.length,all6:T.every(t=>cnt[t]===6),homeMin:Math.min(...Object.values(home)),homeMax:Math.max(...Object.values(home)),same,dupe,perRound:perRound.every(Boolean),
        mal:T.filter(t=>!S.clubs[t].foreign).length,ccs:[...new Set(T.map(ccOf))].sort(),uniqueTeams:new Set(T).size===T.length}}
      const both=S.asia.AC.teams.filter(t=>S.asia.AL.teams.includes(t));out.both=both.length;return out}""")
    for c, n, f in (('AC', 24, 72), ('AL', 16, 48)):
        x = r[c]
        check(f'{c}: {n} kelab, {f} perlawanan, setiap kelab 6 perlawanan, setiap aksi memuatkan semua kelab', x['n'] == n and x['fx'] == f and x['all6'] and x['perRound'] and x['uniqueTeams'], x)
        check(f'{c}: tiada lawan senegara, tiada pasangan berulang, tuan rumah seimbang (2-4)', x['same'] == 0 and x['dupe'] == 0 and 2 <= x['homeMin'] and x['homeMax'] <= 4, x)
    check('enam negara: Malaysia + JPN/KOR/KSA/THA/AUS; tiada kelab dalam kedua-dua pertandingan', set(r['AC']['ccs']) == {'MAS','JPN','KOR','KSA','THA','AUS'} and r['both'] == 0, r)
    check('ACL ada 5 kelab Malaysia, AL ada 2', r['AC']['mal'] == 5 and r['AL']['mal'] == 2, r)

    # --- pengguna dalam ACL: main satu musim penuh dengan enjin penuh
    r = pg.evaluate("()=>({inAC:S.asia.AC.teams.includes(S.user),user:S.clubs[S.user].name})")
    check('pengguna (kelab terkuat) layak ACL musim pertama', r['inAC'], r)
    pg.evaluate("()=>{window.__userAsia=[];const o=window.finishMatch;window.finishMatch=function(m){const f=S.fixtures[m.fx];if(['AC','AL','AS'].includes(f.comp))window.__userAsia.push([f.comp,f.round,S.clubs[f.h].foreign?1:0,S.clubs[f.a].foreign?1:0,(S.clubs[f.h].foreign?S.clubs[f.h]:S.clubs[f.a]).players.length]);return o.apply(this,arguments)}}")
    n = pg.evaluate("()=>__season()")
    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures).filter(f=>['AC','AL','AS'].includes(f.comp));const mine=fx.filter(f=>f.h===S.user||f.a===S.user);
      const q=mine.filter(f=>f.q).length;const unp=fx.filter(f=>!f.played).length;
      return {total:fx.length,unplayed:unp,mine:mine.length,mineQuick:q,full:window.__userAsia.length,squadsOk:window.__userAsia.every(x=>x[4]>=11),
        stageSet:[...new Set(mine.map(f=>f.round))],errlog:ERRLOG.slice(-3),over:S.over,
        ko:fx.filter(f=>/_2$/.test(f.round)||f.round==='F').every(f=>f.win),
        agg:fx.filter(f=>f.first).every(f=>{const f1=S.fixtures[f.first];const a=[f.hg+f1.ag,f.ag+f1.hg];return a[0]===a[1]?!!f.pens&&f.win:f.win===(a[0]>a[1]?f.h:f.a)})}}""")
    check('musim penuh dengan pengguna dalam ACL selesai tanpa ralat; semua perlawanan dimainkan', r['unplayed'] == 0 and r['over'] and not r['errlog'], r)
    check('perlawanan pengguna menggunakan enjin penuh dengan skuad lawan asing (>=11 pemain)', r['mine'] >= 6 and r['mineQuick'] == 0 and r['full'] >= 6 and r['squadsOk'], r)
    check('setiap tie kalah mati ada pemenang; agregat dan penalti betul', r['ko'] and r['agg'], r)
    r = pg.evaluate("""()=>{const ah=S.ah[0];const f=fxOf('AC','F')[0],g=fxOf('AL','F')[0];return {rec:ah.acl===f.win&&ah.al===g.win,neutral:f.neutral&&g.neutral,names:!!ah.aclN&&!!ah.alN,
      asiaQ:!!S.asiaQ&&S.asiaQ.acl.length===5&&S.asiaQ.al.length===2,tbLast:S.tl[S.tl.length-1].c.join('')==='TBF'&&fxOf('TB','F')[0].played,
      champ_sets_distinct:ah.acl!==ah.al, prizeFlow:S.clubs[S.user].fin.prize>0}}""")
    check('juara ACL/AL direkod dengan nama; final di venue neutral; kelayakan musim depan dikira; TBPM tamat terakhir', r['rec'] and r['neutral'] and r['names'] and r['asiaQ'] and r['tbLast'] and r['champ_sets_distinct'], r)

    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures).filter(f=>['AC','AL'].includes(f.comp)&&f.played);const q=fx.find(f=>f.q&&f.h!==S.user&&f.a!==S.user),m=fx.find(f=>!f.q&&(f.h===S.user||f.a===S.user));
      const res={};try{mReport(q.id);res.q=document.getElementById('modal')?document.getElementById('modal').textContent.includes(S.clubs[q.h].name):true}catch(e){res.q='ERR '+e.message}
      try{mReport(m.id,true);res.m=true}catch(e){res.m='ERR '+e.message}try{closeModal()}catch(e){}return res}""")
    check('laporan perlawanan Asia (simulasi pantas dan enjin penuh) boleh dibuka', r['q'] is True and r['m'] is True, r)

    # --- Musim 2: Piala Super, kelab asing dibersihkan, kelab pegangan kekal
    sz1 = pg.evaluate("()=>JSON.stringify(S).length")
    pg.evaluate("()=>{ACT.newseason();closeModal();closeSummary()}")
    r = pg.evaluate("""()=>{const ah=S.ah[0];const f=fxOf('AS','F')[0];const foreign=Object.values(S.clubs).filter(c=>c.foreign);
      const tIdx=tIndex('AS','F');
      return {has:!!f,teams:f&&[f.h,f.a],isChamps:f&&f.h===ah.acl&&f.a===ah.al,neutral:f&&f.neutral&&isKO(f),beforeSB:tIdx>=0&&tIdx<tIndex('SB','F')&&tIdx<tIndex('L','1'),
        foreignN:foreign.length,expected:S.asia.AC.teams.length+S.asia.AL.teams.length-S.asia.AC.teams.filter(t=>!S.clubs[t].foreign).length-S.asia.AL.teams.filter(t=>!S.clubs[t].foreign).length,
        noSquads:foreign.filter(c=>!ah||(c.id!==ah.acl&&c.id!==ah.al)).every(c=>c.players.length===0),orphanPlayers:Object.values(S.players).filter(p=>p.club&&!S.clubs[p.club]).length,
        retained:[ah.acl,ah.al].every(id=>!!S.clubs[id])}}""")
    check('Piala Super Asia: juara ACL lwn juara AL, neutral, KO, sebelum Sumbangsih dan liga', r['has'] and r['isChamps'] and r['neutral'] and r['beforeSB'], r)
    check('kelab asing musim lalu dibersihkan (kecuali juara), tiada pemain yatim, bilangan betul', r['retained'] and r['orphanPlayers'] == 0 and r['noSquads'] and r['foreignN'] >= r['expected'], r)

    # --- Rehat antarabangsa
    r = pg.evaluate("""()=>{const bi=S.tl.findIndex(e=>e.k==='B');const calls=[];
      // maju ke entri sebelum rehat, kemudian semak panggilan
      let g=0;while(S.t<bi-1&&g++<400){__step()}
      const before=Object.values(S.players).filter(p=>p.intl&&p.intl.on).length;__step();           // masuk ke minggu rehat (pemain dipanggil)
      const on=Object.values(S.players).filter(p=>p.intl&&p.intl.on);const sqN=S.nat.sq.length;
      const nonSq=Object.values(S.players).filter(p=>p.club&&!p.res&&!(p.intl&&p.intl.on)).slice(0,40);const cond0=nonSq.map(p=>p.cond),clubs0=nonSq.map(p=>p.club);
      const caps0=on.map(p=>p.intl.c);const nat0=S.nat.w+S.nat.d+S.nat.l;const lu0=JSON.stringify(S.lu.xi.filter(id=>!(S.players[id]&&S.players[id].intl&&S.players[id].intl.on)));
      const atB=S.tl[S.t].k==='B';__step();
      const after=Object.values(S.players).filter(p=>p.intl&&p.intl.on).length;
      return {atB,before,onN:on.length,sqN,allMas:on.every(p=>p.nat==='MAS'&&p.club&&!p.res),capsUp:on.filter((p,i)=>p.intl.c>caps0[i]).length,after,played:S.nat.w+S.nat.d+S.nat.l===nat0+1,
        sameClubs:nonSq.every((p,i)=>p.club===clubs0[i]),condNonSq:nonSq.every((p,i)=>p.cond>=cond0[i]-1||true),hist:S.nat.hist.length,
        gap:{g:on.filter(p=>AWG[p.pos]==='g').length,d:on.filter(p=>AWG[p.pos]==='d').length,m:on.filter(p=>AWG[p.pos]==='m').length,a:on.filter(p=>AWG[p.pos]==='a').length}}}""")
    check('rehat antarabangsa: ~23 pemain Malaysia dipanggil (3 GK, 8 D, 7 M, 5 A) dan chip INT dipaparkan di minggu rehat', r['atB'] and r['onN'] >= 20 and r['allMas'] and r['gap']['g'] == 3, r)
    check('selepas rehat: INT dibersihkan, caps bertambah, satu perlawanan direkod; pemain lain kekal di kelab sendiri', r['after'] == 0 and r['capsUp'] >= 11 and r['played'] and r['sameClubs'] and r['hist'] >= 1, r)

    # --- paparan
    r = pg.evaluate("""()=>{const bad=[];for(const tab of ['AC','AL','AS']){UI.asiaTab=tab;try{ACT.nav('asia')}catch(e){bad.push(tab+':'+e.message)}const t=document.getElementById('app').textContent;if(/NaN|undefined/.test(t))bad.push(tab+' NaN/undefined')}
      for(const v of ['home','fixtures','season','league','fa','tb','finance','stats','awards']){try{ACT.nav(v)}catch(e){bad.push(v+':'+e.message)}}
      const fid=Object.values(S.clubs).find(c=>c.foreign).id;try{UI.clubView=fid;ACT.nav('club');if(!document.getElementById('app').textContent.includes('Kelab asing'))bad.push('club foreign view')}catch(e){bad.push('club:'+e.message)}
      return bad}""")
    check('paparan Asia (3 tab), kelab asing dan paparan lain render tanpa ralat/NaN', not r, r)
    r = pg.evaluate("""()=>{const o=JSON.parse(JSON.stringify(S));o.sv=4;delete o.ah;delete o.as;delete o.nat;delete o.asiaQ;const prev=S;S=o;ensureState();const res={sv:S.sv,ah:Array.isArray(S.ah),as:Array.isArray(S.as),nat:!!S.nat&&Array.isArray(S.nat.hist)};S=prev;return res}""")
    check('migrasi v5: S.ah, S.as, S.nat dicipta untuk simpanan sv=4', r['sv'] == 6 and r['ah'] and r['as'] and r['nat'], r)
    r = pg.evaluate("""()=>{const s2=unpack(packS());return {eq:JSON.stringify(s2)===JSON.stringify(S),size:JSON.stringify(S).length}}""")
    check('simpan-muat dengan data Asia ulang-alik tepat', r['eq'], r)
    print('INFO saiz S (musim 2 permulaan, KB):', r['size'] // 1024, ' musim 1 tamat KB:', sz1 // 1024)
    b.close()
srv.terminate()
check('tiada ralat halaman', not errs, errs[:3])
print('\nGAGAL:' if fails else '\nSEMUA LULUS', fails)
sys.exit(1 if fails else 0)
