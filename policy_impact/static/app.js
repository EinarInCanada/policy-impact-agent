'use strict';
const $ = id => document.getElementById(id);
let config, latest = null, busy = false;
function element(tag, text, className) {
  const node = document.createElement(tag);
  if (text !== undefined) node.textContent = text;
  if (className) node.className = className;
  return node;
}
function status(text, error = false) { $('status').textContent = text; $('status').className = error ? 'error' : ''; }
function task() { return {document_id:'review-policy', before:'v1', after:'v2', at:$('date').value, intent:$('intent').value, question:$('question').value}; }
function setBusy(value) {
  busy = value;
  for (const id of ['preview','generate','scenario','date','intent','question','mode','model','key','consent','provider','endpoint']) $(id).disabled = value;
  for (const button of document.querySelectorAll('#demo-list button')) button.disabled = value;
  $('download').disabled = value || !latest;
  $('findings').setAttribute('aria-busy', String(value));
}
function invalidate() {
  latest = null; $('download').disabled = true;
  $('demo-notice').hidden = true; $('demo-notice').replaceChildren();
  for (const id of ['scope','metrics','changes','evidence']) $(id).replaceChildren();
  $('findings').replaceChildren(element('p', 'Inputs changed. Preview evidence or generate a new draft.', 'empty'));
  $('trace').textContent = 'No execution for the current inputs.';
}
function chooseCase() {
  const selected = config.cases.find(c => c.id === $('scenario').value);
  $('date').value = selected.task.at; $('intent').value = selected.task.intent || 'current_review';
  $('question').value = selected.task.question; invalidate();
}
function render(result) {
  const context = result.investigation, packet = result.packet;
  const evidence = result.discovered_evidence || context.evidence;
  const anchors = new Map(evidence.map((e, i) => [e.id, `evidence-${i}`]));
  $('demo-notice').hidden = result.mode !== 'saved_demo';
  $('demo-notice').replaceChildren();
  if(result.demo){$('demo-notice').append(element('strong','Saved AI-authored example · not a live run'),element('p',result.notice));}
  $('scope').textContent = `${context.investigation_date} · ${context.intent.replaceAll('_',' ')} · ${context.timing_warning}. Sources are fictional. Human review required.`;
  $('metrics').replaceChildren();
  for (const [value, label] of [[context.comparison.changes.length,'Changed clauses'],[evidence.length,result.demo ? 'Included evidence passages' : 'Retrieved passages'],[result.model_calls || 0,result.demo ? 'Live model calls' : 'Model calls']]) {
    const box = element('div',undefined,'metric'); box.append(element('strong',String(value)),element('span',label)); $('metrics').append(box);
  }
  $('findings').replaceChildren();
  if (!packet) $('findings').append(element('p',result.mode === 'offline_preview' ? 'Evidence preview only. No AI findings have been generated. Inspect the passages below or configure your own model key.' : `No successful draft. Run status: ${result.status}. Inspect the execution trace.`, 'empty'));
  else {
    $('findings').append(element('p',packet.summary));
    for (const finding of packet.findings) {
      const card = element('article',undefined,'card');
      card.append(element('span',finding.status.replaceAll('_',' '),'tag'),element('p',finding.statement));
      for (const id of finding.evidence_ids) {
        const button = element('button',id,'reference'); button.type = 'button';
        button.addEventListener('click',()=>{ const target = $(anchors.get(id)); if(target){ target.scrollIntoView({block:'center'}); target.focus({preventScroll:true}); } });
        card.append(button);
      }
      if (finding.missing_information.length) { card.append(element('h4','Missing information')); const list = element('ul'); for (const item of finding.missing_information) list.append(element('li',item)); card.append(list); }
      $('findings').append(card);
    }
    for (const limitation of packet.limitations) $('findings').append(element('p',limitation,'small'));
    $('findings').append(element('p',packet.mandatory_notice,'notice'));
    if(result.demo){const next=element('article',undefined,'card');next.append(element('h4','What the reviewer does next'));const list=element('ol');for(const step of result.demo.next_steps)list.append(element('li',step));next.append(list);$('findings').append(next);}
  }
  $('changes').replaceChildren();
  for (const change of context.comparison.changes) {
    const card = element('article',undefined,'card'); card.append(element('h4',`${change.clause_id} · ${change.change}`));
    const diff = element('div',undefined,'diff');
    for (const [side,label,cls] of [['before','Before · v1','old'],['after','After · v2','new']]) {
      const column = element('div',undefined,cls); column.append(element('span',label,'muted'),element('blockquote',change[side]?.reference.quote || 'No clause on this side.')); diff.append(column);
    }
    card.append(diff); $('changes').append(card);
  }
  $('evidence').replaceChildren();
  for (const e of evidence) {
    const card = element('article',undefined,'card evidence-card'); card.id = anchors.get(e.id); card.tabIndex = -1;
    card.append(element('h4',e.id),element('blockquote',e.reference.quote));
    const details = element('details'); details.append(element('summary','Verified reference coordinates'),element('code',`[${e.reference.start}, ${e.reference.end}) Unicode code points · SHA-256 ${e.reference.source_fingerprint}`)); card.append(details); $('evidence').append(card);
  }
  $('trace').textContent = JSON.stringify({mode:result.mode,status:result.status || 'draft_ready',model:result.model || null,model_calls:result.model_calls || 0,tool_calls:result.tool_calls || 0,elapsed_seconds:result.elapsed_seconds ?? null,usage:result.usage || result.usage_per_call || null,trace:result.trace || [],demo_provenance:result.demo?.provenance || null,reports_sha256:result.demo?.reports_sha256 || null,retrieval_exclusions:context.retrieval_exclusions},null,2);
}
async function loadDemo(id) {
  if(busy || !config) return;
  invalidate();setBusy(true);status('Opening saved example… No model request.');
  $('key').value='';$('consent').checked=false;
  try {
    const response=await fetch(`/api/demos/${encodeURIComponent(id)}`);
    if(!response.ok)throw new Error('Saved example could not be loaded.');
    const result=await response.json();
    $('scenario').value=result.demo.scenario_id;
    $('date').value=result.task.at;$('intent').value=result.task.intent;$('question').value=result.task.question;
    latest=result;render(result);
    status(`Saved example: ${result.demo.title}. No API key used; no live model call.`);
  } catch(error){status(error.message,true);} finally{setBusy(false);}
}
async function run(mode) {
  if(busy || !config) return;
  if(!$('setup').reportValidity()) return;
  if(mode !== 'preview' && (!$('consent').checked || !$('key').value || !$('model').value)) { status('Enter your model ID and key, then explicitly consent to remote processing.',true); return; }
  const payload = {task:task(),mode,provider:$('provider').value,endpoint:$('provider').value === 'compatible' ? $('endpoint').value.trim() : '',model:mode === 'preview' ? null : $('model').value,api_key:mode === 'preview' ? '' : $('key').value,allow_remote:mode !== 'preview' && $('consent').checked};
  if(mode !== 'preview') { $('key').value = ''; $('consent').checked = false; }
  invalidate(); setBusy(true); status(mode === 'preview' ? 'Preparing local evidence…' : 'Investigating… The page will wait for the bounded run. Reloading does not cancel a request already sent.');
  try {
    const response = await fetch('/api/run',{method:'POST',headers:{'Content-Type':'application/json','X-Review-Token':config.csrf_token},body:JSON.stringify(payload)});
    payload.api_key = '';
    const result = await response.json(); if(!response.ok) throw new Error(result.error || 'Request failed.');
    latest = result; render(result);
    const failed = result.mode === 'bounded_agent' && result.status !== 'draft_ready';
    status(failed ? `Investigation stopped: ${result.status}. No successful draft.` : mode === 'preview' ? 'Offline preview ready · zero model calls.' : 'Draft ready for human review. Exact references checked; conclusions are not certified.',failed);
  } catch(error) { status(error.message || 'Local request failed.',true); }
  finally { payload.api_key = ''; setBusy(false); }
}
$('setup').addEventListener('submit',e=>{ e.preventDefault(); run('preview'); });
$('generate').addEventListener('click',()=>run($('mode').value));
function changeProvider() {
  $('key').value = ''; $('consent').checked = false; $('model').value = '';
  $('endpoint').value = ''; $('endpoint-settings').hidden = $('provider').value !== 'compatible';
  const selected = config.providers.find(p=>p.id === $('provider').value);
  $('destination').textContent = selected.endpoint ? `Request destination: ${selected.endpoint}` : 'Request destination: the custom HTTPS endpoint you enter.';
}
$('provider').addEventListener('change',changeProvider);
$('endpoint').addEventListener('input',()=>{ $('key').value=''; $('consent').checked=false; });
$('model').addEventListener('input',()=>{ $('consent').checked=false; });
for(const id of ['date','intent','question']) $(id).addEventListener('input',invalidate);
$('scenario').addEventListener('change',chooseCase);
$('download').addEventListener('click',()=>{ if(!latest) return; const url = URL.createObjectURL(new Blob([JSON.stringify(latest,null,2)],{type:'application/json'})); const a = element('a'); a.href = url; a.download = 'policy-impact-review.json'; a.click(); setTimeout(()=>URL.revokeObjectURL(url),1000); });
async function init() {
  try {
    const response = await fetch('/api/config'); if(!response.ok) throw new Error('Cannot load the local corpus.'); config = await response.json();
    $('provider').replaceChildren(); for(const p of config.providers){const option=element('option',p.label);option.value=p.id;$('provider').append(option);} changeProvider();
    for(const demo of config.demos){const button=element('button',undefined,'demo-button');button.type='button';button.append(element('strong',demo.title),element('span',demo.description));button.addEventListener('click',()=>loadDemo(demo.id));$('demo-list').append(button);}
    $('scenario').replaceChildren(); for(const c of config.cases) { const option = element('option',c.id.replaceAll('-',' ')); option.value = c.id; $('scenario').append(option); }
    for(const source of config.sources) { const row = element('div',undefined,'source'); row.append(element('strong',`${source.document_id} / ${source.revision_id}`),element('p',`${source.role} · published ${source.published_on || 'unknown'} · effective ${source.effective_on || 'unknown'}`,'small'),element('p',source.provenance,'small')); $('sources').append(row); }
    chooseCase(); setBusy(false); await loadDemo(config.demos[0].id);
  } catch(error) { status(error.message,true); }
}
init();
