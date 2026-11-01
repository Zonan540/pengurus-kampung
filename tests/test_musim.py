import subprocess, time, json, sys, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
SEASONS = int(sys.argv[1]) if len(sys.argv) > 1 else 4
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8801'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
errs = []; R = {'seasons': []}
def safe(f,*a):
    try: return f(*a)
    except Exception as e: return 'ERR '+str(e)[:200]

VIEWS = ['home','inbox','squad','tactic','train','staff','transfer','finance','board','profile','scout','season','fixtures','league','fa','tb','awards','stats','clubs','saves','help','feedback','jobs','medical']

INV = r"""()=>{const out=[];const owner={};
  for(const [cid,c] of Object.entries(S.clubs)){for(const id of [...c.players,...(c.res||[])]){const p=S.players[id];if(!p){out.push('missing player '+id+' in '+cid);continue}
     if(owner[id])out.push('player in two clubs '+id);owner[id]=cid;if(p.club!==cid&&!(p.loan))out.push('club mismatch '+id+' '+p.club+'!='+cid)}
    for(const k of ['bal','tb']){if(c.tier&&!Number.isFinite(c[k]))out.push('NaN '+k+' '+cid)}
    if(c.players.length<14)out.push('small squad '+cid+' '+c.players.length)}
  for(const [id,p] of Object.entries(S.players)){if(p.club&&!S.clubs[p.club])out.push('ghost club '+id);if(p.club&&!owner[id]&&!p.loan)out.push('orphan '+id+' club '+p.club);
    if(Object.values(p.a||{}).some(v=>!Number.isFinite(v)))out.push('NaN attr '+id);if(!Number.isFinite(p.wage))out.push('NaN wage '+id)}
  const fa=new Set(S.fa||[]);for(const id of fa){const p=S.players[id];if(!p)out.push('fa missing '+id);else if(p.club)out.push('fa has club '+id)}
  const past=Object.values(S.fixtures).filter(f=>f.t<S.t&&!f.played);if(past.length)out.push('unplayed past fixtures '+past.length);
  return out.slice(0,25)}"""

STATS = r"""()=>{const j=JSON.stringify(S);const t0=performance.now();const z=packS();const t1=performance.now();
  const r0=performance.now();render();const r1=performance.now();
  let ls=0;for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);ls+=(localStorage.getItem(k)||'').length*2}
  return {season:S.seasonNo,json:j.length,packed:z.length*2,packMs:Math.round(t1-t0),renderMs:Math.round(r1-r0),lsKB:Math.round(ls/1024),
   players:Object.keys(S.players).length,fixtures:Object.keys(S.fixtures).length,inbox:S.inbox.length,tlog:S.tlog.length,fa:(S.fa||[]).length,
   keys:Object.entries(S).map(([k,v])=>[k,JSON.stringify(v===undefined?null:v).length]).sort((a,b)=>b[1]-a[1]).slice(0,8),
   errlog:ERRLOG.slice(-5),user:S.user,tier:S.clubs[S.user]&&S.clubs[S.user].tier,over:!!S.over,jobless:!!(S.job&&S.job.jobless)}}"""

with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console ' + m.text[:200]) if m.type == 'error' and 'ERR_FAILED' not in m.text else None)
    pg.goto('http://localhost:8801/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    R['start'] = pg.evaluate(STATS)
    t0 = time.time()
    for s in range(SEASONS):
        st = time.time()
        res = pg.evaluate(r"""(target)=>{let n=0;const t0=performance.now();
          while(S.seasonNo<target&&n<4000){if(S.over){ACT.newseason();closeModal();closeSummary();n++;continue}if(!S.user){return {stop:'jobless',n,job:JSON.stringify(S.job).slice(0,300)}}
            if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);
            if(LIVE){try{endLive()}catch(e){}}
            doAdvance();closeSummary();closeModal();n++}
          return {n,ms:Math.round(performance.now()-t0)}}""", s + 2)
        inv = pg.evaluate(INV); stats = pg.evaluate(STATS)
        R['seasons'].append({'adv': res, 'wall': round(time.time() - st, 1), 'inv': inv, 'stats': stats})
        if res.get('stop'): break
    # all views render
    vr = {}
    for v in VIEWS:
        try: vr[v] = safe(pg.evaluate, "(v)=>{const t=performance.now();ACT.nav(v);return Math.round(performance.now()-t)}", v)
        except Exception as e: vr[v] = 'ERR ' + str(e)[:120]
    R['views_ms'] = vr
    # save round trip
    R['roundtrip'] = safe(pg.evaluate, "()=>{if(!S.user)return 'skip: tiada pengurus (jobless)';packS();const a=JSON.stringify(S);const s2=unpack(packS());const b2=JSON.stringify(s2);const s3=unpack(packS(true));return {utf16:a===b2,b64:JSON.stringify(s3)===a,b64len:packS(true).length}}")
    # save file then load slot and check equality
    R['slot'] = safe(pg.evaluate, "()=>{if(!S.user)return 'skip: tiada pengurus (jobless)';const m=saveSlot(1);const s=loadSlot(1);return {msg:m,ok:!!s&&JSON.stringify(s).length===JSON.stringify(S).length}}")
    # XSS probe: hostile strings in names
    R['xss'] = safe(pg.evaluate, """(views)=>{window.__x=0;const P='<img src=x onerror="window.__x=(window.__x||0)+1">';
      S.manager='M'+P;const mine=S.clubs[S.user].players;S.players[mine[0]].name='A'+P;S.players[mine[1]].name='B'+P;
      const oc=Object.keys(S.clubs).find(c=>c!==S.user);S.clubs[oc].name='K'+P;S.clubs[S.user].nick='N'+P;
      inbox('tf','T'+P,'B'+P);const hits={};
      for(const v of views){try{ACT.nav(v)}catch(e){}hits[v]=document.querySelectorAll('#app img[src="x"]').length}
      return hits}""", VIEWS)
    time.sleep(1.0)
    R['xss_fired'] = safe(pg.evaluate, "()=>window.__x")
    # quota: fill storage then autosave
    R['bench'] = safe(pg.evaluate, "()=>{const t0=performance.now();(save(),saveFlush());const t1=performance.now();const o=window.save;window.save=()=>{};const t2=performance.now();doAdvance();closeSummary();closeModal();const t3=performance.now();window.save=o;return {saveMs:Math.round(t1-t0),advNoSaveMs:Math.round(t3-t2),saveCallsInSrc:(document.scripts[3]||{}).text?null:null}}")
    R['extraClubs'] = safe(pg.evaluate, "()=>Object.entries(S.clubs).filter(([k,c])=>!Number.isFinite(c.bal)).map(([k,c])=>[k,c.name,c.tier,c.bal,c.players.length,Object.keys(c).join(',')])")
    R['quota2'] = safe(pg.evaluate, """()=>{const chunk='y'.repeat(100000);let i=0;for(;i<200;i++){try{localStorage.setItem('zq-'+i,chunk)}catch(e){break}}
      const before=localStorage.getItem('pk3-slot-auto');S.inbox.unshift({id:'zq',t:'test',b:'x',cat:'tf',d:curDate(),read:false});
      let ret,thrown=null;try{ret=saveSlot('auto')}catch(e){thrown=e.message}const after=localStorage.getItem('pk3-slot-auto');
      let ret2;try{(save(),saveFlush());ret2='(save(),saveFlush()) returned silently'}catch(e){ret2='throw '+e.message}
      const toastText=(document.getElementById('toast')||{}).textContent||'';
      for(let k=0;k<i;k++)localStorage.removeItem('zq-'+k);
      return {chunks:i,ret,thrown,ret2,autoChanged:before!==after,autoIntact:!!unpack(after),toast:toastText.slice(0,100)}}""")
    R['quota'] = safe(pg.evaluate, """()=>{let filler='';const chunk='x'.repeat(500000);let i=0;try{for(;i<40;i++){localStorage.setItem('zz-fill-'+i,chunk)}}catch(e){}
      const before=localStorage.getItem('pk3-slot-auto');S.inbox.unshift({id:'zz',t:'test',b:'x',cat:'tf',d:curDate(),read:false});
      let thrown=null,ret;try{ret=saveSlot('auto')}catch(e){thrown=e.message}const after=localStorage.getItem('pk3-slot-auto');
      const toastText=(document.getElementById('toast')||{}).textContent||'';
      for(let k=0;k<i;k++)localStorage.removeItem('zz-fill-'+k);
      return {fillChunks:i,ret,thrown,autoChanged:before!==after,autoIntact:!!unpack(after),toast:toastText.slice(0,80)}}""")
    # corrupted import must not crash (run last: it may replace S)
    R['badimport'] = safe(pg.evaluate, """()=>{const out=[];const autoBefore=localStorage.getItem('pk3-slot-auto');
      for(const t of ['', 'garbage', 'Zabc', 'B!!!', '{"v":3}', '{"v":3,"clubs":{}}']){let r;try{importText(t);r='ok'}catch(e){r='THROW '+e.message}
        out.push({t, r, msg:UI.saveMsg&&UI.saveMsg.msg, sUser:S&&S.user, nClubs:S&&S.clubs?Object.keys(S.clubs).length:null, screen:UI.screen, appLen:document.getElementById('app').innerHTML.length})}
      const autoAfter=localStorage.getItem('pk3-slot-auto');return {out,autoOverwritten:autoBefore!==autoAfter,autoStillValid:!!unpack(autoAfter)}}""")
    R['save_fn_src'] = safe(pg.evaluate, "()=>save.toString()")
    R['wall_total'] = round(time.time() - t0, 1)
    b.close()
srv.terminate(); R['errs'] = errs[:30]
print(json.dumps(R, indent=1, ensure_ascii=False))
