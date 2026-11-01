"""Ujian Fasa 3 (2.0): DOB/umur, tempat lahir, sejarah kerjaya, pemain bersara, kecederaan berstruktur, Medical, RST, rehat, migrasi v3."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8812'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:400]))
    if not ok: fails.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('http://localhost:8812/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")

    # 1. DOB & umur
    r = pg.evaluate("""()=>{const ps=Object.values(S.players);const ref=S.season+'-07-01';
      return {n:ps.length,noDob:ps.filter(p=>!p.dob||!/^\\d{4}-\\d\\d-\\d\\d$/.test(p.dob)).length,noBp:ps.filter(p=>!p.bp).length,
        mismatch:ps.filter(p=>ageOf(p,ref)!==p.age).length,
        young:ps.filter(p=>p.res&&(ageOf(p,ref)<18||ageOf(p,ref)>21)).length,
        bpMasState:ps.filter(p=>p.nat==='MAS').every(p=>STATES.includes(p.bp)),bpImp:ps.filter(p=>p.nat!=='MAS').every(p=>BP_CITY[p.nat]&&BP_CITY[p.nat].includes(p.bp))}}""")
    check('semua pemain ada DOB sah dan tempat lahir', r['noDob'] == 0 and r['noBp'] == 0, r)
    check('umur pada 1 Julai sepadan p.age untuk semua pemain', r['mismatch'] == 0, r)
    check('pelapis berusia 18-21', r['young'] == 0, r)
    check('tempat lahir: MAS=negeri, import=bandar negara itu', r['bpMasState'] and r['bpImp'], r)
    r = pg.evaluate("""()=>{const p=Object.values(S.players)[0];p.dob='2000-03-15';p.age=26;return [ageOf(p,'2026-03-14'),ageOf(p,'2026-03-15'),ageOf(p,'2026-07-01'),ageOf(p,'2027-03-14'),ageOf(p,'2027-03-15')]}""")
    check('umur berubah tepat pada hari lahir', r == [25, 26, 26, 26, 27], r)

    # 2. migrasi v3 daripada simpanan sv=2 tanpa dob/bp/legends
    r = pg.evaluate("""()=>{const o=JSON.parse(JSON.stringify(S));o.sv=2;delete o.legends;Object.values(o.players).forEach(p=>{delete p.dob;delete p.bp});
      const prev=S;S=o;ensureState();const ps=Object.values(S.players);const res={sv:S.sv,ok:ps.every(p=>p.dob&&p.bp),cons:ps.every(p=>ageOf(p,S.season+'-07-01')===p.age),leg:typeof S.legends==='object'};S=prev;return res}""")
    check('migrasi v3: dob/bp dijana, umur konsisten, legends wujud', r['sv'] == 4 and r['ok'] and r['cons'] and r['leg'], r)

    # 3. main dua musim sebagai pengurus; semak arkib kerjaya
    pg.evaluate("""()=>{window.__play=(target)=>{let n=0;while(S.seasonNo<target&&n<4000){if(S.over){ACT.newseason();closeModal();closeSummary();n++;continue}if(!S.user){takeJob(S.lg[3][0]);closeModal()}
      if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal();n++}return n}}""")
    pg.evaluate("()=>__play(2)")
    r = pg.evaluate("""()=>{const ps=Object.values(S.players);let bad=[];ps.forEach(p=>{const h=(p.hist||[]).reduce((a,x)=>a+x[2],0)+(p.cs?p.cs[2]:0);if(h!==p.car.ap)bad.push([p.name,h,p.car.ap])});
      const withHist=ps.filter(p=>p.hist&&p.hist.length).length;const dup=ps.some(p=>{const h=p.hist||[];return h.some((x,i)=>i&&h[i-1][0]===x[0]&&h[i-1][1]===x[1]&&h[i-1][6]===x[6])});
      return {bad:bad.slice(0,3),nbad:bad.length,withHist,dup,seasonNo:S.seasonNo}}""")
    check('jumlah penampilan dalam sejarah = p.car.ap untuk semua pemain', r['nbad'] == 0 and r['withHist'] > 100, r)
    check('tiada stint berturutan yang sama (tiada penutupan berganda)', not r['dup'], r)
    r = pg.evaluate("""()=>{const L=S.legends||{};const ids=Object.keys(L);let bad=[];ids.forEach(id=>{const l=L[id];const h=l.h.reduce((a,x)=>a+x[2],0);if(h!==l.car[0])bad.push([l.n,h,l.car[0]]);if(S.players[id])bad.push(['masih hidup',l.n])});
      const id=ids[0];return {n:ids.length,bad:bad.slice(0,3),nbad:bad.length,fields:id&&Object.keys(L[id]).join(','),sample:id&&pname(id)}}""")
    check('pemain bersara diarkib (S.legends) dengan sejarah penuh', r['n'] > 20 and r['nbad'] == 0, r)
    r = pg.evaluate("""()=>{const id=Object.keys(S.legends)[0];mRetired(id);const html=document.body.textContent;const t=plink(id);closeModal();
      return {hasName:html.includes(S.legends[id].n),btn:t.includes('data-act="legend"'),pn:pname(id)===S.legends[id].n}}""")
    check('profil pemain bersara boleh dibuka dan dipautkan', r['hasName'] and r['btn'] and r['pn'], r)

    # 4. sejarah perpindahan
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[my.players.length-1]];const to=S.lg[3].find(c=>c!==S.user);const n0=(p.mv||[]).length;doTransfer(p.id,to,5000,p.wage,1);const m=p.mv[p.mv.length-1];
      return {n:(p.mv||[]).length-n0,kind:m[4],from:m[1]===S.user,to:m[2]===to,fee:m[3]}}""")
    check('doTransfer merekod sejarah perpindahan', r['n'] == 1 and r['kind'] == 0 and r['from'] and r['to'] and r['fee'] == 5000, r)

    # 5. kecederaan berstruktur
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[0]];p.inj=0;p.injx=null;p.cond=100;const x=createInjury(p,'match');const T=INJ_T[x.k];
      return {k:x.k,n:x.n,inj:p.inj,ret:x.ret===addDays(x.d0,x.n),inRange:x.n>=2&&x.n<=Math.round(T[2]*medMul())+1,sev:x.sv===T[3],ih:p.ih.length,label:injLabel(p)}}""")
    check('createInjury: jenis, tarikh, tahap dan sejarah konsisten', r['ret'] and r['inj'] == r['n'] and r['sev'] and r['ih'] >= 1 and r['inRange'], r)
    r = pg.evaluate("""()=>{const c={};let long=0,N=4000;const p={cond:100,age:25,club:null,ih:[],injx:null};for(let i=0;i<N;i++){p.injx=null;const x=createInjury(p,'match');c[x.k]=(c[x.k]||0)+1;if(x.n>=100)long++}
      const tr={};for(let i=0;i<2000;i++){p.injx=null;const x=createInjury(p,'train');tr[x.sv]=(tr[x.sv]||0)+1}return {long:long/N,tr,types:Object.keys(c).length}}""")
    check('semua 10 jenis kecederaan boleh berlaku; jangka panjang ~0.9%', r['types'] == 10 and 0.003 < r['long'] < 0.02, r)
    check('kecederaan latihan hanya tahap ringan/sederhana', all(int(k) <= 2 for k in r['tr']), r)
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[1]];p.inj=0;p.injx=null;p.cond=100;const x=createInjury(p,'match');x.k='ham';x.n=20;x.sv=2;p.inj=20;
      const early=rushBack(p);p.inj=4;const ok=rushBack(p);const st={inj:p.inj,rush:p.injx.rush,rec:p.injx.rec,avail:available(p)};
      const w=injWeight(p,null);p.injx.rec=0;p.injx.rush=0;const w0=injWeight(p,null);return {early,ok,st,boost:w/w0}}""")
    check('pulang awal ditolak jika <75% pulih', r['early'] and 'Terlalu awal' in r['early'], r)
    check('pulang awal dibenarkan hampir pulih; tetingkap kambuh 14 hari, berat risiko 5x', r['ok'] is None and r['st']['inj'] == 0 and r['st']['rush'] == 1 and r['st']['rec'] == 14 and r['st']['avail'] and abs(r['boost'] - 5) < .01, r)
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[2]];p.inj=10;p.injx={k:'buku',n:10,d0:curDate(),ret:addDays(curDate(),10),rec:0,rush:0,ag:0,sv:2};
      recover(7);const a=p.inj;recover(7);const b={inj:p.inj,rec:p.injx&&p.injx.rec};recover(7);const c2=p.injx&&p.injx.rec;recover(7);return {a,b,c2,end:p.injx}}""")
    check('pemulihan: inj turun, tetingkap kambuh bermula bila pulih, hilang selepas tamat', r['a'] == 3 and r['b']['inj'] == 0 and r['b']['rec'] == 7 and r['end'] is None, r)
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[3]];p.inj=0;p.injx=null;const x=createInjury(p,'match');const orig=p.inj=250;x.n=250;const gap=daysBetween(S.tl[S.tl.length-1].d,buildTimeline(S.season+1)[0].d);
      return {gap,okGap:gap>20&&gap<200,id:p.id}}""")
    # carry-over uji pada newSeason sebenar
    pg.evaluate("""()=>{const id=%s;window.__cid='%s'}""" % ('0', 'x'))
    r2 = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players[3]];p.ctr=S.season+3;p.age=24;p.inj=daysBetween(curDate(),S.tl[S.tl.length-1].d)+150;window.__cp=p.id;window.__inj0=p.inj;while(!S.over){if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(LIVE){try{endLive()}catch(e){}}if(!S.user)break;doAdvance();closeSummary();closeModal()}return {over:S.over}}""")
    pg.evaluate("()=>{ACT.newseason();closeModal();closeSummary()}")
    r3 = pg.evaluate("""()=>{const p=S.players[window.__cp];return p?{inj:p.inj,cl:p.club===S.user,start:window.__inj0}:null}""")
    check('kecederaan jangka panjang dibawa ke musim baharu (tidak ditetapkan semula)', r3 is None or (r3['inj'] > 40 and r3['inj'] < 150), r3)

    # 6. rehat, RST
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const ps=my.players.map(id=>S.players[id]).filter(p=>!p.res&&!p.inj);const p=ps[0];p.cond=50;p.rest=0;
      const rst=isRST(p),chip=status(p).includes('RST');const inXI=S.lu.xi.includes(p.id);const err=setRest(p);const un=!available(p),out=!S.lu.xi.includes(p.id)&&!S.lu.bench.includes(p.id);const chip2=status(p).includes('RHT');
      const c0=p.cond;const tr0=JSON.stringify(S.tr.ind[p.id]||null);recover(7);const c1=p.cond;
      const gone=!p.rest;p.rest=3;const dup=setRest(p);return {rst,chip,inXI,err,un,out,chip2,c0,c1,gone,dup}}""")
    check('RST ditanda bila kondisi <65', r['rst'] and r['chip'], r)
    check('rehat: pemain tidak tersedia, keluar dari barisan, chip RHT', r['err'] is None and r['un'] and r['out'] and r['chip2'], r)
    check('rehat: kondisi pulih lebih cepat, tamat selepas 7 hari', r['c1'] - r['c0'] >= 14 + 18 and r['gone'], r)
    check('rehat berganda ditolak', r['dup'] is not None, r)
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const p=S.players[my.players.find(id=>!S.players[id].res&&!S.players[id].inj&&!S.players[id].rest)];setRest(p);const t0=JSON.stringify(p.a);const ind0=JSON.stringify(S.tr.ind);
      // latihan tidak melatih pemain berehat
      const before=p.a.pas+p.a.tck+p.a.fin;S.tr.int='H';for(let i=0;i<30;i++){p.rest=7;trainTick(7)}return {same:before===p.a.pas+p.a.tck+p.a.fin}}""")
    check('pemain bercuti tidak menjalani latihan', r['same'], r)

    # 7. UI: Medical, profil, nav
    r = pg.evaluate("""()=>{const my=S.clubs[S.user];const ps=my.players.map(id=>S.players[id]).filter(p=>!p.res);ps.forEach(p=>{p.inj=0;p.injx=null;p.rest=0});
      createInjury(ps[0],'match');ps[1].cond=40;setRest(ps[2]);const x=createInjury(ps[3],'match');ps[3].inj=2;x.n=40;
      ACT.nav('medical');const t=document.getElementById('app').textContent;const nav=[...document.querySelectorAll('nav button')].some(b=>/Medical/.test(b.innerText));
      mPlayer(ps[0].id);const m=document.body.textContent;closeModal();ACT.nav('squad');const sq=document.getElementById('app').innerHTML.includes('RST');
      return {t:t.slice(0,60),inj:t.includes('Pemain cedera'),rst:t.includes('RST'),rest:t.includes('Sedang bercuti'),rush:t.includes('Pulang awal'),nav,prof:m.includes('Biodata dan sejarah kerjaya')&&m.includes(ps[0].bp),sq}}""")
    check('tab Medical memaparkan cedera, RST, cuti rehat, butang pulang awal', r['inj'] and r['rst'] and r['rest'] and r['rush'] and r['nav'], r)
    check('profil pemain memaparkan biodata dan sejarah; skuad menunjukkan RST', r['prof'] and r['sq'], r)
    r = pg.evaluate("""()=>{const out={};for(const v of VIEWS_ALL){try{ACT.nav(v);out[v]=1}catch(e){out[v]='ERR '+e.message}}return Object.entries(out).filter(([k,v])=>v!==1)}""".replace('VIEWS_ALL', json.dumps(['home','inbox','squad','tactic','train','staff','transfer','finance','board','profile','scout','season','fixtures','league','fa','tb','awards','stats','clubs','saves','medical'])))
    check('semua paparan dirender tanpa ralat', not r, r)
    # XSS bp / nama
    r = pg.evaluate("""()=>{window.__x=0;const P='<img src=x onerror="window.__x=1">';const my=S.clubs[S.user];const p=S.players[my.players[0]];p.bp=P;p.name='N'+P;mPlayer(p.id);const a=document.querySelectorAll('img[src="x"]').length;closeModal();
      const l=Object.keys(S.legends)[0];S.legends[l].bp=P;S.legends[l].n='L'+P;mRetired(l);const b=document.querySelectorAll('img[src="x"]').length;closeModal();ACT.nav('medical');return {a,b,x:window.__x}}""")
    check('XSS: tempat lahir/nama dalam profil dan pemain bersara dilepaskan', r['a'] == 0 and r['b'] == 0, r)

    # 8. simpan-muat termasuk medan baharu
    r = pg.evaluate("""()=>{const z=packS();const s2=unpack(z);const p=Object.values(s2.players).find(p=>p.hist&&p.hist.length);const q=S.players[p.id];return {sv:s2.sv,eq:JSON.stringify(s2)===JSON.stringify(S),leg:Object.keys(s2.legends).length>0,hist:JSON.stringify(p.hist)===JSON.stringify(q.hist)}}""")
    check('simpan-muat mengekalkan DOB, sejarah, legends (ulang-alik tepat)', r['eq'] and r['leg'] and r['hist'] and r['sv'] == 4, r)
    r = pg.evaluate("""()=>{const t=performance.now();for(let i=0;i<3;i++)saveSlot('auto');return {ms:(performance.now()-t)/3,kb:Math.round(packS().length*2/1024),json:Math.round(JSON.stringify(S).length/1024)}}""")
    print('simpan:', r)
    check('saveSlot masih < 300 ms', r['ms'] < 300, r)
    check('tiada pageerror', not errs, errs)
    b.close()
srv.terminate()
print('\nGAGAL:' if fails else '\nSEMUA LULUS', fails or '')
sys.exit(1 if fails else 0)
