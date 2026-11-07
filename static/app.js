const $=id=>document.getElementById(id);
const safe=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function send(url,body){const r=await fetch(url,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Request failed');return j}
$('suspicious').onclick=()=>{$('title').value='Remote typing assistant';$('description').value='Earn R5000 daily with no experience. Pay R300 registration fee immediately to secure your job. WhatsApp only.'};
$('normal').onclick=()=>{$('title').value='Junior Data Analyst';$('description').value='Company seeks junior data analyst with SQL, Excel and reporting experience. Apply through the official careers portal and attend an HR interview.'};
$('matchExample').onclick=()=>{$('cv').value='Junior software developer with Python, PostgreSQL, SQL, REST API development and data analysis experience.';$('job').value='Hiring backend developer with Python, PostgreSQL, SQL and API development skills.'};
$('scanForm').onsubmit=async e=>{e.preventDefault();$('scanResult').textContent='Analysing...';try{let r=await send('/api/analyze',{title:$('title').value,description:$('description').value,location:$('location').value});$('scanResult').innerHTML=`<h3>${safe(r.label)}</h3><p><b>Experimental ML score (not fraud probability):</b> ${r.model_risk_percent}%<br><b>Safety-rule points:</b> ${r.rule_points}</p><p><b>Warning phrases:</b> ${r.warnings.length?r.warnings.map(safe).join(', '):'None detected'}</p><p><b>Location:</b> ${safe(r.location_notice||'Not verified')}</p><small>${safe(r.disclaimer)}</small>`;loadHistory()}catch(e){$('scanResult').textContent=e.message}};
$('matchForm').onsubmit=async e=>{e.preventDefault();$('matchResult').textContent='Calculating...';try{let r;if($('cvFile').files.length){const form=new FormData();form.append('cv',$('cvFile').files[0]);form.append('job',$('job').value);const resp=await fetch('/api/match-file',{method:'POST',body:form});r=await resp.json();if(!resp.ok)throw Error(r.error||'Upload failed');}else{r=await send('/api/match',{cv:$('cv').value,job:$('job').value});}$('matchResult').innerHTML=`<h3>${r.similarity_percent}% text similarity</h3><small>${safe(r.note)}</small>`}catch(e){$('matchResult').textContent=e.message}};
async function loadHistory(){try{let r=await fetch('/api/history'),rows=await r.json();$('historyList').innerHTML=rows.length?rows.map(x=>`<div class="history-row"><div><b>${safe(x.title)}</b><br><small>${safe(new Date(x.created_at).toLocaleString())}</small></div><span>${safe(x.label)} (${x.risk_percent}%)</span></div>`).join(''):'No scans yet. Analyse an advert above.'}catch(e){$('historyList').textContent='Could not load history.'}}loadHistory();


$('jobSearchForm').onsubmit=async e=>{
 e.preventDefault();const box=$('jobResults');box.textContent='Searching Adzuna...';
 try{
  const q=new URLSearchParams({title:$('jobQuery').value,location:$('jobLocation').value});
  const resp=await fetch('/api/jobs?'+q);const data=await resp.json();
  if(!resp.ok)throw Error(data.error||'Search failed');
  box.innerHTML=data.jobs.length?'':'No matching jobs found. Try another search.';
  data.jobs.forEach(job=>{
   const item=document.createElement('article');item.className='history-row';
   const info=document.createElement('div');
   const title=document.createElement('h3');title.textContent=job.title;info.append(title);
   const meta=document.createElement('p');meta.textContent=job.company+' • '+job.location;info.append(meta);
   const desc=document.createElement('p');desc.textContent=job.description.slice(0,450);info.append(desc);
   const scan=document.createElement('button');scan.type='button';scan.className='ghost';scan.textContent='Check fraud risk';
   scan.onclick=()=>{$('title').value=job.title.slice(0,120);$('description').value=(job.description||'').slice(0,8000);$('location').value=job.location||'';$('scanResult').textContent='Job copied from Adzuna. Click Analyse job advert to check it.';document.getElementById('scanner').scrollIntoView({behavior:'smooth'});};
   const match=document.createElement('button');match.type='button';match.className='ghost';match.textContent='Match my CV';
   match.onclick=()=>{$('job').value=(job.description||'').slice(0,8000);document.getElementById('matcher').scrollIntoView({behavior:'smooth'});};
   info.append(scan,match);
   if(job.url&&/^https:\/\//i.test(job.url)){const link=document.createElement('a');link.href=job.url;link.target='_blank';link.rel='noopener noreferrer';link.textContent='View listing ↗';info.append(link);}
   item.append(info);box.append(item);
  });
 }catch(err){box.textContent=err.message;}
};
