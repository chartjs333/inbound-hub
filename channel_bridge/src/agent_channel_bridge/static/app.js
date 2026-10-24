'use strict';
const $ = id => document.getElementById(id);
let csrf='', config, channels=[], stream=null, proof=null, popup=null, pendingNonce=null;
const notice = text => { $('notice').textContent=text; };
async function api(path, options={}) {
 const response = await fetch('/mobile'+path, {...options, credentials:'same-origin',
   headers:{...(options.body && typeof options.body==='string'?{'Content-Type':'application/json'}:{}),
     ...(options.method && options.method!=='GET'?{'X-CSRF-Token':csrf}:{}),...options.headers}});
 const data = await response.json();
 if (!response.ok) throw new Error(data.detail || 'Действие не выполнено');
 return data;
}
function action(callback){return async e=>{if(e)e.preventDefault();try{await callback(e);}catch(error){notice(error.message);}};}
function node(tag,text){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;return el;}
function button(text,callback){const el=node('button',text);el.type='button';el.onclick=action(callback);return el;}
async function authenticate(binding){
 popup=window.open('about:blank','hub-identity','width=480,height=700');
 if(!popup)throw new Error('Разрешите окно входа для этого сайта');
 const challenge=await api('/challenge',{method:'POST',body:JSON.stringify(binding)});
 pendingNonce=challenge.nonce;
 const url=new URL(config.identity_provider);
 url.searchParams.set('challenge',JSON.stringify(challenge));
 url.searchParams.set('return_origin',location.origin);
 popup.location=url.href;
}
window.addEventListener('message',action(async event=>{
 if(!config || !popup)return;
 if(event.origin!==new URL(config.identity_provider).origin || event.source!==popup)return;
 const data=event.data;
 if(!data?.proof || data.proof.nonce!==pendingNonce || typeof data.signature!=='string')return;
 pendingNonce=null; popup.close();popup=null;
 if(data.proof.action==='login'){
   const response=await api('/login',{method:'POST',body:JSON.stringify(data)});csrf=response.csrf;await refresh();
 }else{proof=data;notice('Личность подтверждена. Выдайте выбранное разрешение.');}
}));
$('login-form').onsubmit=action(async e=>authenticate(Object.fromEntries(new FormData(e.target))));
$('logout').onclick=action(async()=>{await api('/logout',{method:'POST'});csrf='';stopCamera();proof=null;await refresh();});
$('refresh').onclick=action(refresh);
async function refresh(){
 let me;try{me=await api('/session');}catch{ $('login').hidden=false;$('workspace').hidden=true;return; }
 csrf=me.csrf;$('identity').textContent=me.user+' · '+me.project;$('login').hidden=true;$('workspace').hidden=false;
 channels=await api('/channels');$('channels').replaceChildren();$('grant-channel').replaceChildren();
 for(const channel of channels){
   const card=node('div');card.className='card';card.append(node('strong',channel.channel_id));
   if(channel.type==='human')for(const [name,online] of [['Online',true],['Offline',false]])
     card.append(button(name,async()=>{await api('/presence/'+encodeURIComponent(channel.channel_id),{method:'POST',body:JSON.stringify({online})});notice(name+' установлен. Online истекает через 60 секунд без обновления.');}));
   $('channels').append(card);const option=node('option',channel.channel_id);option.value=channel.channel_id;$('grant-channel').append(option);
 }updateActions();
 const requests=await api('/requests');$('requests').replaceChildren();
 for(const request of requests){
   const card=node('article');card.className='card';card.append(node('h3',request.channel_id+' · '+request.status),node('p',request.text));
   if(request.status==='queued')card.append(button('Отменить запрос',async()=>{await api('/requests/'+encodeURIComponent(request.request_id)+'/cancel',{method:'POST'});await refresh();}));
   if(request.status==='delivered'){
     const text=node('textarea');text.setAttribute('aria-label','Ответ на '+request.request_id);card.append(text);
     card.append(button('Отправить ответ',async()=>{await upload(request.request_id,new Blob([text.value],{type:'text/plain'}));}));
     const file=node('input');file.type='file';file.accept='image/png,image/jpeg,audio/wav,application/json,text/plain';file.setAttribute('aria-label','Файл наблюдения');
     file.onchange=action(async()=>{if(file.files[0])await upload(request.request_id,file.files[0]);});card.append(file);
     if(request.operation==='request_observation')card.append(button('Разрешить камеру и сделать фото',()=>camera(request.request_id)),button('Записать голос (10 сек.)',()=>voice(request.request_id)));
   }$('requests').append(card);
 }
}
function updateActions(){proof=null;const channel=channels.find(c=>c.channel_id===$('grant-channel').value);for(const [id,values] of [['grant-agent',channel?.agents||[]],['grant-action',channel?.capabilities||[]]]){ $(id).replaceChildren(...values.map(v=>{const o=node('option',v);o.value=v;return o;}));}}
$('grant-channel').onchange=updateActions;
$('grant-action').onchange=()=>{proof=null;};
$('step-up').onclick=action(()=>authenticate({channel_id:$('grant-channel').value,action:$('grant-action').value}));
$('grant-form').onsubmit=action(async()=>{const data=await api('/grants',{method:'POST',body:JSON.stringify({channel_id:$('grant-channel').value,agent_id:$('grant-agent').value,action:$('grant-action').value,...(proof||{})})});proof=null;$('grant-result').textContent='Разрешение: '+data.grant_id;});
$('qr-form').onsubmit=action(discover);
async function discover(){
 const checkpoint=$('checkpoint').value.trim();if(!/^[A-Za-z0-9_.:-]{1,128}$/.test(checkpoint))throw new Error('Нужен идентификатор зарегистрированной точки, а не URL');
 const found=await api('/checkpoints/'+encodeURIComponent(checkpoint));$('plugins').replaceChildren(node('p',found.device.manufacturer+' / '+found.device.model));
 for(const plugin of found.plugins){const card=node('div');card.className='card';card.append(node('strong',plugin.plugin_id+' '+plugin.version));
   if(plugin.runtime_target!=='server'){const link=node('a','Открыть официальный магазин');link.href=plugin.install_source;link.rel='noopener noreferrer';link.target='_blank';link.className='module';card.append(link);}
   card.append(button('Согласен активировать модуль',async()=>{await api('/activate',{method:'POST',body:JSON.stringify({checkpoint,plugin_id:plugin.plugin_id,app_version:[1,0,0],consent:true})});notice('Модуль активирован. Для выполнения действия требуется отдельное разрешение.');}));$('plugins').append(card);
 }
}
function stopCamera(){if(stream)stream.getTracks().forEach(t=>t.stop());stream=null;$('preview').srcObject=null;$('preview').hidden=true;$('capture').hidden=true;}
async function camera(requestId){stopCamera();stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'},audio:false});$('preview').hidden=false;$('preview').srcObject=stream;await $('preview').play();$('capture').hidden=false;$('capture').onclick=action(async()=>{const canvas=document.createElement('canvas');canvas.width=$('preview').videoWidth;canvas.height=$('preview').videoHeight;canvas.getContext('2d').drawImage($('preview'),0,0);const blob=await new Promise(r=>canvas.toBlob(r,'image/png'));stopCamera();await upload(requestId,blob);});}
$('scan').onclick=action(async()=>{if(!('BarcodeDetector' in window)){notice('Сканер недоступен: введите код вручную.');return;}stopCamera();stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}});$('preview').hidden=false;$('preview').srcObject=stream;await $('preview').play();const detector=new BarcodeDetector({formats:['qr_code']});const deadline=Date.now()+30000;while(stream&&Date.now()<deadline){const codes=await detector.detect($('preview'));if(codes.length){$('checkpoint').value=codes[0].rawValue;stopCamera();await discover();return;}await new Promise(r=>setTimeout(r,250));}stopCamera();});
async function upload(id,blob){await api('/requests/'+encodeURIComponent(id)+'/observation',{method:'POST',headers:{'Content-Type':blob.type||'application/octet-stream'},body:blob});notice('Наблюдение сохранено и связано с запросом.');await refresh();}
async function voice(id){
 const mic=await navigator.mediaDevices.getUserMedia({audio:true});const audio=new AudioContext({sampleRate:48000});let processor,source;
 try{const chunks=[];source=audio.createMediaStreamSource(mic);processor=audio.createScriptProcessor(4096,1,1);processor.onaudioprocess=e=>chunks.push(new Float32Array(e.inputBuffer.getChannelData(0)));source.connect(processor);processor.connect(audio.destination);notice('Идёт запись голоса — 10 секунд.');await new Promise(r=>setTimeout(r,10000));processor.disconnect();source.disconnect();
 const count=chunks.reduce((n,c)=>n+c.length,0),buffer=new ArrayBuffer(44+count*2),view=new DataView(buffer);let pos=44;const ascii=(offset,s)=>[...s].forEach((c,i)=>view.setUint8(offset+i,c.charCodeAt(0)));ascii(0,'RIFF');view.setUint32(4,36+count*2,true);ascii(8,'WAVEfmt ');view.setUint32(16,16,true);view.setUint16(20,1,true);view.setUint16(22,1,true);view.setUint32(24,audio.sampleRate,true);view.setUint32(28,audio.sampleRate*2,true);view.setUint16(32,2,true);view.setUint16(34,16,true);ascii(36,'data');view.setUint32(40,count*2,true);for(const chunk of chunks)for(const v of chunk){view.setInt16(pos,Math.max(-1,Math.min(1,v))*32767,true);pos+=2;}await upload(id,new Blob([buffer],{type:'audio/wav'}));
 }finally{mic.getTracks().forEach(t=>t.stop());if(processor)processor.disconnect();if(source)source.disconnect();await audio.close();}
}
window.addEventListener('pagehide',stopCamera);
(async()=>{try{config=await api('/config');await refresh();}catch(error){notice(error.message);}})();
