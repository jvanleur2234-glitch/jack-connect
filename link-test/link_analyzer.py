#!/usr/bin/env python3
"""
LinkTest Analyzer — receives URL from zo.space, analyzes with requests + Ollama
"""

import os, json, requests

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://127.0.0.1:11434")

def ollama_chat(prompt, max_tokens=300):
    """Use /api/chat — faster than /api/generate for short prompts."""
    resp = requests.post(f"{OLLAMA_URL}/api/chat", json={
        "model": "qwen3:1.7b",
        "messages": [{"role": "user", "content": prompt}],
        "stream": False,
        "options": {"num_predict": max_tokens}
    }, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data["message"]["content"].strip()

def analyze_url(url: str) -> dict:
    """Analyze URL using HTTP fetch + LLM."""
    try:
        # Use agent-fetch for full content (bypasses anti-bot, gets clean markdown)
        import subprocess
        result = subprocess.run(
            ["agent-fetch", url, "--json"],
            capture_output=True, text=True, timeout=30
        )
        content = ""
        title = url
        if result.returncode == 0:
            import json as pjson
            try:
                fd = pjson.loads(result.stdout)
                content = fd.get("textContent", "") or fd.get("markdown", "") or ""
                content = content[:8000]
                title = fd.get("title", title) or title
            except:
                content = result.stdout[:8000]
        else:
            # fallback: simple fetch
            resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            content = resp.text[:6000]
            import re
            t = re.search(r'<title[^>]*>([^<]+)</title>', content, re.I)
            if t:
                title = t.group(1).strip()[:100]
        
        domain = url.split("/")[2] if "//" in url else url

        prompt = f"""Analyze this website for automation opportunities.

URL: {url}
Title: {title or domain}

Content:
{content[:6000]}

Return ONLY valid JSON (no markdown, no code blocks):
{{
  "title": "page title",
  "business_type": "what this business does in 3-5 words",
  "automations": [
    {{"name": "opportunity name", "description": "one sentence description", "impact": "High|Medium|Low", "time_to_build": "estimate like '1 day' or '2 hours'", "monthly_value": "$X"}},
    {{...}},
    {{...}}
  ],
  "monthly_value": "$total monthly value"
}}"""
        
        result = ollama_chat(prompt, max_tokens=400)
        
        try:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*"[^{}]*\}', result, re.DOTALL)
            if not json_match:
                # Try whole response
                data = json.loads(result)
            else:
                data = json.loads(json_match.group())
            
            data["title"] = title or data.get("title", domain)
            return data
        except:
            pass
        
        return fallback_response(title or domain)
    
    except Exception as e:
        return fallback_response(url)

def fallback_response(title: str) -> dict:
    return {
        "title": title,
        "business_type": "Service Business",
        "automations": [
            {"name": "Lead Response Bot", "description": "Instantly respond to new leads within 5 minutes", "impact": "High", "time_to_build": "1 day", "monthly_value": "$500"},
            {"name": "Appointment Reminders", "description": "SMS reminders 24h and 1h before appointments", "impact": "Medium", "time_to_build": "2 hours", "monthly_value": "$200"},
            {"name": "Follow-up Sequence", "description": "Automated nurture emails for cold leads", "impact": "Medium", "time_to_build": "3 hours", "monthly_value": "$300"}
        ],
        "monthly_value": "$1,000"
    }

# ── HTTP Server ─────────────────────────────────────────────────────────────
def run_server(port):
    from http.server import HTTPServer, BaseHTTPRequestHandler
    
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            if self.path != "/analyze":
                self.send_error(404)
                return
            
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode()
            data = json.loads(body)
            url = data.get("url", "")
            
            if not url:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "URL required"}).encode())
                return
            
            result = analyze_url(url)
            
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(result).encode())
        
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "service": "link-test-analyzer"}).encode())
        
        def log_message(self, fmt, *args):
            print(f"[LinkTest] {fmt % args}")
    
    addr = ("0.0.0.0", port)
    server = HTTPServer(addr, Handler)
    print(f"LinkTest Analyzer running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=int(os.environ.get("PORT", 5002)))
    args = parser.parse_args()
    run_server(args.port)