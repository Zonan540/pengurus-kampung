import subprocess, time, json, sys, os
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site');OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'shots');os.makedirs(OUT,exist_ok=True)
srv=subprocess.Popen([sys.executable,'-m','http.server','8793'],cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1)
errs=[];R={}
with sync_playwright() as p:
    b=p.chromium.launch()
    for name,vp in (('phone',{'width':390,'height':844}),('desk',{'width':1366,'height':900})):
        ctx=b.new_context(viewport=vp,is_mobile=(name=='phone'),has_touch=(name=='phone'))
        ctx.route('**/*',lambda r:r.abort() if (r.request.method=='POST' or 'fonts.g' in r.request.url) else r.continue_())
        ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
        pg=ctx.new_page();pg.on('pageerror',lambda e:errs.append(name+': '+str(e)))
        pg.goto('http://localhost:8793/index.html');pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0",timeout=20000)
        pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'",timeout=20000);time.sleep(.5)
        pg.evaluate("""()=>{UI.screen='game';newWorld();UI.selClub=S.lg[3][0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame();
          for(let i=0;i<12;i++){doAdvance();closeSummary();closeModal()}}""")
        pg.evaluate("()=>ACT.nav('inbox')");time.sleep(.3)
        r={}
        r["n"]=pg.evaluate("()=>S.inbox.length");r["firstUnreadKept"]=pg.evaluate("()=>{const l=S.inbox;return l[0].read}")
        r['detailVisibleBefore']=pg.evaluate("()=>{const d=document.querySelector('.idetail');return getComputedStyle(d).display}")
        pg.screenshot(path=f'{OUT}/{name}_list.png')
        # tap a message lower in the list
        btns=pg.locator('.ilist button');k=min(5,btns.count()-1);r['tapIdx']=k
        btns.nth(k).scroll_into_view_if_needed();btns.nth(k).click();time.sleep(.3)
        r['after']=pg.evaluate("""()=>{const d=document.querySelector('.idetail');const cs=getComputedStyle(d);const rc=d.getBoundingClientRect();
           return {open:d.classList.contains('open'),pos:cs.position,display:cs.display,top:Math.round(rc.top),h:Math.round(rc.height),title:d.querySelector('h2')&&d.querySelector('h2').textContent,
             sel:UI.inboxSel,want:document.querySelectorAll('.ilist button')[%d]?.dataset.arg,back:getComputedStyle(document.querySelector('.iback')).display}}"""%k)
        pg.screenshot(path=f'{OUT}/{name}_open.png')
        if name=='phone':
            pg.click('[data-act="iclose"]');time.sleep(.3)
            r['closed']=pg.evaluate("()=>({open:UI.inboxOpen,display:getComputedStyle(document.querySelector('.idetail')).display})")
            # open from home widget then navigate away and back
            pg.evaluate("()=>ACT.nav('home')");time.sleep(.2)
            hb=pg.locator('[data-act="imsg"]')
            if hb.count():
                hb.first.click();time.sleep(.3);r['fromHome']=pg.evaluate("()=>({view:UI.view,open:document.querySelector('.idetail').classList.contains('open')})")
            pg.evaluate("()=>ACT.nav('squad')");pg.evaluate("()=>ACT.nav('inbox')");time.sleep(.2)
            r['reenter']=pg.evaluate("()=>document.querySelector('.idetail').classList.contains('open')")
            # action buttons inside sheet: find message with links and click one
            pg.evaluate("()=>{const m=S.inbox.find(x=>x.links||x.pl||x.fx);if(m)ACT.imsg(m.id)}");time.sleep(.2)
            r['sheetButtons']=pg.evaluate("()=>[...document.querySelectorAll('.idetail.open button')].map(b=>b.textContent.trim()).slice(0,5)")
            pb=pg.locator('.idetail.open [data-act="player"], .idetail.open [data-act="report"]')
            if pb.count():
                pb.first.click();time.sleep(.3);r['modalOverSheet']=pg.evaluate("()=>{const m=document.querySelector('.modal-bg');return !!m&&+getComputedStyle(m).zIndex>48}")
                pg.screenshot(path=f'{OUT}/phone_modal_over_sheet.png')
            pg.keyboard.press('Escape');pg.keyboard.press('Escape');time.sleep(.2)
            r['escClosed']=pg.evaluate("()=>UI.inboxOpen")
            r['hscroll']=pg.evaluate("()=>document.documentElement.scrollWidth")
        R[name]=r;ctx.close()
    b.close()
srv.terminate();R['errs']=errs;print(json.dumps(R,indent=1,ensure_ascii=False))
