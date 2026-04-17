#!/usr/bin/env python3
"""CloudBrowser API - Playwright + Ollama browser automation"""
import os, json, subprocess, uuid, threading, re as re_mod
from flask import Flask, jsonify, request, send_file
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

PORT    = int(os.environ.get('PORT', 9876))
OLLAMA  = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
MODEL   = os.environ.get('OLLAMA_MODEL', 'llama3.2:1b')
STORAGE = '/tmp/cloudbrowser-sessions'
os.makedirs(STORAGE, exist_ok=True)

URL_PAT = re_mod.compile(r'https?://[^) \s"]+')

def ollama_chat(model, messages):
    payload = {'model': model, 'messages': messages, 'stream': False}
    try:
        r = subprocess.run(
            ['curl', '-s', '-X', 'POST', f'{OLLAMA}/api/chat',
             '-H', 'Content-Type: application/json',
             '-d', json.dumps(payload)],
            capture_output=True, text=True, timeout=120)
        return json.loads(r.stdout).get('message', {}).get('content', '')
    except Exception as e: return '[Ollama error: ' + str(e) + ']'

def action_from_text(text):
    t = str(text).lower()
    if any(w in t for w in ['done', 'finished', 'complete']): return {'action': 'done', 'target': ''}
    m = URL_PAT.search(str(text))
    if m: return {'action': 'navigate', 'target': m.group()}
    if 'click' in t: return {'action': 'click', 'target': 'body'}
    if 'type' in t or 'fill' in t: return {'action': 'type', 'target': 'input[type=text]|sample'}
    if 'wait' in t:
        nums = re_mod.findall(r'\d+', text)
        return {'action': 'wait', 'target': nums[0] if nums else '1'}
    return {'action': 'wait', 'target': '1'}

sessions = {}
lock = threading.Lock()

def fp(sid, k): return f'{STORAGE}/' + str(sid) + '_' + k + '.json'
def sv(sid, k, d):
    with open(fp(sid,k), 'w') as f: json.dump(d, f)
def ld(sid, k):
    p = fp(sid,k)
    if os.path.exists(p):
        with open(p) as f: return json.load(f)
    return []

def do_task(sid, task_text):
    # Declare result/history before try block so they are in scope in except
    task_result = {}
    task_history = []
    try:
        from playwright.sync_api import sync_playwright
        shot_dir = f'{STORAGE}/' + str(sid) + '_shots'
        os.makedirs(shot_dir, exist_ok=True)
        shot_n = [0]

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            ctx = browser.new_context(user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36')
            page = ctx.new_page()

            resp = ollama_chat(MODEL, [
                {'role': 'system', 'content': 'Plain English.'},
                {'role': 'user', 'content': 'Task: ' + task_text + ' What is the first action?'}])
            plan = action_from_text(resp)
            steps = 0

            while steps < 20:
                steps += 1
                action = plan.get('action', 'wait')
                target = plan.get('target', '1')
                if action == 'done': break

                try:
                    if action == 'navigate':
                        page.goto(target, wait_until='domcontentloaded', timeout=15000)
                    elif action == 'click': page.click(target, timeout=5000)
                    elif action == 'type':
                        parts = target.split('|', 1)
                        page.fill(parts[0], parts[1] if len(parts) > 1 else '')
                    elif action == 'wait': page.wait_for_timeout(int(target) if target.isdigit() else 1000)
                    else: page.wait_for_timeout(500)
                    page.wait_for_timeout(300)
                except: pass

                shot_n[0] += 1
                try: page.screenshot(path=shot_dir + '/step_' + str(shot_n[0]).zfill(2) + '.png')
                except: pass

                resp = ollama_chat(MODEL, [
                    {'role': 'system', 'content': 'Plain English.'},
                    {'role': 'user', 'content': 'Prev: ' + action + '. Title: ' + page.title()[:60] + '. Task: ' + task_text + '. Next?'}])
                plan = action_from_text(resp)

            # Build result after loop
            summary_msg = [{'role': 'user', 'content': 'Summarize: ' + task_text}]
            summary = ollama_chat(MODEL, [{'role': 'system', 'content': 'One sentence.'}] + summary_msg)
            shots_list = sorted(os.listdir(shot_dir)) if os.path.exists(shot_dir) else []
            shots = ['/sessions/' + str(sid) + '/shots/' + fn for fn in shots_list]
            task_result = {'status': 'done', 'result': summary, 'final_url': page.url, 'title': page.title(), 'screenshots': shots}
            task_history = summary_msg
            browser.close()

        sv(sid, 'result', task_result)
        sv(sid, 'history', task_history)
        with lock: sessions[sid]['status'] = 'done'
    except Exception as e:
        sv(sid, 'result', {'status': 'done', 'result': str(e)})
        sv(sid, 'history', [])
        with lock: sessions[sid]['status'] = 'done'

@app.route('/health')
def health(): return jsonify({'status': 'ok', 'sessions': len(sessions)})

@app.route('/session', methods=['POST'])
def new_session():
    sid = 'cb_' + uuid.uuid4().hex[:12]
    with lock: sessions[sid] = {'id': sid, 'status': 'ready', 'task': None}
    return jsonify({'session_id': sid, 'status': 'ready'})

@app.route('/sessions')
def list_sessions():
    with lock: return jsonify(list(sessions.values()))

@app.route('/sessions/<sid>')
def get_session(sid):
    if sid not in sessions: return jsonify({'error': 'not found'}), 404
    with lock: s = dict(sessions[sid])
    r = ld(sid, 'result'); h = ld(sid, 'history')
    s.update(r); s['history'] = h
    return jsonify(s)

@app.route('/sessions/<sid>/shots/<filename>')
def get_shot(sid, filename):
    return send_file(STORAGE + '/' + str(sid) + '_shots/' + filename)

@app.route('/task/<sid>', methods=['GET', 'POST'])
def task(sid):
    if sid not in sessions: return jsonify({'error': 'not found'}), 404
    if request.method == 'GET':
        r = ld(sid, 'result')
        with lock: st = sessions[sid]['status']
        return jsonify({'id': sid, 'status': st, **(r or {})})
    data = request.get_json() or {}
    task_text = data.get('task', '')
    if not task_text: return jsonify({'error': 'task required'}), 400
    with lock: sessions[sid]['status'] = 'running'; sessions[sid]['task'] = task_text
    t = threading.Thread(target=do_task, args=(sid, task_text), daemon=True)
    t.start()
    return jsonify({'id': sid, 'status': 'running', 'task': task_text})

if __name__ == '__main__':
    print('CloudBrowser API on port ' + str(PORT) + ' | Ollama: ' + OLLAMA + ' | Model: ' + MODEL)
    app.run(host='0.0.0.0', port=PORT, threaded=True)
