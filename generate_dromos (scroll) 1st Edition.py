#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_dromos.py
Διαβάζει το sxediagramma.txt και παράγει:
  - index.html (κύρια σελίδα)
  - <folder>/index.html για κάθε # με <folder>name</folder>
  - Αν υπάρχει <folder-all> σε κάποιο #, αυτό το section μπαίνει σε ΟΛΑ τα subfolders.
"""

import re
import os
import sys

# ─────────────────────────────────────────────────────────────────────────────
# PARSING
# ─────────────────────────────────────────────────────────────────────────────

def parse_inline(text):
    """[label](url) → <a target=_blank με Tor fallback>"""
    return re.sub(
        r'\[([^\]]+)\]\(([^)]+)\)',
        lambda m: (
            f'<a href="{m.group(2)}" target="_blank" '
            f'onclick="return openLink(event,\'{m.group(2)}\')">'
            f'{m.group(1)}</a>'
        ),
        text
    )

def parse_file(path):
    """
    Επιστρέφει (popup_node, nodes).
    Κάθε node είναι dict με:
      type: 'popup'|'h1'|'h2'|'h3'|'link'|'hline'
      label, url, body, children, folder, folder_all
    """
    with open(path, encoding='utf-8') as f:
        raw = f.read()

    # ── popup ──
    popup_node = None
    popup_match = re.search(r'<popup>(.*?)</popup>', raw, re.DOTALL)
    if popup_match:
        popup_raw = popup_match.group(1).strip()
        titles = re.findall(r'\{(.*?)\}', popup_raw, re.DOTALL)
        popup_node = {
            'type': 'popup',
            'label': titles[0].strip() if titles else 'Info',
            'body':  titles[1].strip() if len(titles) > 1 else '',
        }
        raw = raw[:popup_match.start()] + raw[popup_match.end():]

    nodes = []
    current_h1 = None
    current_h2 = None

    if popup_node:
        nodes.append(popup_node)

    for line in raw.splitlines():
        line = line.rstrip()
        if not line:
            continue

        if line.strip() == '--hline--':
            nodes.append({'type': 'hline'})
            current_h1 = None
            current_h2 = None
            continue

        # ── h1: ищем тег folder / folder-all ──
        h1m = re.match(r'^# (.+)', line)
        h2m = re.match(r'^## (.+)', line)
        h3m = re.match(r'^### (.+)', line)
        lkm = re.match(r'^\[([^\]]+)\]\(([^)]+)\)', line)

        if h1m:
            raw_label = h1m.group(1)
            folder_all = bool(re.search(r'<folder-all\s*/?\s*>', raw_label))
            folder_m   = re.search(r'<folder>([^<]+)</folder>', raw_label)
            folder     = folder_m.group(1).strip() if folder_m else None
            # καθαρό label (αφαιρούμε tags)
            clean_label = re.sub(r'<folder[^>]*>.*?</folder>', '', raw_label)
            clean_label = re.sub(r'<folder-all\s*/?\s*>', '', clean_label).strip()
            node = {
                'type': 'h1', 'label': clean_label, 'children': [],
                'folder': folder, 'folder_all': folder_all,
            }
            nodes.append(node)
            current_h1 = node
            current_h2 = None

        elif h2m:
            node = {'type': 'h2', 'label': h2m.group(1).strip(), 'children': []}
            if current_h1:
                current_h1['children'].append(node)
            else:
                nodes.append(node)
            current_h2 = node

        elif h3m:
            node = {'type': 'h3', 'label': h3m.group(1).strip(), 'children': []}
            if current_h2:
                current_h2['children'].append(node)
            elif current_h1:
                current_h1['children'].append(node)
            else:
                nodes.append(node)

        elif lkm:
            node = {'type': 'link', 'label': lkm.group(1), 'url': lkm.group(2)}

            def last_h3(parent):
                if parent and parent['children'] and parent['children'][-1]['type'] == 'h3':
                    return parent['children'][-1]
                return None

            if current_h2:
                lh3 = last_h3(current_h2)
                (lh3 if lh3 else current_h2)['children'].append(node)
            elif current_h1:
                lh3 = last_h3(current_h1)
                (lh3 if lh3 else current_h1)['children'].append(node)
            else:
                nodes.append(node)

    return popup_node, nodes


# ─────────────────────────────────────────────────────────────────────────────
# HTML RENDERING
# ─────────────────────────────────────────────────────────────────────────────

_uid = [0]

def new_uid():
    _uid[0] += 1
    return f'menu_{_uid[0]}'

def reset_uid():
    _uid[0] = 0

def render_link(node):
    url, label = node['url'], node['label']
    return (f'<li class="menu-link">'
            f'<a href="{url}" target="_blank" onclick="return openLink(event,\'{url}\')">'
            f'{label}</a></li>')

def render_h3(node):
    uid = new_uid()
    inner = '\n'.join(render_node(c) for c in node['children'])
    if node['children']:
        return f'''<li class="h3-item">
  <button class="toggle-btn h3-btn" onclick="toggleMenu('{uid}')">
    <span class="arrow">▸</span>{node["label"]}
  </button>
  <ul id="{uid}" class="submenu">{inner}</ul>
</li>'''
    return f'<li class="h3-item h3-leaf"><span class="leaf-label">◦ {node["label"]}</span></li>'

def render_h2(node):
    uid = new_uid()
    inner = '\n'.join(render_node(c) for c in node['children'])
    if node['children']:
        return f'''<li class="h2-item">
  <button class="toggle-btn h2-btn" onclick="toggleMenu('{uid}')">
    <span class="arrow">▸</span>{node["label"]}
  </button>
  <ul id="{uid}" class="submenu">{inner}</ul>
</li>'''
    return f'<li class="h2-item h2-leaf"><span class="leaf-label">· {node["label"]}</span></li>'

def render_h1(node):
    uid = new_uid()
    inner = '\n'.join(render_node(c) for c in node['children'])
    if node['children']:
        return f'''<li class="h1-item">
  <button class="toggle-btn h1-btn" onclick="toggleMenu('{uid}')">
    <span class="arrow">▸</span>{node["label"]}
  </button>
  <ul id="{uid}" class="submenu">{inner}</ul>
</li>'''
    return f'<li class="h1-item h1-leaf"><span class="leaf-label">{node["label"]}</span></li>'

def render_popup(node):
    uid = new_uid()
    paragraphs = re.split(r'\n\s*\n', node['body'].strip())
    paras_html = ''.join(
        '<p>' + parse_inline(p.replace('\n', '<br>')) + '</p>'
        for p in paragraphs if p.strip()
    )
    return f'''<li class="menu-link popup-item">
  <button class="popup-trigger" onclick="showPopup(\'{uid}\')">{node["label"]}</button>
</li>
<div id="{uid}" class="popup-overlay" onclick="closePopup(event,\'{uid}\')">
  <div class="popup-box">
    <button class="popup-close" onclick="closePopupDirect(\'{uid}\')">✕</button>
    {paras_html}
  </div>
</div>'''

def render_node(node):
    t = node['type']
    if t == 'hline':  return '<li class="menu-hline"><hr></li>'
    if t == 'link':   return render_link(node)
    if t == 'h1':     return render_h1(node)
    if t == 'h2':     return render_h2(node)
    if t == 'h3':     return render_h3(node)
    if t == 'popup':  return render_popup(node)
    return ''

def build_sidebar(nodes):
    items = '\n'.join(render_node(n) for n in nodes)
    return f'<ul class="sidebar-menu">{items}</ul>'


# ─────────────────────────────────────────────────────────────────────────────
# CSS + JS (κοινό για όλες τις σελίδες)
# ─────────────────────────────────────────────────────────────────────────────

COMMON_CSS = '''\
<style>
:root{
  --bg:#0d0e14;
  --sidebar-bg:#10111a;
  --sidebar-border:#252640;
  --accent:#7b6ea8;
  --accent2:#b8aee0;
  --accent3:#7eb8c9;
  --accent-glow:rgba(123,110,168,.35);
  --glow2:rgba(126,184,201,.22);
  --text:#cdd0e8;
  --text-muted:#6870a8;
  --link:#b8aee0;
  --link-hover:#d4cdee;
  --hline:#4a4870;
  --sidebar-w:275px;
  --transition:.25s cubic-bezier(.4,0,.2,1);
  --font-ui: ui-monospace,"Cascadia Code","Fira Code","Courier New",monospace;
  --font-head: system-ui,-apple-system,"Segoe UI",sans-serif;
}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html,body{height:100%;overflow:hidden}
@media(max-height:500px){body{overflow:auto}}
body{background:var(--bg);color:var(--text);font-family:var(--font-ui);display:flex;flex-direction:column}
#bg-layer{
  position:fixed;inset:0;z-index:0;
  background:url('../MyBackground.svg') center center/contain no-repeat;
  opacity:.45;pointer-events:none;
}
@media(min-width:701px){
  #bg-layer{
    left:var(--sidebar-w);
  }
}
#blob1{
  position:fixed;width:520px;height:520px;border-radius:50%;z-index:0;
  background:radial-gradient(circle,rgba(123,110,168,.22) 0%,transparent 70%);
  top:-140px;left:-140px;pointer-events:none;
  animation:blobDrift 14s ease-in-out infinite alternate;
}
#blob2{
  position:fixed;width:400px;height:400px;border-radius:50%;z-index:0;
  background:radial-gradient(circle,rgba(126,184,201,.14) 0%,transparent 70%);
  bottom:-100px;right:-80px;pointer-events:none;
  animation:blobDrift 18s ease-in-out infinite alternate-reverse;
}
@keyframes blobDrift{0%{transform:translate(0,0) scale(1)}100%{transform:translate(40px,28px) scale(1.09)}}
body::after{
  content:'';position:fixed;inset:0;z-index:999;pointer-events:none;
  background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.06) 2px,rgba(0,0,0,.06) 4px);
}
#topbar{
  position:relative;z-index:100;height:56px;
  display:flex;align-items:center;padding:0 18px;
  background:rgba(10,10,14,.9);backdrop-filter:blur(18px);
  border-bottom:1px solid var(--sidebar-border);
  gap:14px;flex-shrink:0;
  box-shadow:0 2px 28px rgba(123,110,168,.14);
}
#topbar h1{
  font-family:var(--font-head);font-weight:800;font-size:1.28rem;
  letter-spacing:.14em;text-transform:uppercase;
  background:linear-gradient(90deg,var(--accent2),var(--accent3),var(--accent2));
  background-size:200% auto;
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  animation:shimmer 3s linear infinite;flex:1;
}
@keyframes shimmer{0%{background-position:0%}100%{background-position:200%}}
#menu-toggle{
  display:none;background:none;border:none;cursor:pointer;
  color:var(--accent2);font-size:1.5rem;line-height:1;
  padding:4px 8px;border-radius:8px;
  transition:background var(--transition),box-shadow var(--transition);
}
#menu-toggle:hover{background:rgba(167,139,250,.12);box-shadow:0 0 12px var(--accent-glow)}
/* back button */
#back-btn{
  background:none;border:1px solid var(--sidebar-border);cursor:pointer;
  color:var(--accent2);font-size:.85rem;font-family:var(--font-ui);
  padding:5px 12px;border-radius:8px;white-space:nowrap;
  transition:background var(--transition),border-color var(--transition),box-shadow var(--transition);
  text-decoration:none;display:inline-flex;align-items:center;gap:6px;
}
#back-btn:hover{
  background:rgba(184,174,224,.1);
  border-color:var(--accent2);
  box-shadow:0 0 12px var(--accent-glow);
}
/* search */
#search-btn{
  background:none;border:none;cursor:pointer;
  color:var(--accent2);font-size:1.25rem;
  padding:6px 9px;border-radius:10px;position:relative;
  transition:background var(--transition),transform var(--transition),box-shadow var(--transition);
}
#search-btn:hover{background:rgba(167,139,250,.15);transform:scale(1.15) rotate(-8deg);box-shadow:0 0 18px var(--accent-glow)}
#search-btn::after{
  content:'';position:absolute;inset:-4px;border-radius:14px;
  border:1px solid rgba(167,139,250,.3);opacity:0;
  animation:pulseRing 2.5s ease-out infinite;
}
@keyframes pulseRing{0%{transform:scale(.9);opacity:.6}70%{transform:scale(1.35);opacity:0}100%{opacity:0}}
#search-box{
  display:none;align-items:center;gap:8px;
  background:rgba(15,15,24,.97);border:1px solid var(--accent);border-radius:28px;
  padding:6px 16px;box-shadow:0 0 24px var(--accent-glow);
}
#search-box.visible{display:flex;animation:popIn .2s cubic-bezier(.34,1.56,.64,1)}
@keyframes popIn{from{opacity:0;transform:scaleX(.8)}to{opacity:1;transform:scaleX(1)}}
#search-input{
  background:none;border:none;outline:none;
  color:var(--text);font-family:var(--font-ui);font-size:.87rem;
  width:190px;caret-color:var(--accent2);
}
#search-input::placeholder{color:var(--text-muted)}
#search-go{background:none;border:none;cursor:pointer;color:var(--accent2);font-size:1rem;transition:transform var(--transition),color var(--transition)}
#search-go:hover{transform:scale(1.25);color:var(--accent3)}
#search-close-btn{background:none;border:none;cursor:pointer;color:var(--text-muted);font-size:.85rem;transition:color var(--transition)}
#search-close-btn:hover{color:#fff}
#layout{position:relative;z-index:1;display:flex;flex:1;overflow:hidden;min-height:0}
#sidebar{
  width:var(--sidebar-w);flex-shrink:0;
  background:linear-gradient(180deg,#0f0f1c 0%,#0c0c15 100%);
  border-right:1px solid var(--sidebar-border);
  overflow-y:auto;overflow-x:hidden;height:100%;min-height:0;
  transition:transform var(--transition),box-shadow var(--transition);
  scrollbar-width:thin;scrollbar-color:var(--accent) transparent;
}
#sidebar.open{box-shadow:6px 0 40px rgba(123,110,168,.3)}
#sidebar::-webkit-scrollbar{width:3px}
#sidebar::-webkit-scrollbar-thumb{background:linear-gradient(var(--accent),var(--accent3));border-radius:2px}
#sidebar::before{content:'';display:block;height:2px;background:linear-gradient(90deg,var(--accent),var(--accent3),transparent);opacity:.75}
#main{flex:1;overflow:auto;padding:32px 36px;height:100%;min-height:0}
.sidebar-menu{list-style:none;padding:8px 0}
.menu-hline{padding:4px 12px}
.menu-hline hr{border:none;height:2px;margin:6px 0;background:linear-gradient(90deg,transparent,var(--hline) 25%,var(--hline) 75%,transparent);border-radius:1px;box-shadow:0 0 6px rgba(74,72,112,.5)}
.h1-btn{
  width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:var(--font-head);font-weight:700;font-size:.91rem;
  color:var(--accent2);padding:11px 16px 11px 14px;
  display:flex;align-items:center;gap:8px;
  letter-spacing:.06em;text-transform:uppercase;position:relative;
  transition:background var(--transition),color var(--transition),padding-left var(--transition);
}
.h1-btn::before{content:'';position:absolute;left:0;top:20%;bottom:20%;width:2px;border-radius:2px;background:linear-gradient(var(--accent),var(--accent3));opacity:0;transition:opacity var(--transition)}
.h1-btn:hover,.h1-btn.open{background:rgba(167,139,250,.07);color:#fff;padding-left:18px}
.h1-btn:hover::before,.h1-btn.open::before{opacity:1}
.h1-leaf .leaf-label{display:block;padding:11px 16px;font-family:var(--font-head);font-weight:700;font-size:.91rem;color:var(--text-muted);text-transform:uppercase;letter-spacing:.06em}
.h2-btn{
  width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:var(--font-ui);font-size:.82rem;font-weight:600;
  color:var(--text);padding:9px 16px 9px 30px;
  display:flex;align-items:center;gap:7px;
  transition:background var(--transition),color var(--transition);
}
.h2-btn:hover{background:rgba(124,58,237,.1);color:var(--accent2)}
.h2-leaf .leaf-label{display:block;padding:9px 16px 9px 30px;font-size:.82rem;color:var(--text-muted)}
.h3-btn{
  width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:var(--font-ui);font-size:.76rem;
  color:var(--text-muted);padding:7px 16px 7px 46px;
  display:flex;align-items:center;gap:6px;
  transition:background var(--transition),color var(--transition);
}
.h3-btn:hover{background:rgba(56,189,248,.07);color:var(--accent3)}
.h3-leaf .leaf-label{display:block;padding:7px 16px 7px 46px;font-size:.76rem;color:var(--text-muted)}
.menu-link a{
  display:block;padding:7px 16px 7px 46px;
  color:var(--link);font-size:.81rem;text-decoration:none;position:relative;
  transition:color var(--transition),padding-left var(--transition),text-shadow var(--transition);
}
.menu-link a::before{content:'›';position:absolute;left:34px;opacity:0;transform:translateX(-5px);color:var(--accent3);transition:opacity var(--transition),transform var(--transition)}
.menu-link a:hover{color:var(--link-hover);padding-left:52px;text-shadow:0 0 12px rgba(167,139,250,.55)}
.menu-link a:hover::before{opacity:1;transform:translateX(0)}
.sidebar-menu>.menu-link a{padding-left:20px}
.sidebar-menu>.menu-link a::before{left:10px}
.sidebar-menu>.menu-link a:hover{padding-left:26px}
.toggle-btn .arrow{display:inline-block;font-size:.72em;color:var(--text-muted);transition:transform var(--transition),color var(--transition);will-change:transform}
.toggle-btn.open .arrow{transform:rotate(90deg);color:var(--accent2)}
.submenu{list-style:none;padding:0;overflow:hidden;max-height:0;opacity:0;transition:max-height .32s cubic-bezier(.4,0,.2,1),opacity .28s ease}
.submenu.open{max-height:1000px;opacity:1}
.popup-trigger{
  width:100%;text-align:left;background:none;border:none;cursor:pointer;
  font-family:var(--font-head);font-weight:600;font-size:.88rem;
  color:var(--accent2);padding:10px 16px;
  border-left:2px solid var(--accent);position:relative;overflow:hidden;
  transition:background var(--transition);
}
.popup-trigger::after{content:'';position:absolute;inset:0;background:linear-gradient(90deg,rgba(124,58,237,.18),transparent);transform:translateX(-100%);transition:transform .38s ease}
.popup-trigger:hover{background:rgba(124,58,237,.07)}
.popup-trigger:hover::after{transform:translateX(0)}
.popup-overlay{display:none;position:fixed;inset:0;z-index:500;background:rgba(0,0,0,.72);backdrop-filter:blur(8px);align-items:center;justify-content:center}
.popup-overlay.active{display:flex;animation:fadeIn .2s ease}
.popup-box{
  background:linear-gradient(135deg,#14142a,#0f0f20);
  border:1px solid var(--accent);
  box-shadow:0 0 60px var(--accent-glow),0 0 120px rgba(56,189,248,.1);
  border-radius:16px;padding:34px 38px;
  max-width:500px;width:90%;position:relative;
  font-size:.94rem;line-height:1.78;color:var(--text);
  animation:slideUp .25s cubic-bezier(.34,1.56,.64,1);
}
.popup-box::before,.popup-box::after{content:'';position:absolute;width:22px;height:22px;border-color:var(--accent3);border-style:solid}
.popup-box::before{top:10px;left:10px;border-width:2px 0 0 2px;border-radius:3px 0 0 0}
.popup-box::after{bottom:10px;right:10px;border-width:0 2px 2px 0;border-radius:0 0 3px 0}
.popup-box p{margin-bottom:.9em}
.popup-box p:last-child{margin-bottom:0}
.popup-box a{color:var(--accent3);text-decoration:underline}
.popup-box a:hover{color:#fff;text-shadow:0 0 8px var(--glow2)}
.popup-close{position:absolute;top:12px;right:14px;background:none;border:none;cursor:pointer;color:var(--text-muted);font-size:1.1rem;transition:color var(--transition),transform var(--transition)}
.popup-close:hover{color:#fff;transform:rotate(90deg)}
@keyframes fadeIn{from{opacity:0}to{opacity:1}}
@keyframes slideUp{from{opacity:0;transform:translateY(28px) scale(.95)}to{opacity:1;transform:translateY(0) scale(1)}}
.ripple{position:absolute;border-radius:50%;pointer-events:none;background:rgba(167,139,250,.22);transform:scale(0);animation:rippleAnim .55s linear}
@keyframes rippleAnim{to{transform:scale(4);opacity:0}}
@media(max-width:700px){
  #menu-toggle{display:block}
  #sidebar{
    position:fixed;left:0;top:56px;bottom:0;z-index:200;
    transform:translateX(-110%);
    overflow-y:auto;
    /* ύψος = όλη η οθόνη μείον topbar, με scroll αν χρειαστεί */
    max-height:calc(100vh - 56px);
    height:calc(100vh - 56px);
  }
  #sidebar.open{transform:translateX(0)}
  #search-input{width:140px}
}
@media(max-width:700px) and (orientation:landscape){
  /* Σε landscape η οθόνη είναι κοντή — το sidebar πρέπει να scrollάρει */
  #sidebar{
    /* ξαναορίζουμε ύψος με βάση το 100dvh αν υποστηρίζεται, αλλιώς 100vh */
    height:calc(100dvh - 56px);
    max-height:calc(100dvh - 56px);
    overflow-y:auto;
    /* scrollbar πάντα ορατό ώστε να ξέρει ο χρήστης ότι υπάρχει κύλιση */
    overscroll-behavior:contain;
  }
  /* Επιτρέπουμε scroll στο main περιεχόμενο */
  #main{overflow-y:auto}
}
</style>'''

COMMON_JS = '''\
<script>
function toggleSidebar(){document.getElementById('sidebar').classList.toggle('open')}
document.addEventListener('click',function(e){
  const sb=document.getElementById('sidebar');
  if(sb.classList.contains('open')&&!sb.contains(e.target)&&e.target.id!=='menu-toggle')
    sb.classList.remove('open');
});
function toggleSearch(){
  const box=document.getElementById('search-box');
  box.classList.toggle('visible');
  if(box.classList.contains('visible'))setTimeout(()=>document.getElementById('search-input').focus(),40);
}
function closeSearch(){document.getElementById('search-box').classList.remove('visible')}
function doSearch(){
  const q=document.getElementById('search-input').value.trim();
  if(!q)return;
  const url='https://www.wolframalpha.com/input?i='+encodeURIComponent(q);
  const w=window.open(url,'_blank');
  if(!w||w.closed||typeof w.closed==='undefined') window.location.href=url;
}
function toggleMenu(id){
  const ul=document.getElementById(id);
  ul.classList.toggle('open');
  ul.previousElementSibling.classList.toggle('open');
}
function showPopup(id){document.getElementById(id).classList.add('active')}
function closePopup(event,id){if(event.target===document.getElementById(id))document.getElementById(id).classList.remove('active')}
function closePopupDirect(id){document.getElementById(id).classList.remove('active')}
function openLink(event,url){
  event.preventDefault();
  const w=window.open(url,'_blank');
  if(!w||w.closed||typeof w.closed==='undefined') window.location.href=url;
  return false;
}
document.addEventListener('click',function(e){
  const el=e.target.closest('button,.menu-link a');
  if(!el)return;
  const r=document.createElement('span');r.className='ripple';
  const rect=el.getBoundingClientRect(),s=Math.max(rect.width,rect.height);
  r.style.cssText='width:'+s+'px;height:'+s+'px;left:'+(e.clientX-rect.left-s/2)+'px;top:'+(e.clientY-rect.top-s/2)+'px;';
  el.style.position='relative';el.style.overflow='hidden';
  el.appendChild(r);setTimeout(()=>r.remove(),580);
});
</script>'''


# ─────────────────────────────────────────────────────────────────────────────
# PAGE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def make_topbar(title='Δρόμος', back=False, bg_path='MyBackground.svg'):
    """Επιστρέφει topbar HTML. back=True → κουμπί επιστροφής."""
    back_btn = ''
    if back:
        back_btn = '<a id="back-btn" href="../index.html">← Αρχική</a>'
    return f'''\
<div id="topbar">
  <button id="menu-toggle" onclick="toggleSidebar()" aria-label="Μενού">☰</button>
  <h1>{title}</h1>
  {back_btn}
  <div id="search-box">
    <input id="search-input" type="text" placeholder="Αναζήτηση Wolfram…"
           onkeydown="if(event.key==='Enter')doSearch()">
    <button id="search-go" onclick="doSearch()" title="Αναζήτηση">⏎</button>
    <button id="search-close-btn" onclick="closeSearch()">✕</button>
  </div>
  <button id="search-btn" onclick="toggleSearch()" title="Αναζήτηση">🔍</button>
</div>'''


def build_page(sidebar_html, title='Δρόμος', back=False, bg_path='MyBackground.svg'):
    """Φτιάχνει ολόκληρη HTML σελίδα."""
    # Το bg path στο CSS διαφέρει: ρίζα vs subfolder
    css = COMMON_CSS
    if back:
        # Στα subfolders το SVG είναι ../MyBackground.svg (ήδη στο COMMON_CSS)
        pass
    else:
        # Στο root το SVG είναι MyBackground.svg
        css = css.replace("url('../MyBackground.svg')", "url('MyBackground.svg')")

    topbar = make_topbar(title=title, back=back)

    return f'''\
<!DOCTYPE html>
<html lang="el">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
{css}
</head>
<body>
<div id="bg-layer"></div>
<div id="blob1"></div>
<div id="blob2"></div>
{topbar}
<div id="layout">
  <nav id="sidebar" aria-label="Πλαϊνό μενού">
    {sidebar_html}
  </nav>
  <main id="main"></main>
</div>
{COMMON_JS}
</body>
</html>
'''


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────


import copy

def strip_folder_prefix(nodes, folder):
    """
    Επιστρέφει deep copy των nodes με τα URLs απαλλαγμένα
    από το prefix 'folder/' (case-sensitive).
    """
    prefix = folder.rstrip('/') + '/'
    def fix_node(n):
        n = dict(n)
        if n.get('type') == 'link':
            url = n['url']
            if url.startswith(prefix):
                n['url'] = url[len(prefix):]
        if 'children' in n:
            n['children'] = [fix_node(c) for c in n['children']]
        return n
    return [fix_node(n) for n in nodes]

def main():
    script_dir  = os.path.dirname(os.path.abspath(__file__))
    input_path  = os.path.join(script_dir, 'sxediagramma.txt')
    output_path = os.path.join(script_dir, 'index.html')

    popup_node, nodes = parse_file(input_path)

    # ── 1. Κύριο index.html ──────────────────────────────────────────────────
    reset_uid()
    sidebar_nodes = nodes  # όλοι οι nodes (popup + h1 + hline κτλ.)
    sidebar_html  = build_sidebar(sidebar_nodes)
    html = build_page(sidebar_html, title='Δρόμος', back=False)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f'✓ {output_path}')

    # ── 2. Βρες folder-all sections ──────────────────────────────────────────
    folder_all_nodes = [n for n in nodes if n.get('type') == 'h1' and n.get('folder_all')]

    # ── 3. Sub-folder index.html για κάθε <folder> ───────────────────────────
    for node in nodes:
        if node.get('type') != 'h1':
            continue
        folder = node.get('folder')
        if not folder:
            continue

        folder_path = os.path.join(script_dir, folder)
        if not os.path.isdir(folder_path):
            print(f'⚠  Ο φάκελος "{folder}" δεν βρέθηκε — παράλειψη.')
            continue

        # Δόμηση sidebar για subfolder:
        # popup (αν υπάρχει) + folder-all sections + το ίδιο το section
        sub_nodes = []
        if popup_node:
            sub_nodes.append(popup_node)
        for fa in folder_all_nodes:
            # Αποφύγαμε διπλοεγγραφή αν το ίδιο node είναι και folder_all
            if fa is not node:
                sub_nodes.append(fa)
        sub_nodes.append(node)

        reset_uid()
        sub_nodes = strip_folder_prefix(sub_nodes, folder)
        sub_sidebar = build_sidebar(sub_nodes)
        sub_html = build_page(
            sub_sidebar,
            title=node['label'],
            back=True,
        )
        sub_output = os.path.join(folder_path, 'index.html')
        with open(sub_output, 'w', encoding='utf-8') as f:
            f.write(sub_html)
        print(f'✓ {sub_output}')

    print('\nΟλοκληρώθηκε.')

if __name__ == '__main__':
    main()
