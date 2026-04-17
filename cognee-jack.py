#!/usr/bin/env python3
"""
JackConnect Memory Layer — Cognee Integration
Powers the Superintendent RE agent with persistent graph+vector memory.

Usage:
    python3 jack-connect/cognee-jack.py remember "Jack closed a deal on 123 Main St"
    python3 jack-connect/cognee-jack.py recall "what deals has Jack closed"
    python3 jack-connect/cognee-jack.py status
"""

import asyncio
import os
import sys
import json
import argparse
from pathlib import Path

# ── Config ───────────────────────────────────────────────────────────────────
JACK_MEMORY_DIR = os.environ.get("JACK_MEMORY_DIR", str(Path.home() / ".jack-connect" / "memory"))
CONFIG_FILE = Path(JACK_MEMORY_DIR) / "config.json"
os.makedirs(JACK_MEMORY_DIR, exist_ok=True)

# Default LLM = Ollama locally (free)
os.environ.setdefault("LLM_API_KEY", "ollama")
os.environ.setdefault("LLM_BASE_URL", "http://localhost:11434/v1")
os.environ.setdefault("LLM_MODEL", "qwen3:1.7b")

# ── Jack's Memory Categories ─────────────────────────────────────────────────
JACK_ONTOLOGY = {
    "leads": {
        "description": "Prospective clients and lead information",
        "examples": ["buyer looking for 3BR in Sioux Falls", "seller interested in listing evaluation"]
    },
    "deals": {
        "description": "Active transactions and closed deals",
        "examples": ["123 Main St under contract", "456 Oak Ave closed for $285K"]
    },
    "cma_reports": {
        "description": "Comparable market analysis reports",
        "examples": ["CMA for 123 Main St showing $275K-$290K range"]
    },
    "market_intel": {
        "description": "Farm area monitoring, new listings, price changes",
        "examples": ["New listing at 789 Pine Rd asking $320K", "Price drop on 321 Elm St to $199K"]
    },
    "client_nurture": {
        "description": "Client follow-ups, birthdays, anniversaries, SOI contacts",
        "examples": ["Jack's sphere of influence: 47 contacts", "Birthday text due for Sarah Miller on Apr 20"]
    },
    "transactions": {
        "description": "Deadline tracking, contingencies, signatures",
        "examples": ["Inspection due Apr 22 on 123 Main St", "Closing scheduled May 5"]
    },
    "preferences": {
        "description": "Jack's business preferences and working style",
        "examples": ["Jack prefers texts over emails", "Jack works 8am-6pm CT"]
    },
    "lessons_learned": {
        "description": "Deal lessons, client insights, what worked",
        "examples": ["Always verify lender pre-approval before showing", "FSBO owners need more follow-up"]
    }
}

# ── Cognee Import ────────────────────────────────────────────────────────────
try:
    import cognee
    COGNEE_AVAILABLE = True
except ImportError:
    COGNEE_AVAILABLE = False
    print("[WARN] Cognee not installed. Run: uv pip install cognee")

# ── API ──────────────────────────────────────────────────────────────────────

async def jack_remember(content: str, category: str = None):
    """Store something in Jack's memory."""
    if not COGNEE_AVAILABLE:
        print("[ERROR] Cognee not available")
        return False
    
    # Tag with category for graph segmentation
    tagged = f"[{category or 'general'}] {content}"
    await cognee.remember(tagged)
    print(f"[MEMORY] ✓ Stored in {category or 'general'}: {content[:80]}")
    return True

async def jack_recall(query: str, category: str = None):
    """Query Jack's memory."""
    if not COGNEE_AVAILABLE:
        print("[ERROR] Cognee not available")
        return []
    
    # Filter by category if specified
    search_query = query if category is None else f"[{category}] {query}"
    results = await cognee.recall(search_query)
    
    print(f"[RECALL] Query: '{query}'")
    if category:
        print(f"         Filter: {category}")
    for i, r in enumerate(results, 1):
        print(f"  {i}. {r[:200]}")
    return results

async def jack_status():
    """Show memory system status."""
    print("=" * 50)
    print("JackConnect Memory — Cognee Status")
    print("=" * 50)
    print(f"  Memory dir: {JACK_MEMORY_DIR}")
    print(f"  Cognee:     {'✅ Available' if COGNEE_AVAILABLE else '❌ Not installed'}")
    print(f"  LLM:        {os.environ.get('LLM_MODEL', 'qwen3:1.7b')} @ {os.environ.get('LLM_BASE_URL', 'localhost:11434')}")
    print()
    print("  Memory Categories:")
    for cat, info in JACK_ONTOLOGY.items():
        print(f"    • {cat}: {info['description']}")
    print()
    print("  Commands:")
    print("    remember <text>  — Store something")
    print("    recall <query>   — Query memory")
    print("    status          — This screen")
    print("=" * 50)

async def demo():
    """Run a demo of Jack's memory system."""
    print("\n🎓 JackConnect Memory Demo\n")
    
    # Store some sample data
    samples = [
        ("Jack Vanleur works at Alpine Real Estate in Sioux Falls, SD. Specializes in residential and investment properties.", "preferences"),
        ("Lead: Mike Johnson, buyer, looking for 3BR under $300K in Sioux Falls 57104. Pre-approved $275K. Active since Apr 10.", "leads"),
        ("Active deal: 123 Main St, Sioux Falls. Listed $285K. Offer accepted at $282K. Inspection Apr 22. Closing May 5.", "deals"),
        ("CMA for 123 Main St: Active comps show $275K-$295K range. Average DOM 21 days. Jack's recommended list price: $285K.", "cma_reports"),
        ("Birthday for Sarah Miller (past client) is April 22. Last purchase was 456 Oak Ave in 2023.", "client_nurture"),
        ("Market alert: New listing 789 Pine Rd asking $319K. 4BR/3BA, 2200 sqft. Will need to check comparables.", "market_intel"),
        ("Lesson: Always get lender pre-approval letter before booking showings. Mike almost wasted 2 hours on a property he couldn't afford.", "lessons_learned"),
    ]
    
    print("Storing sample memories...")
    for content, category in samples:
        await jack_remember(content, category)
    
    print("\n\nQuerying memory...\n")
    
    queries = [
        ("What active deals does Jack have?", "deals"),
        ("What does Jack remember about leads?", "leads"),
        ("What's the CMA for 123 Main St?", "cma_reports"),
        ("Any birthdays or nurture tasks coming up?", "client_nurture"),
        ("What lessons has Jack learned?", "lessons_learned"),
    ]
    
    for query, cat in queries:
        await jack_recall(query, cat)
        print()

# ── CLI ──────────────────────────────────────────────────────────────────────

async def main():
    parser = argparse.ArgumentParser(description="JackConnect Memory — Powered by Cognee")
    parser.add_argument("command", choices=["remember", "recall", "status", "demo", "setup"],
                        help="Command to run")
    parser.add_argument("text", nargs="?", help="Text to remember or query")
    parser.add_argument("--category", "-c", default=None,
                        help="Memory category (leads, deals, cma_reports, market_intel, client_nurture, transactions, preferences, lessons_learned)")
    
    args = parser.parse_args()
    
    if args.command == "status":
        await jack_status()
    elif args.command == "demo":
        await demo()
    elif args.command == "setup":
        await jack_setup()
    elif args.command == "remember":
        if not args.text:
            print("Error: provide text to remember")
            sys.exit(1)
        success = await jack_remember(args.text, args.category)
        sys.exit(0 if success else 1)
    elif args.command == "recall":
        if not args.text:
            print("Error: provide a query")
            sys.exit(1)
        results = await jack_recall(args.text, args.category)
        sys.exit(0 if results else 1)

if __name__ == "__main__":
    asyncio.run(main())
