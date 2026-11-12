const $=id=>document.getElementById(id);
let events=null,lastMessage=0,validUntil=0,paused=false;
const number=(id,n,digits=0)=>$(id).innerHTML=n==null?'—':`${Number(n).toFixed(digits)}<small> mm</small>`;
function clearPrediction(message){
  for(const id of ['diameter','length','head','candidate','confidence','frameId'])$(id).textContent='—';
  $('frameInfo').textContent=message;
}
function offline(message){
  $('status').textContent=message;$('liveDot').classList.remove('on');$('feedLabel').textContent='NO CURRENT INSPECTION';
  $('empty').hidden=false;$('offlineTitle').textContent='Feed unavailable';$('offlineNote').textContent=message;
  clearPrediction('No current inspection · REVIEW');
}
function update(r){
  validUntil=performance.now()+Math.max(0,500-(r.frame_age_ms??500));
  lastMessage=performance.now();$('model').textContent=r.model||'PI';$('source').textContent=r.source==='test image'?'TEST IMAGE · NOT A LIVE CAMERA':`USB camera ${r.source}`;
  $('skipped').textContent=r.skipped_frames??0;
  $('latency').innerHTML=r.processing_ms==null?'—':`${r.processing_ms.toFixed(0)}<small> ms</small>`;
  $('age').innerHTML=r.frame_age_ms==null?'—':`${r.frame_age_ms.toFixed(0)}<small> ms</small>`;
  $('tail').innerHTML=r.timing?`${r.timing.p95_ms.toFixed(0)} / ${r.timing.p99_ms.toFixed(0)}<small> ms</small>`:'—';
  if(r.camera_error||r.stale){offline(r.camera_error||'Waiting for a fresh inspection');return;}
  $('empty').hidden=true;$('liveDot').classList.add('on');$('feedLabel').textContent='LIVE FROM PI';
  $('status').textContent='Connected · automatic routing locked to REVIEW';$('frameInfo').textContent=`Inspection #${r.frame_id} · candidate only`;
  number('diameter',r.measured_diameter_mm,2);number('length',r.measured_length_mm,1);
  $('head').textContent=r.head_type||'—';$('candidate').textContent=r.label||r.candidate_bin||'—';
  $('confidence').textContent=r.bolt_conf==null?'—':`${(r.bolt_conf*100).toFixed(0)}%`;$('frameId').textContent=r.frame_id??'—';
}
function connect(){
  if(events)events.close();paused=false;lastMessage=performance.now();$('pause').textContent='Pause view';
  $('stream').src=`/stream.mjpg?t=${Date.now()}`;$('status').textContent='Connecting to Pi…';
  events=new EventSource('/api/events');events.onmessage=e=>{try{update(JSON.parse(e.data));}catch{offline('Invalid response from server');}};
  events.onerror=()=>offline('Network connection interrupted. Reconnecting…');
}
$('connect').onclick=connect;
$('pause').onclick=()=>{if(paused){connect();return;}paused=true;events?.close();$('stream').removeAttribute('src');$('pause').textContent='Resume view';offline('View paused. Camera capture continues on the Pi.');};
setInterval(()=>{if(!paused&&performance.now()-lastMessage>1500)offline('No recent result from the Pi. Check the Ethernet connection.');},500);
setInterval(()=>{if(!paused&&validUntil&&performance.now()>validUntil)clearPrediction('Stale inspection · REVIEW');},100);
window.addEventListener('pagehide',()=>events?.close());
connect();
