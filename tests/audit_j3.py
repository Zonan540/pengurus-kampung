"""Audit J3 (2.0): kesan faktor pada keputusan. python3 tests/audit_j3.py [bil_perlawanan]
Pasukan teratas (kekuatan tertinggi) lwn tercorot di Liga 1. Ukur peratus kemenangan pasukan lemah, kemenangan 3+ gol, dan kesan moral/kondisi/tempat sendiri."""
import subprocess, sys, time, json, os
from playwright.sync_api import sync_playwright
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','site')
srv=subprocess.Popen([sys.executable,'-m','http.server','8803'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
JS=r"""(N)=>{newWorld();const ids=S.lg[1].slice().sort((a,b)=>clubStrength(b)-clubStrength(a));const top=ids[0],bot=ids[ids.length-1];const sd=clubStrength(top)-clubStrength(bot);
 const setM=(cid,m,c)=>S.clubs[cid].players.forEach(id=>{S.players[id].mor=m;S.players[id].cond=c});
 const run=(h,a,mh,ma,ch,ca)=>{let wH=0,d=0,wA=0,big=0,gh=0,ga=0,hb=0;for(let i=0;i<N;i++){setM(h,mh,ch);setM(a,ma,ca);const fx={id:'aud'+i,comp:'L',lg:1,h,a,round:1,t:0,played:false};S.fixtures['aud'+i]=fx;const m=newMatch(fx,-1);let g=0;while(!m.done&&g++<400)stepMinute(m);
   const x=m.sc[0],y=m.sc[1];gh+=x;ga+=y;if(x>y)wH++;else if(x===y)d++;else wA++;if(y-x>=3)big++;if(x-y>=3)hb++;delete S.fixtures['aud'+i]}return {homeW:wH/N,draw:d/N,awayW:wA/N,away3:big/N,home3:hb/N,gh:gh/N,ga:ga/N}};
 const out={sd:+sd.toFixed(2)};
 out.topHome_neutral=run(top,bot,70,70,100,100);
 out.botHome_vs_top=run(bot,top,70,70,100,100);
 out.top_away_vs_bot_normal=run(bot,top,70,70,100,100);
 out.bot_lowMor_top_highMor=run(bot,top,20,95,100,100);   // pasukan lemah moral rendah (home) lwn pasukan kuat moral tinggi
 out.bot_highMor_top_lowMor=run(bot,top,95,20,100,100);
 out.bot_fresh_top_tired=run(bot,top,70,70,100,55);
 out.bot_tired_top_fresh=run(bot,top,70,70,55,100);
 const eq=run(ids[8],ids[9],70,70,100,100);out.equal_teams=eq;
 return out}"""
with sync_playwright() as p:
    b=p.chromium.launch();ctx=b.new_context()
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg=ctx.new_page();pg.goto('http://localhost:8803/index.html');pg.wait_for_function("typeof newWorld==='function'",timeout=20000);time.sleep(1)
    r=pg.evaluate(JS,int(sys.argv[1]) if len(sys.argv)>1 else 600)
    print(json.dumps(r,indent=1));b.close()
srv.terminate()
