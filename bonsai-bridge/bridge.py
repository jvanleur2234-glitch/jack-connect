#!/usr/bin/env python3
"""
Bonsai Bridge — Ollama-compatible API for Bonsai 1.7B ONNX (Q4)
JackConnect talks to it like Ollama. Zero code changes needed.

Usage:
    python3 bridge.py [--port 11435]

Then set OLLAMA_URL=http://localhost:11435 in JackConnect
"""
import os, sys, json, time, threading, argparse
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs
import onnxruntime as ort
import numpy as np
import torch

# ── Config ──────────────────────────────────────────
MODEL_DIR  = os.environ.get("BONSAI_MODEL_DIR", "/tmp/bonsai-q4")
MODEL_PATH = os.path.join(MODEL_DIR, "onnx/model_q4.onnx")
PORT       = int(os.environ.get("BONSAI_BRIDGE_PORT", "11435"))

# ── Load tokenizer ──────────────────────────────────
print(f"[Bonsai Bridge] Loading tokenizer from {MODEL_DIR}...")
from transformers import AutoTokenizer
tokenizer = AutoTokenizer.from_pretrained(
    "onnx-community/Bonsai-1.7B-ONNX",
    local_files_only=True,
    trust_remote_code=True,
)
tokenizer.pad_token = tokenizer.eos_token
print("[Bonsai Bridge] Tokenizer loaded ✅")

# ── Load ONNX model ────────────────────────────────
print(f"[Bonsai Bridge] Loading model from {MODEL_PATH}...")
sess_options = ort.SessionOptions()
sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
sess_options.intra_op_num_threads = int(os.environ.get("BONSAI_THREADS", "4"))

providers = ["CPUExecutionProvider"]
if "CUDAExecutionProvider" in ort.get_available_providers():
    providers = ["CUDAExecutionProvider", "CPUExecutionProvider"]

sess = ort.InferenceSession(MODEL_PATH, sess_options, providers=providers)
print(f"[Bonsai Bridge] Model loaded on: {providers} ✅")

# ── Generation config ──────────────────────────────
gen_config = {
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.9,
    "do_sample": True,
}
CONFIG_PATH = os.path.join(MODEL_DIR, "generation_config.json")
if os.path.exists(CONFIG_PATH):
    with open(CONFIG_PATH) as f:
        gc = json.load(f)
        gen_config["max_new_tokens"] = gc.get("max_new_tokens", 512)
        gen_config["temperature"]     = gc.get("temperature", 0.7)
        gen_config["top_p"]           = gc.get("top_p", 0.9)

# ── KV Cache ───────────────────────────────────────
past_key_values = None  # Will be a list of (k, v) numpy arrays

def generate(prompt: str, max_new_tokens: int = None, temperature: float = None,
             top_p: float = None) -> str:
    global past_key_values

    max_new_tokens = max_new_tokens or gen_config["max_new_tokens"]
    temperature    = temperature    or gen_config["temperature"]
    top_p          = top_p          or gen_config["top_p"]
    do_sample      = temperature > 0

    # Tokenize
    inputs = tokenizer(prompt, return_tensors="np", padding=True)
    input_ids      = inputs["input_ids"].astype(np.int64)
    attention_mask = inputs["attention_mask"].astype(np.int64)
    batch_size, seq_len = input_ids.shape

    num_logits_to_keep = seq_len  # full logits needed for first token

    # Build past_key_values feed dict
    num_layers = 28  # Bonsai 1.7B has 28 layers
    feed_dict = {
        "input_ids": input_ids,
        "attention_mask": attention_mask,
        "num_logits_to_keep": np.array([num_logits_to_keep], dtype=np.int64),
    }

    # Initialize KV cache if cold start
    if past_key_values is None:
        past_key_values = []
        for _ in range(num_layers):
            # shape: [batch, heads, seq, dim]
            past_key_values.append([np.zeros((1, 16, 0, 128), dtype=np.float32),  # key
                                    np.zeros((1, 16, 0, 128), dtype=np.float32)]) # value

    # Add past KV cache to feed dict
    for i, (k, v) in enumerate(past_key_values):
        feed_dict[f"past_key_values.{i}.key"]   = k
        feed_dict[f"past_key_values.{i}.value"] = v

    # KV dims: key/value shape [batch, heads, seq_len+past_seq, head_dim]
    generated = []
    total_seq  = seq_len

    for step in range(max_new_tokens):
        outputs = sess.run(None, feed_dict)
        logits  = outputs[0]  # [batch, seq, vocab]
        present = outputs[1:]

        # Get next token
        if do_sample:
            # apply temperature
            logits_temp = logits[:, -1, :] / (temperature if temperature > 0 else 1.0)
            probs = np.exp(logits_temp - np.max(logits_temp, axis=-1, keepdims=True))
            probs = probs / np.sum(probs, axis=-1, keepdims=True)
            # top-p nucleus sampling
            if top_p < 1.0:
                sorted_indices = np.argsort(-probs, axis=-1)
                sorted_probs    = np.take_along_axis(probs, sorted_indices, axis=-1)
                cumsum          = np.cumsum(sorted_probs, axis=-1)
                mask            = cumsum <= top_p
                # keep at least one token
                mask = np.concatenate([np.ones_like(mask[:, :1]), mask[:, :-1]], axis=1)
                probs[mask] = 0
                probs = probs / np.sum(probs, axis=-1, keepdims=True)
            next_token = np.array([[np.random.choice(len(probs[0]), p=probs[0])]])
        else:
            next_token = np.argmax(logits[:, -1, :], axis=-1, keepdims=True)

        generated.append(next_token.item())
        past_key_values = []
        offset = 0
        for i in range(num_layers):
            k = present[offset]; v = present[offset + 1]; offset += 2
            new_k = np.concatenate([feed_dict[f"past_key_values.{i}.key"],   k], axis=2)
            new_v = np.concatenate([feed_dict[f"past_key_values.{i}.value"], v], axis=2)
            past_key_values.append([new_k, new_v])

        # Prepare next input
        feed_dict["input_ids"]              = next_token.astype(np.int64)
        feed_dict[f"past_key_values.{i}.key"]   = past_key_values[i][0]
        feed_dict[f"past_key_values.{i}.value"] = past_key_values[i][1]
        num_logits_to_keep = 1

        if next_token.item() == tokenizer.eos_token_id:
            break

    return tokenizer.decode(generated, skip_special_tokens=True)

def reset_cache():
    global past_key_values
    past_key_values = None

# ── Ollama-compatible API ─────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"[BonsaiBridge] {fmt % args}")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

    def do_GET(self):
        if self.path == "/health":
            self.send_json({"status": "ok", "model": "Bonsai-1.7B-ONNX-Q4"})
        elif self.path == "/api/tags":
            self.send_json({
                "models": [{
                    "name": "bonsai-1.7b-q4",
                    "model": "onnx-community/Bonsai-1.7B-ONNX",
                    "size": 1100000000,
                    "modified_at": "2026-04-16T00:00:00Z",
                }]
            })
        else:
            self.send_json({"error": "not found"}, 404)

    def do_POST(self):
        content_len = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(content_len))

        if self.path == "/api/chat":
            # Ollama /api/chat format
            messages = body.get("messages", [])
            prompt   = "\n".join([f"{m['role']}: {m['content']}" for m in messages])
            prompt  += "\nassistant:"

            model    = body.get("model", "bonsai-1.7b-q4")
            options  = body.get("options", {})
            max_new  = options.get("num_predict", gen_config["max_new_tokens"])
            temp     = options.get("temperature", gen_config["temperature"])

            try:
                response = generate(prompt, max_new_tokens=max_new, temperature=temp)
                self.send_json({
                    "model": model,
                    "message": {"role": "assistant", "content": response},
                    "done": True,
                })
            except Exception as e:
                import traceback; traceback.print_exc()
                self.send_json({"error": str(e)}, 500)

        elif self.path == "/api/generate":
            # Ollama /api/generate format
            prompt = body.get("prompt", "")
            model  = body.get("model", "bonsai-1.7b-q4")
            options = body.get("options", {})
            max_new = options.get("num_predict", gen_config["max_new_tokens"])
            temp    = options.get("temperature", gen_config["temperature"])

            try:
                response = generate(prompt, max_new_tokens=max_new, temperature=temp)
                self.send_json({
                    "model": model,
                    "response": response,
                    "done": True,
                })
            except Exception as e:
                self.send_json({"error": str(e)}, 500)

        elif self.path == "/api/embeddings":
            self.send_json({"embedding": [0.0] * 2048}, 200)

        else:
            self.send_json({"error": "not found"}, 404)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    print(f"[Bonsai Bridge] Starting on http://0.0.0.0:{PORT}")
    print(f"[Bonsai Bridge] Ollama-compatible API — use /api/chat and /api/generate")
    print(f"[Bonsai Bridge] Health: http://localhost:{PORT}/health")
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    server.serve_forever()
