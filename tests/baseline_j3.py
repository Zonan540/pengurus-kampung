"""Garis dasar enjin perlawanan (J3): python3 tests/baseline_j3.py <bil_dunia> <fail_keluar.json>
Simulasi semua perlawanan liga dalam N dunia rawak; simpan [liga,beza_kekuatan,gH,gA,derbi,sh0,sh1,xg0,xg1]."""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','site')
srv=subprocess.Popen([sys.executable,'-m','http.server','8802'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
JS=r"""(n)=>{const rows=[];
 for(let w=0;w<n;w++){newWorld();
  for(const f of Object.values(S.fixtures)){if(f.comp!=='L')continue;const hs=clubStrength(f.h),as=clubStrength(f.a);
    const m=newMatch(f,-1);let g=0;while(!m.done&&g++<400)stepMinute(m);
    rows.push([f.lg,+(hs-as).toFixed(2),m.sc[0],m.sc[1],isDerby(f)?1:0,m.st.sh[0],m.st.sh[1],+m.st.xg[0].toFixed(2),+m.st.xg[1].toFixed(2)])}}
 return rows}"""
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context()
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.goto('http://localhost:8802/index.html');pg.wait_for_function("typeof newWorld==='function'",timeout=20000);time.sleep(1)
    t=time.time();rows=pg.evaluate(JS,int(sys.argv[1]));print('wall',round(time.time()-t,1),'errs',errs[:3],file=sys.stderr)
    json.dump(rows,open(sys.argv[2],'w'));b.close()
srv.terminate()
