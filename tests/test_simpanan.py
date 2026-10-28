import subprocess, time, json, sys, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8802'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
errs = []; R = {}
def safe(f, *a):
    try: return f(*a)
    except Exception as e: return 'ERR ' + str(e)[:300]
VIEWS = ['home','inbox','squad','tactic','train','staff','transfer','finance','board','profile','scout','season','fixtures','league','fa','tb','awards','stats','clubs','saves','help','feedback','jobs']
CPU = int(sys.argv[1]) if len(sys.argv) > 1 else 1
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 390, 'height': 844})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    if CPU > 1:
        cdp = ctx.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate', {'rate': CPU})
    pg.goto('http://localhost:8802/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=30000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=30000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    # count save calls per advance step
    pg.evaluate("()=>{window.__saves=0;window.__saveMs=0;const o=saveSlot;window.saveSlot=function(s){const t=performance.now();const r=o(s);window.__saveMs+=performance.now()-t;window.__saves++;return r}}")
    R['steps'] = pg.evaluate("""()=>{const out=[];for(let i=0;i<45;i++){if(S.fr&&!S.fr.done){frAuto();frConfirm()}S.job.conf=Math.max(S.job.conf,80);
        const s0=__saves,m0=__saveMs,t=performance.now();doAdvance();closeSummary();closeModal();out.push([__saves-s0,Math.round(__saveMs-m0),Math.round(performance.now()-t)])}
      const tot=out.reduce((a,x)=>[a[0]+x[0],a[1]+x[1],a[2]+x[2]],[0,0,0]);return {perStepAvg:{saves:+(tot[0]/out.length).toFixed(2),saveMs:Math.round(tot[1]/out.length),stepMs:Math.round(tot[2]/out.length)},maxStepMs:Math.max(...out.map(x=>x[2])),json:JSON.stringify(S).length,packedChars:packS().length}}""")
    R['clickSave'] = pg.evaluate("()=>{const s0=__saves,m0=__saveMs;const m=S.inbox[3];ACT.imsg(m.id);return {saves:__saves-s0,ms:Math.round(__saveMs-m0)}}")
    # XSS probe including modals
    R['xss'] = safe(pg.evaluate, """(views)=>{window.__x=0;const P='<img src=x onerror="window.__x=(window.__x||0)+1">';
      S.manager='M'+P;const mine=S.clubs[S.user].players;mine.slice(0,4).forEach((id,i)=>S.players[id].name='P'+i+P);
      const oc=Object.keys(S.clubs).find(c=>c!==S.user&&S.clubs[c].tier);S.clubs[oc].name='K'+P;S.clubs[S.user].nick='N'+P;S.clubs[S.user].stadium='S'+P;
      inbox('tf','T'+P,'B'+P);const hits={};
      for(const v of views){try{ACT.nav(v)}catch(e){}hits[v]=document.querySelectorAll('img[src="x"]').length}
      try{mPlayer(mine[0])}catch(e){hits.mPlayerErr=e.message}hits.mPlayer=document.querySelectorAll('img[src="x"]').length;closeModal();
      const fx=Object.values(S.fixtures).find(f=>f.played&&(f.h===S.user||f.a===S.user));if(fx){try{ACT.report(fx.id)}catch(e){hits.repErr=e.message}hits.report=document.querySelectorAll('img[src="x"]').length;closeModal()}
      try{UI.clubView=oc;UI.view='club';render()}catch(e){hits.clubErr=e.message}hits.club=document.querySelectorAll('img[src="x"]').length;
      return hits}""", VIEWS)
    time.sleep(1.0); R['xss_fired'] = pg.evaluate("()=>window.__x")
    R['xss_inSaves'] = safe(pg.evaluate, "()=>{ACT.nav('saves');return document.getElementById('app').innerHTML.includes('onerror=\"window.__x')}")
    # quota: fill until fail, then save
    R['quota'] = safe(pg.evaluate, """()=>{const chunk='y'.repeat(100000);let i=0;for(;i<200;i++){try{localStorage.setItem('zq-'+i,chunk)}catch(e){break}}let j=0;for(;j<2000;j++){try{localStorage.setItem('zs-'+j,'y'.repeat(1000))}catch(e){break}}
      const before=localStorage.getItem('pk3-slot-auto');S.inbox.unshift({id:'zq',t:'test',b:Array.from({length:30000},()=>Math.random().toString(36).slice(2)).join(''),cat:'tf',d:curDate(),read:false});
      const ret=saveSlot('auto');const after=localStorage.getItem('pk3-slot-auto');
      let r2;try{save();r2='save() returns, no throw'}catch(e){r2='throw '+e.message}
      const toastText=(document.getElementById('toast')||{}).textContent||'';const tc=(document.getElementById('toast')||{}).className;
      for(let k=0;k<i;k++)localStorage.removeItem('zq-'+k);for(let k=0;k<j;k++)localStorage.removeItem('zs-'+k);
      return {chunks:i,ret,r2,autoChanged:before!==after,autoIntact:!!unpack(after),toast:toastText.slice(0,100),toastOn:tc}}""")
    R['errlog'] = pg.evaluate("()=>ERRLOG")
    b.close()
srv.terminate(); R['errs'] = errs[:30]
print(json.dumps(R, indent=1, ensure_ascii=False))
