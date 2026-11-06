"""Ujian 2.1 Beta 1: formasi tambahan, peranan pemain, keakraban taktik, migrasi SCHEMA 8, simpanan pergi-balik, enjin."""
import subprocess, sys, time, os, json
from playwright.sync_api import sync_playwright
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'site')
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8830'], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1)
fails = []; errs = []
def check(name, ok, info=None):
    print(('PASS ' if ok else 'FAIL ') + name + ('' if ok else '  -> ' + json.dumps(info, ensure_ascii=False, default=str)[:700]))
    if not ok: fails.append(name)
with sync_playwright() as p:
    b = p.chromium.launch(); ctx = b.new_context(viewport={'width': 1366, 'height': 900})
    ctx.route('**/*', lambda r: r.abort() if (r.request.method == 'POST' or 'fonts.g' in r.request.url) else r.continue_())
    ctx.add_init_script("localStorage.setItem('pk3-invite', JSON.stringify({code:'AUTO',adm:0,at:'2026-10-28'}));localStorage.setItem('pk3-hidehelp','1')")
    pg = ctx.new_page(); pg.on('pageerror', lambda e: errs.append(str(e)[:300]))
    pg.on('console', lambda m: errs.append('console ' + m.text[:200]) if m.type == 'error' and 'Failed to load resource' not in m.text else None)
    pg.goto('http://localhost:8830/index.html'); pg.wait_for_function("typeof newWorld==='function'&&document.getElementById('app').innerHTML.length>0", timeout=20000)
    pg.wait_for_function("!document.getElementById('splash')||getComputedStyle(document.getElementById('splash')).pointerEvents==='none'", timeout=20000); time.sleep(.5)
    pg.evaluate("()=>{UI.screen='game';newWorld();UI.selClub=S.lg[1].slice().sort((a,b)=>clubStrength(b)-clubStrength(a))[0];renderStart();document.getElementById('mgr').value='Uji';ACT.startgame()}")

    # --- data
    r = pg.evaluate("""()=>{const bad=[];const nf=Object.keys(FORMS);
      for(const f of nf){const sl=FORMS[f];if(sl.length!==11)bad.push(f+' bukan 11 slot');if(sl[0][0]!=='GK'||sl.filter(s=>s[0]==='GK').length!==1)bad.push(f+' GK');
        for(const [pos,x,y] of sl){if(!POSXY[pos])bad.push(f+' posisi '+pos);if(x<0||x>100||y<0||y>100)bad.push(f+' koordinat')}
        const out=sl.filter(s=>s[0]!=='GK');const nm=f.split('-').map(Number).reduce((a,b)=>a+b,0);if(nm!==10)bad.push(f+' nama formasi tak sepadan '+nm)}
      const sup=['4-2-2-2','4-3-1-2','3-4-1-2','4-4-1-1'].filter(f=>!FORMS[f]);
      return{nf:nf.length,bad,sup}}""")
    check('formasi: 13 formasi, semua sah (11 slot, 1 GK, posisi dan koordinat sah)', r['nf'] == 13 and not r['bad'] and not r['sup'], r)
    r = pg.evaluate("""()=>{const bad=[];const sh=new Set();const used=new Set();
      for(const [pos,L] of Object.entries(ROLE_POS)){if(!PW[pos])bad.push('PW '+pos);for(const rk of L){used.add(rk);const R=ROLE[rk];if(!R){bad.push('tiada '+rk);continue}
        const sum=Object.values(R.w).reduce((a,b)=>a+b,0);if(Math.abs(sum)>1e-9)bad.push(rk+' jumlah w '+sum);
        for(const k in R.w){if(!ATTR.includes(k))bad.push(rk+' atribut '+k);const base=(PW[pos]||{})[k]||0;if(base+R.w[k]<-1e-9)bad.push(rk+'@'+pos+' berat negatif '+k)}
        if(!Array.isArray(R.c)||R.c.length!==3)bad.push(rk+' c');for(const k in (R.like||{})){if(k!=='ment'&&!TAC_OPT[k])bad.push(rk+' like '+k);else if(k!=='ment'&&!TAC_OPT[k][1][R.like[k]])bad.push(rk+' like nilai')}
        if(!R.n||!R.d||!R.s)bad.push(rk+' teks')}}
      for(const rk of Object.keys(ROLE)){if(!used.has(rk))bad.push('peranan tak digunakan '+rk);if(sh.has(ROLE[rk].s))bad.push('kod pendek berganda '+rk);sh.add(ROLE[rk].s)}
      return{n:Object.keys(ROLE).length,bad}}""")
    check('peranan: jumlah berat 0, tiada berat negatif, kod unik, sinergi sah', r['n'] == 24 and not r['bad'], r)

    # --- keakraban asas
    r = pg.evaluate("""()=>{const f0=S.lu.form;return{f0,sv:S.sv,F:S.fam&&S.fam.F,cur:famF(f0),nova:famF('4-2-2-2'),role:famR('f9'),ai:(()=>{const s=S.sv;return 1})()}}""")
    check('keakraban: SCHEMA 8, formasi semasa 100%, formasi baharu 40%, peranan baharu 35%', r['sv'] == 8 and r['cur'] == 100 and r['nova'] == 40 and r['role'] == 35, r)

    # --- kesan peranan pada pemain sintetik
    r = pg.evaluate("""()=>{const mk=(pos,a)=>({pos,alt:[],a:Object.assign(Object.fromEntries(ATTR.map(k=>[k,10])),a)});
      const cf=mk('CF',{tec:16,vis:16,pas:15,fin:7,hea:7,str:7}),poacher=mk('CF',{fin:17,psn:16,cmp:15,hea:7,str:7,tec:7}),flat=mk('CF',{});
      const d=(p,pos,rk,f)=>roleEval(p,pos,rk,null,f)-roleRating(p,pos);
      return{f9good:d(cf,'CF','f9',100),f9bad:d(poacher,'CF','f9',100),poaGood:d(poacher,'CF','poa',100),flat:d(flat,'CF','f9',100),
        low:d(cf,'CF','f9',35),syn:roleEval(cf,'CF','f9',{pass:'L'},100)-roleEval(cf,'CF','f9',{pass:'H'},100)}}""")
    check('peranan: False 9 untung untuk pemain teknikal, rugi untuk penyudah; Penyudah untung untuk penyudah', r['f9good'] > .5 and r['f9bad'] < -.5 and r['poaGood'] > .5, r)
    check('peranan: pemain rata hampir neutral; keakraban rendah kurangkan faedah; sinergi taktik berfungsi', abs(r['flat']) < .05 and r['low'] < r['f9good'] - .3 and r['syn'] > 0, r)

    # --- UI: tetapkan peranan, padang, set semula bila formasi bertukar
    r = pg.evaluate("""()=>{UI.view='squad';render();const f0=S.lu.form;const i=FORMS[f0].findIndex(s=>s[0]==='CF');
      CHG.role(String(i),{value:'f9'});const t=curTac();const stored=t.rl[i];render();
      const html=document.getElementById('app').innerHTML;const panel=html.includes('Peranan pemain'),code=html.includes('rolec');
      const m1=newMatch(userFixture0(),-1);return{i,stored,panel,code}
      function userFixture0(){return Object.values(S.fixtures).find(f=>!f.played&&(f.h===S.user||f.a===S.user))}}""")
    check('UI: panel Peranan pemain dipaparkan, peranan disimpan dalam taktik, kod peranan pada padang', r['stored'] == 'f9' and r['panel'] and r['code'], r)
    r = pg.evaluate("""()=>{UI.view='tactic';render();const html=document.getElementById('app').innerHTML;return{pan:html.includes('Keakraban taktik'),n:(html.match(/data-act="tacset" data-arg="0\\|form\\|/g)||[]).length}}""")
    check('UI: halaman Taktik ada panel keakraban dan 13 butang formasi', r['pan'] and r['n'] == 13, r)

    # --- perlawanan: peranan pengguna dan AI, penalti formasi
    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures).find(f=>!f.played&&(f.h===S.user||f.a===S.user));const side=fx.h===S.user?0:1;
      const t=curTac();const i=t.rl.findIndex(x=>x==='f9');
      const m=newMatch(fx,side);const sd=m.sides[side];const e=sd.on.find(x=>x.si===i);
      const ai=m.sides[1-side];const aiRoles=ai.on.filter(x=>x.rk).length;
      const f0=sd.form;S.fam.F[f0]=100;const p1=profile(m,side),a1=profile(m,1-side);S.fam.F[f0]=40;const p2=profile(m,side),a2=profile(m,1-side);S.fam.F[f0]=100;
      let g=0;while(!m.done&&g++<400)stepMinute(m);
      return{rk:e&&e.rk,rf:e&&e.rf,rk0:sd.rk0,aiRoles,ratio:p2.att/p1.att,ratioD:p2.def/p1.def,aiSame:Math.abs(a2.att/a1.att-1)<1e-9,done:m.done,sc:m.sc}}""")
    check('perlawanan: peranan pengguna dipakai pada slot betul, direkodkan dalam rk0', r['rk'] == 'f9' and r['rf'] == 35 and r['rk0'] == ['f9'], r)
    check('perlawanan: AI kekal dengan peranan standard (keseimbangan liga tidak berubah)', r['aiRoles'] == 0, r)
    check('perlawanan: penalti keakraban 40% ~ -2.4% di serangan dan pertahanan pengguna, AI tidak terjejas', .974 < r['ratio'] < .978 and .974 < r['ratioD'] < .978 and r['aiSame'] and r['done'], r)

    # --- keakraban naik/turun selepas perlawanan
    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures).find(f=>!f.played&&(f.h===S.user||f.a===S.user));const side=fx.h===S.user?0:1;
      const t=curTac();S.fam.F={};S.fam.F[S.lu.form]=100;S.fam.F['4-2-2-2']=60;S.fam.F['3-5-2']=80;S.fam.R={f9:35,poa:50,inf:35};
      const m=newMatch(fx,side);const sd=m.sides[side];
      famAfter(m,fx);const a={cur:S.fam.F[S.lu.form],ot:S.fam.F['4-2-2-2'],ot2:S.fam.F['3-5-2'],f9:S.fam.R.f9,poa:S.fam.R.poa,inf:S.fam.R.inf,rk0:sd.rk0.slice()};
      const fr=Object.assign({},fx,{comp:'FR'});
      // formasi digunakan: naikkan melalui taktik 4-2-2-2 -> uji kenaikan 10% (liga) dan 15% (persahabatan)
      S.fam.F={};const m2=newMatch(fx,side);m2.sides[side].form0='4-2-2-2';famAfter(m2,fx);const lg=S.fam.F['4-2-2-2'];
      S.fam.F={};famAfter(m2,fr);const frv=S.fam.F['4-2-2-2'];
      S.fam.F={'4-2-2-2':99};famAfter(m2,fx);const cap=S.fam.F['4-2-2-2'];const msg=S.inbox[0]&&S.inbox[0].t;
      return{a,lg,frv,cap,msg}}""")
    check('keakraban: formasi tak digunakan susut 0.5 tetapi tak bawah 40; peranan digunakan naik 15', r['a']['ot'] == 59.5 and r['a']['ot2'] == 79.5 and r['a']['f9'] == 50 and r['a']['poa'] == 49.5 and r['a']['inf'] == 35, r)
    check('keakraban: formasi baharu +10 (liga), +15 (persahabatan), terhad 100 dan beri mesej inbox', r['lg'] == 50 and r['frv'] == 55 and r['cap'] == 100 and 'sebati' in (r['msg'] or ''), r)

    # --- tukar taktik dalam perlawanan membawa peranan taktik itu
    r = pg.evaluate("""()=>{const fx=Object.values(S.fixtures).find(f=>!f.played&&(f.h===S.user||f.a===S.user));const side=fx.h===S.user?0:1;
      const tb=S.tac.list[1];tb.form='4-4-1-1';tb.rl=new Array(11).fill('');tb.rl[10]='tgt';tb.rl[9]='sha';
      const m=newMatch(fx,side);const sd=m.sides[side];sd.tac=Object.assign({},tb);changeFormation(m,side,'4-4-1-1',true);
      const cfRk=(sd.on.find(e=>e.si===10)||{}).rk,amRk=(sd.on.find(e=>e.si===9)||{}).rk;
      const roles=sd.on.filter(e=>e.rk).map(e=>e.rk+'@'+e.pos+e.si);
      // tukar manual ke formasi lain kosongkan peranan
      changeFormation(m,side,'4-3-3',true);const left=sd.on.filter(e=>e.rk&&!e.off).length;
      let g=0;while(!m.done&&g++<400)stepMinute(m);
      return{cfRk,amRk,roles,left,done:m.done}}""")
    check('perlawanan: tukar ke taktik lain membawa peranan taktik itu; tukar manual menetapkan semula', r['cfRk'] == 'tgt' and r['amRk'] == 'sha' and r['left'] == 0 and r['done'], r)

    # --- migrasi dan simpanan pergi-balik
    r = pg.evaluate("""()=>{const bak=JSON.stringify(S);const o=JSON.parse(bak);const f0=o.lu.form;
      delete o.fam;o.sv=7;o.tac.list.forEach(t=>delete t.rl);S=o;runMigrations();
      const mig={sv:S.sv,keep:S.fam.F[f0],other:S.fam.F['4-2-2-2'],rl:S.tac.list.every(t=>Array.isArray(t.rl)),pen:famMul({userSide:0,sides:[{form:f0}]},0)};
      // simpanan lama (tanpa tac langsung)
      const o2=JSON.parse(bak);delete o2.fam;delete o2.tac;o2.sv=7;S=o2;runMigrations();ensureTac();const mig2=famF(S.lu.form);
      S=JSON.parse(bak);S.fam.F['3-5-2']=77;S.fam.R.f9=88.5;S.tac.list[0].rl=['','','','','','','','','','','f9'];
      const txt=packS();const back=unpack(txt);
      return{mig,mig2,rt:{f:back.fam.F['3-5-2'],r:back.fam.R.f9,rl:back.tac.list[0].rl[10],sv:back.sv}}}""")
    check('migrasi v8: simpanan SCHEMA 7 dibuka tanpa penalti pada formasi semasa, peranan taktik wujud', r['mig']['sv'] == 8 and r['mig']['keep'] == 100 and r['mig']['other'] is None and r['mig']['rl'] and r['mig']['pen'] == 1 and r['mig2'] == 100, r)
    check('simpanan: keakraban dan peranan taktik selamat pergi-balik (pack/unpack)', r['rt'] == {'f': 77, 'r': 88.5, 'rl': 'f9', 'sv': 8}, r)

    # --- simulasi musim penuh dengan peranan automatik tanpa ralat
    pg.evaluate("""()=>{window.__step=()=>{if(S.over){ACT.newseason();closeModal();closeSummary();return}if(S.fr&&!S.fr.done){frAuto();frConfirm()}
      if(S.job&&typeof S.job.conf==='number')S.job.conf=Math.max(S.job.conf,80);if(LIVE){try{endLive()}catch(e){}}doAdvance();closeSummary();closeModal()}}""")
    r = pg.evaluate("""()=>{ensureTac();autoRoles();const n=curTac().rl.filter(Boolean).length;let g=0;const s0=S.seasonNo;while(!S.over&&g++<4000)__step();
      const fam=S.fam;return{n,over:S.over,played:Object.values(S.fixtures).filter(f=>f.played&&(f.h===S.user||f.a===S.user)).length,F:fam.F,R:fam.R,err:ERRLOG.slice(-3)}}""")
    check('musim penuh: peranan automatik, keakraban berkembang, tiada ralat', r['over'] and r['played'] > 30 and r['F'] and len(r['err']) == 0, r)
    print('keakraban hujung musim:', json.dumps(r['F']), json.dumps(r['R']))
    check('tiada ralat konsol', not errs, errs[:5])
    b.close()
srv.terminate()
print('\nGAGAL: ' + ', '.join(fails) if fails else '\nSEMUA LULUS')
sys.exit(1 if fails else 0)
