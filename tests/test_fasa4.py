"""Ujian Fasa 4 (2.0): kalendar piala, TBPM knockout, Piala Sumbangsih, warna/label, label jadual liga, ekonomi & stadium."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8813'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:500]))
    if not ok: fails.append(name)
PLAY = """()=>{window.__play=(target)=>{let n=0;while(S.seasonNo<target&&n<4000){if(S.over){ACT.newseason();closeModal();closeSummary();n++;continue}if(!S.user){takeJob(S.lg[3][0]);closeModal()}
  if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal();n++}return 'ok'};
  window.__season=()=>{let n=0;const s0=S.seasonNo;while(!S.over&&n<4000){if(!S.user){takeJob(S.lg[3][0]);closeModal()}if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal();n++}return 'ok'}}"""
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('http://localhost:8813/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate(PLAY)

    # --- Kalendar (musim 1)
    r = pg.evaluate("""()=>{const idx=(c,rd)=>tIndex(c,rd);const tl=S.tl;const lg=n=>tIndex('L',n);
      const faF=idx('FA','F'),tbF=idx('TB','F');
      const cupAfterLeague=[...Object.entries(FA_AFTER).map(([r,rd])=>['FA',rd,+r]),...Object.entries(TB_AFTER).map(([r,rd])=>['TB',rd,+r])].every(([c,rd,r])=>idx(c,rd)>lg(r)&&idx(c,rd)<lg(r+1>38?38:r+1)+1);
      const midweek=tl.filter(e=>e.c&&['FA','TB','SB'].includes(e.c[0])&&e.c[1]!=='F'||e.c&&e.c[0]==='TB'&&e.c[1]==='F').every(e=>new Date(e.d+'T00:00:00Z').getUTCDay()===3);
      const dup=new Set(tl.map(e=>e.d)).size===tl.length;
      return {faF,tbF,fa_before_tb:faF<tbF,cupAfterLeague,midweek,dup,noGroups:!tl.some(e=>e.c&&/^(G\\d|QF1|QF2)$/.test(e.c[1])),fmt:S.tb.fmt,sb:tIndex('SB','F'),sbFx:fxOf('SB','F').length}}""")
    check('FA tamat sebelum TBPM', r['fa_before_tb'], r)
    check('semua piala hari Rabu, tarikh unik, susunan selepas pusingan liga betul', r['midweek'] and r['dup'] and r['cupAfterLeague'], r)
    check('format TBPM baharu: knockout tanpa peringkat kumpulan', r['fmt'] == 'ko' and r['noGroups'], r)
    check('Piala Sumbangsih tiada pada musim pertama', r['sb'] < 0 and r['sbFx'] == 0, r)
    r = pg.evaluate("""()=>({r16:fxOf('TB','R16').length,qf:fxOf('TB','QF').length,sf1:fxOf('TB','SF1').length,sf2:fxOf('TB','SF2').length,
      part:S.tb.part.length,uniq:new Set(fxOf('TB','R16').flatMap(f=>[f.h,f.a])).size,ko:fxOf('TB','R16').every(f=>isKO(f))})""")
    check('TBPM Pusingan 16: 8 undian, 16 kelab unik, semua knockout', r['r16'] == 8 and r['uniq'] == 16 and r['ko'] and r['part'] == 16, r)
    r = pg.evaluate("()=>(__season(),{over:S.over})")
    r = pg.evaluate("""()=>{const q=Object.values(S.fixtures).filter(f=>f.comp==='TB');const by=rd=>q.filter(f=>f.round===rd);
      const allWin=q.every(f=>f.played&&(f.round==='SF1'||f.win));
      const tieOK=by('SF2').every(f=>{const f1=S.fixtures[f.first];const aH=f.hg+f1.ag,aA=f.ag+f1.hg;return f.win===(aH>aA?f.h:aH<aA?f.a:f.win)});
      const fin=by('F')[0];
      return {counts:['R16','QF','SF1','SF2','F'].map(x=>by(x).length),allWin,tieOK,champ:fin&&fin.win,neutral:fin&&fin.neutral,
        prize:S.clubs[fin.win].fin?0:0,pending:q.filter(f=>!f.played).length,faF:fxOf('FA','F')[0].played,rec:S.honours[0].TB===fin.win,recFA:S.honours[0].FA===fxOf('FA','F')[0].win}}""")
    check('TBPM knockout: 8/4/2/2/1 perlawanan, semua ada pemenang, final neutral, direkod', r['counts'] == [8, 4, 2, 2, 1] and r['allWin'] and r['tieOK'] and r['neutral'] and r['rec'] and r['recFA'] and r['pending'] == 0, r)

    # --- Musim 2: Sumbangsih
    pg.evaluate("()=>{ACT.newseason();closeModal();closeSummary()}")
    r = pg.evaluate("""()=>{const f=fxOf('SB','F')[0];const h=S.honours[0];const e=S.tl[tIndex('SB','F')];const first=S.tl.findIndex(x=>x.k==='M');
      return {has:!!f,neutral:f&&f.neutral,ko:f&&isKO(f),ch:f&&f.h===h.ch[1],other:f&&f.a!==f.h&&(f.a===h.FA||h.FA===h.ch[1]),tw:e&&e.tw,isFirstMatch:tIndex('SB','F')===first,
        frSlots:S.tl.filter(x=>x.fr).length,beforeLeague:tIndex('SB','F')<tIndex('L',1),lastPre:S.tl[tIndex('SB','F')+1].k==='M'&&S.tl[tIndex('SB','F')+1].c[0]==='L'||true}}""")
    check('Sumbangsih: juara liga lwn juara FA (atau naib), neutral, KO, sebelum liga', r['has'] and r['neutral'] and r['ko'] and r['ch'] and r['other'] and r['beforeLeague'], r)
    check('slot persahabatan pra-musim masih >= 3', r['frSlots'] >= 3, r)
    r = pg.evaluate("""()=>{const f=fxOf('SB','F')[0];S.t=tIndex('SB','F');const st0=Object.values(S.players).reduce((a,p)=>a+p.st.L.ap+p.st.FA.ap+p.st.TB.ap,0);
      simFixture(f);postEntry(S.tl[S.t],S.t);const st1=Object.values(S.players).reduce((a,p)=>a+p.st.L.ap+p.st.FA.ap+p.st.TB.ap,0);
      return {played:f.played,win:!!f.win,rec:S.sb&&S.sb[0]&&S.sb[0].w===f.win&&S.sb[0].s===S.season,noStats:st0===st1,et:!!(f.et||f.pens||f.hg!==f.ag)}}""")
    check('Sumbangsih dimainkan: ada pemenang (masa tambahan/penalti), direkod, tidak masuk statistik liga', r['played'] and r['win'] and r['rec'] and r['noStats'], r)
    pg.evaluate("()=>{S.t=0}")

    # --- Warna & paparan
    r = pg.evaluate("""()=>{const out={};for(const c of ['L','FA','TB','SB','FR']){const el=document.createElement('div');el.innerHTML=compChip(c);document.body.appendChild(el);const ch=el.firstChild;out[c]=getComputedStyle(ch).borderTopColor;el.remove()}return out}""")
    check('setiap pertandingan ada warna chip berbeza', len(set(r.values())) == 5, r)
    r = pg.evaluate("""()=>{const bad=[];for(const v of ['home','fixtures','league','fa','tb','season','finance']){try{ACT.nav(v)}catch(e){bad.push(v+':'+e.message)}}return bad}""")
    check('paparan utama render tanpa ralat (format baharu)', not r, r)
    r = pg.evaluate("""()=>{ACT.nav('tb');return document.getElementById('app').textContent.includes('Pusingan 16')&&!document.getElementById('app').textContent.includes('Undian kumpulan')}""")
    check('halaman TBPM format knockout', r, r)

    # --- Label jadual liga (matematik mata maksimum)
    r = pg.evaluate("""()=>{const mk=(pts,p)=>({id:'x'+pts+'_'+p,p,pts});const t=[];
      // 20 kelab, 38 perlawanan; pemuncak 100 mata, kedua 60 (mx=60+3*4=72 <100)
      for(let i=0;i<20;i++)t.push({id:'c'+i,p:37,pts:100-i*5});
      const a=tableLabels(1,t);
      const t2=t.map((r,i)=>i===1?{...r,pts:98}:r);const b=tableLabels(1,t2); // kedua 98+3=101 >=100, J belum pasti
      const t3=t.map(r=>({...r,p:0,pts:0}));const c=tableLabels(1,t3);
      return {J:a.c0&&a.c0[0],noJ2:!b.c0||b.c0[0]!=='J',empty:Object.keys(c).length,R:Object.values(a).filter(x=>x[0]==='R').length,acl:Object.values(a).filter(x=>x[0]==='ACL').length,al:Object.values(a).filter(x=>x[0]==='AL').length,a:Object.fromEntries(Object.entries(a).map(([k,v])=>[k,v[0]]))}}""")
    check('label J hanya bila pasti; tiada label pada awal musim', r['J'] == 'J' and r['noJ2'] and r['empty'] == 0, r)
    check('label R/ACL/AL dikira dari kedudukan terkunci (3 R, 3 ACL, 2 AL)', r['R'] == 3 and r['acl'] == 3 and r['al'] == 2, r)
    r = pg.evaluate("""()=>{const l=1;const t=leagueTable(l);Object.values(S.fixtures).filter(f=>f.comp==='L'&&f.lg===l&&!f.played).forEach(simFixture);S.t=S.tl.length-1;
      const LB=tableLabels(l,leagueTable(l));const v=Object.values(LB).map(x=>x[0]);UI.lgView=1;ACT.nav('league');const html=document.getElementById('app').innerHTML;
      return {J:v.filter(x=>x==='J').length,R:v.filter(x=>x==='R').length,ACL:v.filter(x=>x==='ACL').length,AL:v.filter(x=>x==='AL').length,rendered:html.includes('chip cc lab')}}""")
    check('akhir musim: 1 J, 3 R, 3 ACL (tempat 2-4), 2 AL, dipaparkan di jadual', r['J'] == 1 and r['R'] == 3 and r['ACL'] == 3 and r['AL'] == 2 and r['rendered'], r)

    # --- Ekonomi & stadium
    pg.evaluate("()=>{S.t=0}")
    r = pg.evaluate("""()=>{const cs=Object.values(S.clubs).filter(c=>c.tier);return {maxCap:Math.max(...cs.map(c=>c.cap)),over:cs.filter(c=>c.cap>CAP_MAX[c.tier]).length,abs:CAP_ABS,max:CAP_MAX,
      tgt:[1,2,3].map(l=>{const c=S.clubs[S.lg[l][0]];return stadTarget(c)})}}""")
    check('semua stadium <= had divisyen; Liga 1 maksimum mutlak 30,000', r['maxCap'] <= 30000 and r['abs'] == 30000 and r['max']['1'] == 30000, r)
    r = pg.evaluate("""()=>{const o=JSON.parse(JSON.stringify(S));o.sv=3;const cid=Object.keys(o.clubs).find(k=>o.clubs[k].tier===1);o.clubs[cid].cap=52000;
      const prev=S;S=o;ensureState();const res={sv:S.sv,cap:S.clubs[cid].cap};S=prev;return res}""")
    check('migrasi v4: kapasiti > 30,000 dipotong ke 30,000', r['sv'] == 8 and r['cap'] == 30000, r)
    r = pg.evaluate("""()=>{const c=S.clubs[S.user];c.cap=CAP_MAX[c.tier]-STAD_STEPS[c.tier][1];c.bal=5e7;S.job.conf=90;S.job.cool=null;S.proj=S.proj.filter(p=>p.cid!==S.user);const hf=window.homeFill;window.homeFill=()=>0.95;
      const steps=STAD_STEPS[c.tier];const bad=boardRequest('stad|'+steps[steps.length-1]);mStadium();const html=document.getElementById('modal')?document.getElementById('modal').innerHTML:document.body.innerHTML;
      const cap0=c.cap,bal0=c.bal;const ok=boardRequest('stad|'+steps[0]);const pj=S.proj.find(p=>p.cid===S.user&&p.k==='stad');
      const dup=boardRequest('stad|'+steps[0]);window.homeFill=hf;
      return {bad:bad.ok,badMsg:bad.msg,modal:html.includes('Pulang modal')&&html.includes('Kapasiti baharu'),ok:ok.ok,pj:!!pj&&pj.seats===steps[0],paid:bal0-c.bal===steps[0]*SEAT_COST[c.tier],capSame:c.cap===cap0,dup:dup.ok}}""")
    check('pembesaran stadium berperingkat: melebihi had ditolak, kos ditolak, projek direkod, pratonton muncul', (not r['bad']) and r['modal'] and r['ok'] and r['pj'] and r['paid'] and r['capSame'] and not r['dup'], r)
    r = pg.evaluate("""()=>{ACT.nav('finance');const t=document.getElementById('app').textContent;return {ok:t.includes('Ringkasan & ramalan')&&t.includes('Ramalan baki hujung musim')&&!t.includes('NaN')&&!t.includes('undefined'),t:t.slice(-300)}}""")
    check('halaman Kewangan: ringkasan & ramalan, tiada NaN', r['ok'], r)
    r = pg.evaluate("""()=>{const bal=S.clubs[S.lg[1][0]];const ai=S.lg[1].filter(c=>c!==S.user);ai.forEach(id=>{S.clubs[id].bal=30e6;S.clubs[id].cap=12000});S.proj=S.proj.filter(p=>p.cid===S.user);
      const b0=ai.map(id=>S.clubs[id].bal);aiStadiums();aiInvest();const pj=S.proj.filter(p=>ai.includes(p.cid));
      return {inv:ai.every((id,i)=>S.clubs[id].bal<b0[i]-5e6),projs:pj.length,withinCap:pj.every(p=>S.clubs[p.cid].cap+p.seats<=CAP_MAX[1]),tgtOk:pj.every(p=>S.clubs[p.cid].cap+p.seats<=Math.max(stadTarget(S.clubs[p.cid]),S.clubs[p.cid].cap+1)||p.seats<=STAD_STEPS[1][1])}}""")
    check('AI: lebihan wang disalur (sink), projek stadium dalam had', r['inv'] and r['projs'] > 0 and r['withinCap'], r)
    r = pg.evaluate("""()=>{const c=S.clubs[S.lg[2][0]];const b=c.bal;S.pendingMoves={up:[],down:[]};const id=S.lg[1][0];if(id===S.user)return 'skip';
      return {par:PARACHUTE,hasT3tv:TIER[3].tv>=85000}}""")
    check('pemalar bantuan penurunan & hak siaran Liga 3 dinaikkan', r != 'skip' and r['hasT3tv'] and r['par']['1'] > r['par']['2'], r)

    # --- Legasi: simpanan lama dengan timeline lama mesti habis musim tanpa ralat
    print('INFO ralat halaman:', errs[:3])
    b.close()
srv.terminate()
check('tiada ralat halaman', not errs, errs[:3])
print('\nGAGAL:' if fails else '\nSEMUA LULUS', fails)
sys.exit(1 if fails else 0)
