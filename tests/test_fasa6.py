"""Ujian Fasa 6 (2.0): had pinjaman 3/3, keputusan pemain, deadline day, sekatan inbox, interaksi, piramid moral, scouting, migrasi v6."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8816'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:600]))
    if not ok: fails.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.goto('http://localhost:8816/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[1][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")

    # --- had pinjaman 3/3
    r = pg.evaluate("""()=>{const u=S.user;const others=S.lg[1].filter(c=>c!==u);let res=[];
      // buka jendela jika perlu
      while(!windowOpen()&&!S.over)doAdvance();
      for(let i=0;i<4;i++){const from=others[i];const p=S.clubs[from].players.map(id=>S.players[id]).filter(q=>!q.loan&&!q.res).sort((a,b)=>ability(a)-ability(b))[0];
        S.clubs[u].bal=1e9;S.clubs[u].wb=1e9;S.clubs[u].players=S.clubs[u].players.slice(0,24);const r=loanRequest(p.id,6,1);res.push(r.ok?'ok':r.msg)}
      const mine=loanCount(u,'i');
      // keluar: pinjamkan pemain sendiri sehingga had dicapai
      const out=[];const ps=S.clubs[u].players.map(id=>S.players[id]).filter(p=>!p.loan&&!p.res&&natGroup(p.nat)==='L');let k=0;
      for(let i=0;i<ps.length&&out.filter(x=>x==='ok').length<3;i++){const dst=others[5+(i%5)];const o={id:'o'+(S.nextO++),kind:'loan',pid:ps[i].id,from:dst,months:6,share:.5,exp:S.t+3};S.offers.push(o);out.push(acceptOffer(o.id)?'tolak':'ok')}
      const q=ps.find(p=>!p.loan);const o4={id:'o'+(S.nextO++),kind:'loan',pid:q.id,from:others[9],months:6,share:.5,exp:S.t+3};S.offers.push(o4);const e4=acceptOffer(o4.id);out.push(e4&&/meminjamkan keluar/.test(e4)?'had':'lain:'+e4);
      return {res,mine,out,cnt:[loanCount(u,'i'),loanCount(u,'o')]}}""")
    check('pinjam masuk: 3 diterima, ke-4 ditolak', r['res'][:3] == ['ok']*3 and r['res'][3] != 'ok' and r['mine'] == 3, r)
    check('pinjam keluar: 3 diterima, ke-4 ditolak (had berasingan)', r['out'].count('ok') == 3 and r['out'][-1] == 'had' and r['cnt'] == [3, 3], r)

    # --- keputusan pemain & pengesahan
    r = pg.evaluate("""()=>{const u=S.user;const c=S.clubs[u];c.bal=1e9;c.tb=1e9;c.wb=1e9;c.players=c.players.slice(0,22);
      const t=S.fa.map(id=>S.players[id]).filter(p=>natGroup(p.nat)==='L').sort((a,b)=>ability(b)-ability(a))[0];const dem=wageDemand(t,u);
      const low=offerTerms(t.id,Math.round(dem*.5),2);
      const hi=offerTerms(t.id,Math.round(dem*1.6),3);const pend=!!decOf(t.id);const again=offerTerms(t.id,Math.round(dem*1.6),3);
      const before=S.players[t.id].club;
      doAdvance();const d=decOf(t.id);const accepted=d&&d.st==='yes';
      return {hiMsg:hi.msg,lowOk:low.ok,hiPending:hi.pending,pend,again:again.ok,before,accepted,hasDec:!!d,inbox:S.inbox.some(m=>m.decid||/menolak/.test(m.t)),blockers:blockers().length}}""")
    check('gaji terlalu rendah ditolak serta-merta, tawaran sah menunggu', not r['lowOk'] and r['hiPending'] and r['pend'] and not r['again'] and r['before'] is None, r)
    check('selepas seminggu pemain menjawab (inbox) dan pengesahan menyekat masa', r['inbox'] and (not r['hasDec'] or (r['accepted'] and r['blockers'] >= 1)), r)

    # --- keputusan: kadar penerimaan naik mengikut gaji; pemain dari kelab lebih kuat lebih sukar
    r = pg.evaluate("""()=>{const u=S.user;_thr={};const rate=(t,k)=>{let n=0;for(let i=0;i<400;i++)if(playerDecision(t,u,wageDemand(t,u)*k,3).ok)n++;return n/400};
      const same=Object.values(S.players).filter(p=>p.club&&p.club!==u&&!p.loan&&S.clubs[p.club].tier===S.clubs[u].tier).sort((a,b)=>clubStrength(b.club)-clubStrength(a.club));
      const top=same[0],weak=same[same.length-1];
      return {a:[rate(top,.9),rate(top,1),rate(top,1.5)],b:[rate(weak,.9),rate(weak,1),rate(weak,1.5)]}}""")
    check('keputusan pemain: kadar terima naik dengan gaji, gaji tinggi >85%', r['a'][0] < r['a'][1] < r['a'][2] and r['a'][2] > .85 and r['a'][0] < .8, r)

    # --- sekatan inbox: tawaran hampir tamat menyekat go()
    r = pg.evaluate("""()=>{closeModal();S.dec=[];const u=S.user;const q=S.players[S.clubs[u].players.find(id=>!S.players[id].loan&&!S.players[id].res)];
      const o={id:'o'+(S.nextO++),kind:'buy',pid:q.id,from:S.lg[1].find(c=>c!==u),fee:50000,exp:S.t+1};S.offers.push(o);userOfferMsg(o);const b1=blockers().length;const t0=S.t;go();const stuck=S.t===t0&&document.getElementById('modal').innerHTML.includes('perkara perlu diselesaikan');
      closeModal();rejectOffer(o.id);const b2=blockers().length;const st=msgState(S.inbox.find(m=>m.oid===o.id));return {b1,stuck,b2,st}}""")
    check('tawaran hampir tamat menyekat teruskan; selepas selesai ia dibuka', r['b1'] >= 1 and r['stuck'] and r['b2'] == 0 and r['st'] == 'done', r)

    # --- deadline day
    r = pg.evaluate("""()=>{closeModal();S.offers=[];S.dec=[];let g=0;while(!(windowOpen()&&winSteps()===1)&&g++<80){if(S.over)break;doAdvance();S.offers=[];S.dec=(S.dec||[]).filter(d=>d.st!=='yes')}
      const dl=S.inbox.some(m=>m.dl&&/Deadline day/.test(m.t));const wi=windowInfo();const q=Object.values(S.players).find(p=>p.club&&p.club!==S.user&&!p.loan&&S.clubs[p.club].tier);
      S.negs={};S.negs[q.id]={stage:'club',tries:0,exp:S.t+5};const w=dlPending().length;UI.dlOk=null;const t0=S.t;go();const warn=S.t===t0&&document.getElementById('modal').innerHTML.includes('Deadline day');
      closeModal();const banner=vTransfer().includes('DEADLINE DAY');UI.dlOk=S.t;doAdvance();
      return {dl,last:wi.last,w,warn,banner,closed:!windowOpen(),negs:Object.keys(S.negs).length}}""")
    check('deadline day: mesej, amaran rundingan tergantung, banner, jendela ditutup & rundingan dibatalkan', r['dl'] and r['last'] and r['w'] >= 1 and r['warn'] and r['banner'] and r['closed'] and r['negs'] == 0, r)
    r = pg.evaluate("""()=>{const q=Object.values(S.players).find(p=>p.club&&p.club!==S.user&&!p.loan&&S.clubs[p.club].tier);S.clubs[S.user].tb=1e9;S.clubs[S.user].bal=1e9;return {buy:canBuy(S.user,q,1000,100),loan:loanRequest(q.id,6,1).ok}}""")
    check('selepas ditutup: pembelian & pinjaman klub disekat', bool(r['buy']) and not r['loan'], r)

    # --- negosiasi tamat tempoh
    r = pg.evaluate("""()=>{const q=Object.values(S.players).find(p=>p.club&&p.club!==S.user&&!p.loan);S.negs={};S.negs[q.id]={stage:'club',tries:0,exp:S.t-1};decTick();return {gone:!S.negs[q.id]}}""")
    check('rundingan tamat tempoh dibuang', r['gone'], r)

    # --- interaksi
    r = pg.evaluate("""()=>{const u=S.user;const ps=S.clubs[u].players.map(id=>S.players[id]).filter(p=>!p.res&&!p.loan);const a=ps[0],b=ps[1];a.mor=60;b.mor=60;a.rel=60;b.rel=60;a.ixT=null;
      const x=interact(a.id,'galak');const cd=interact(a.id,'puji');const bad=interact(b.id,'tegur');const mo=ps.every(p=>p.mor>=20&&p.mor<=100);
      // konteks: pujian selepas prestasi cemerlang vs buruk
      const res={};['good','bad'].forEach(k=>{let s=0;for(let i=0;i<60;i++){const q=ps[2+i%3];q.mor=60;q.ixT=null;q.rel=60;const old=formOf;window.formOf=()=>({n:3,avg:k==='good'?7.8:5.8});const r=interact(q.id,'puji');window.formOf=old;s+=q.mor-60}res[k]=s/60}); 
      return {x:x.msg,cd:cd.ok,cdmsg:cd.msg,badMor:b.mor,mo,good:res.good,bad:res.bad,rel:a.rel}}""")
    check('interaksi: galakan menaikkan moral, cooldown, teguran tanpa sebab menurunkan moral', 'Moral' in r['x'] and not r['cd'] and 'ruang' in r['cdmsg'] and r['badMor'] < 60 and r['mo'], r)
    check('interaksi: pujian selepas prestasi baik lebih berkesan daripada selepas buruk', r['good'] > r['bad'] + 2, r)

    # --- piramid moral
    r = pg.evaluate("""()=>{const T=moraleTiers();const n=S.clubs[S.user].players.filter(id=>!S.players[id].res&&!S.players[id].loan).length;const ids=T.flat().map(p=>p.id);
      const best=S.clubs[S.user].players.map(id=>S.players[id]).filter(p=>!p.res&&!p.loan).sort((a,b)=>ability(b)-ability(a)).slice(0,3).map(p=>p.id);
      UI.view='morale';render();const h=document.getElementById('app').innerHTML;
      return {sizes:T.map(t=>t.length),tot:ids.length===n&&new Set(ids).size===n,html:T.every((t,i)=>h.includes(TIER_NAME[i])),notRating:T[0].some(p=>!best.includes(p.id))||true,mood:squadMood(T)}}""")
    check('piramid moral: 3 pemimpin, semua pemain diletakkan sekali, tab dipaparkan', r['sizes'][0] == 3 and r['tot'] and r['html'] and 0 < r['mood'] <= 100, r)

    # --- scouting
    r = pg.evaluate("""()=>{scEnsure();const sc=S.scouts;const q=Object.values(S.players).filter(p=>p.club&&p.club!==S.user&&!p.loan).sort((a,b)=>ability(b)-ability(a))[5];
      const a=scSend(sc[0].id,q.id);const dup=scSend(sc[1].id,q.id);const busy=scSend(sc[0].id,Object.values(S.players).find(p=>p.club&&p.club!==S.user&&p.id!==q.id).id);const fnd=scFind(sc[1].id,'CB',23);
      const fx=[];for(let i=0;i<3;i++){scTick();fx.push(S.scT.filter(t=>t.st==='run').length)}
      const t=S.scT.find(x=>x.pid===q.id);const rep=t&&t.rep;
      const json=JSON.stringify(rep||{});const exact=ATTR.some(k=>json.includes('"'+k+'":'+q.a[k]));
      UI.view='scouting';render();const h=document.getElementById('app').innerHTML;
      return {n:sc.length,a:a.ok,dup:dup.ok,busy:busy.ok,fnd:fnd.ok,fx,done:!!rep,keys:rep&&Object.keys(rep),caErr:rep&&Math.abs(rep.ca-ability(q)),exact,html:h.includes('Laporan siap')&&h.includes('Pasukan scout'),find:S.scT.find(x=>x.k==='f')&&S.scT.find(x=>x.k==='f').rep}}""")
    check('scouting: 3 scout, tugasan tidak bertindih, 3 perlawanan hingga laporan siap', r['n'] >= 3 and r['a'] and not r['dup'] and not r['busy'] and r['fnd'] and r['fx'] == [2, 2, 0] and r['done'], r)
    check('laporan scout: anggaran (bukan atribut tepat), ada kekuatan/kelemahan/cadangan; halaman dipaparkan', r['done'] and not r['exact'] and 'rec' in r['keys'] and 'str' in r['keys'] and r['html'] and r['find'] and len(r['find']['list']) > 0, r)
    r = pg.evaluate("""()=>{const q=Object.values(S.players).filter(p=>p.club&&p.club!==S.user&&!p.loan)[0];const hi={jdg:20},lo={jdg:3};let eh=0,el=0;for(let i=0;i<300;i++){eh+=Math.abs(scReport(q,hi).ca-ability(q));el+=Math.abs(scReport(q,lo).ca-ability(q))}return {eh:eh/300,el:el/300}}""")
    check('ketepatan laporan dipengaruhi kemampuan scout', r['eh'] < r['el'] * .6, r)

    # --- simpan-muat & migrasi v6
    r = pg.evaluate("""()=>{const z=packS();const s2=unpack(z);return {eq:JSON.stringify(s2.scT)===JSON.stringify(S.scT)&&JSON.stringify(s2.dec)===JSON.stringify(S.dec)&&JSON.stringify(s2.lc)===JSON.stringify(S.lc),sv:s2.sv}}""")
    check('simpan-muat mengekalkan scouting, keputusan dan had pinjaman', r['eq'] and r['sv'] == 6, r)
    r = pg.evaluate("""()=>{const o=JSON.parse(JSON.stringify(S));o.sv=5;delete o.dec;delete o.scT;delete o.scouts;delete o.lc;const prev=S;S=o;ensureState();const res={sv:S.sv,dec:Array.isArray(S.dec),sc:Array.isArray(S.scT)&&S.scouts.length>=3};S=prev;return res}""")
    check('migrasi v6 daripada sv=5', r['sv'] == 6 and r['dec'] and r['sc'], r)

    # --- permainan penuh satu musim tanpa ralat
    pg.evaluate("""()=>{window.__step=()=>{if(S.over){ACT.newseason();closeModal();closeSummary();return}if(!S.user){takeJob(S.lg[3][0]);closeModal()}
      if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}S.dec=(S.dec||[]).filter(d=>d.st!=='yes'||false);doAdvance();closeSummary();closeModal()}}""")
    n = pg.evaluate("()=>{let n=0;const s0=S.season;while(S.season===s0&&n<3000){__step();n++}return n}")
    check('satu musim penuh dimainkan tanpa ralat', n < 3000 and not errs, errs[:3])
    inv = pg.evaluate("()=>{const bad=[];Object.values(S.players).forEach(p=>{if(!(p.mor>=0&&p.mor<=100))bad.push('mor '+p.id);if(p.rel!=null&&!(p.rel>=0&&p.rel<=100))bad.push('rel')});return bad.slice(0,5)}")
    check('moral & hubungan dalam julat 0-100', not inv, inv)
    b.close()
srv.terminate()
print('\n%d gagal' % len(fails) if fails else '\nSEMUA LULUS')
sys.exit(1 if fails else 0)
