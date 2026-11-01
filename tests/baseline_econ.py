"""Garis dasar ekonomi (I): python3 tests/baseline_econ.py <bil_musim> [fail_keluar.json]
Main N musim (pengurus automatik; AI sahaja bila tiada pengurus) dan rakam baki/pendapatan/kapasiti setiap tier sebelum musim baharu."""
import subprocess, sys, time, json
from playwright.sync_api import sync_playwright
import os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','site')
srv=subprocess.Popen([sys.executable,'-m','http.server','8803'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
N=int(sys.argv[1])
SNAP=r"""()=>{const o={s:S.seasonNo,tiers:{}};for(const l of [1,2,3]){const cs=S.lg[l].map(id=>S.clubs[id]);const b=cs.map(c=>c.bal).sort((a,b)=>a-b);const f=k=>cs.reduce((s,c)=>s+c.fin[k],0)/cs.length;
 o.tiers[l]={balMed:b[10],balMin:b[0],balMax:b[19],neg:b.filter(x=>x<0).length,wage:f('wage'),ops:f('ops'),spons:f('spons'),tv:f('tv'),gate:f('gate'),prize:f('prize'),sale:f('sale'),buy:f('buy'),cap:cs.reduce((s,c)=>s+c.cap,0)/20,maxcap:Math.max(...cs.map(c=>c.cap)),wbAvg:cs.reduce((s,c)=>s+wageBill(c.id),0)/20}}
 const u=S.user&&S.clubs[S.user];o.user=u?{tier:u.tier,bal:u.bal,cap:u.cap}:null;o.players=Object.keys(S.players).length;return o}"""
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context(viewport={'width':1366,'height':900})
    ctx.route('**/*',lambda r:r.abort() if (r.request.method=='POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg=ctx.new_page();pg.goto('http://localhost:8803/index.html');pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0",timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'",timeout=20000);time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")
    pg.evaluate("(f)=>{window.__snaps=[];const snap=eval(f);const o=window.newSeason;window.newSeason=function(){try{window.__snaps.push(snap())}catch(e){window.__snaps.push({err:String(e)})}return o.apply(this,arguments)}}",SNAP)
    for s in range(N):
        res=pg.evaluate(r"""(target)=>{let n=0;const t0=performance.now();
          while(S.seasonNo<target&&n<4000){if(S.over){ACT.newseason();closeModal();closeSummary();n++;continue}if(!S.user){if(S.over){newSeason();n++;continue}advance();n++;continue}
            if(S.fr&&!S.fr.done){frAuto();frConfirm()}if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);
            if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal();n++}
          return {n}}""",s+2)
        print(s+1,res,file=sys.stderr)
        if res.get('stop'):break
    out=pg.evaluate("()=>window.__snaps")
    json.dump(out,open(sys.argv[2] if len(sys.argv)>2 else 'econ.json','w'));b.close()
srv.terminate()
