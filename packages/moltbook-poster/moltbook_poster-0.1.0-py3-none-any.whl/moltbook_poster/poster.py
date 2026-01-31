#!/usr/bin/env python3
"""
LLM-Powered Moltbook Poster
Analyzes merged PRs and generates rich technical summaries for Moltbook

Uses Claude CLI to analyze PR context and generate insightful posts
Posts every 4 hours with batched PR summaries
"""
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

# Configuration
STATE_FILE = Path("/tmp/moltbook_state_llm.json")
CREDENTIALS_FILE = Path.home() / ".config/moltbook/credentials.json"
FOUR_HOURS = 4 * 3600


def get_merged_prs_since(since_timestamp: float) -> List[Dict]:
    """Fetch merged PRs from GitHub API with full details"""
    try:
        result = subprocess.run(
            [
                "gh", "pr", "list",
                "--state", "merged",
                "--limit", "50",
                "--json", "number,title,body,mergedAt,files,labels,url"
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        prs = json.loads(result.stdout)

        # Filter for PRs merged since timestamp
        from datetime import timezone
        since_dt = datetime.fromtimestamp(since_timestamp, tz=timezone.utc)
        filtered_prs = []

        for pr in prs:
            merged_at = datetime.fromisoformat(pr["mergedAt"].replace("Z", "+00:00"))
            if merged_at > since_dt:
                filtered_prs.append(pr)

        return filtered_prs

    except subprocess.CalledProcessError as e:
        print(f"⚠️ Failed to fetch PRs: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse PR data: {e}")
        return []


def analyze_prs_with_claude(prs: List[Dict]) -> Dict[str, str]:
    """Use Claude CLI to analyze PRs and generate rich technical summary"""

    # Prepare context
    pr_summaries = []
    for pr in prs:
        pr_info = {
            "number": pr["number"],
            "title": pr["title"],
            "url": pr["url"],
            "description": (pr.get("body", "") or "")[:800],
            "files_changed": len(pr.get("files", [])),
            "labels": [label["name"] for label in pr.get("labels", [])],
            "merged_at": pr["mergedAt"]
        }
        pr_summaries.append(pr_info)

    prompt = f"""You are an AI agent posting to Moltbook, a social network for AI agents.

Analyze these recently merged PRs for WorldArchitect.AI and create a technical post that other AI agents will find valuable.

**WorldArchitect.AI Context:**
- Production AI-powered D&D 5e Game Master platform
- Tech stack: Python/Flask, Gemini API, Firebase, Vanilla JS
- Core principles: "LLM Decides, Server Executes", dice authenticity, framework-free frontend

**Recently Merged PRs:**
{json.dumps(pr_summaries, indent=2)}

**Generate a Moltbook post with:**

1. **Engaging Title** (50-70 chars, not just "Updates shipped")
   - Focus on the architectural theme or key insight
   - Examples: "Parallel Execution: Conflict Detection in Multi-Agent Systems"

2. **Rich Content** (400-800 words) covering:
   - **Architectural Context**: What these changes enable at a systems level
   - **Technical Decisions**: WHY these approaches matter (not just WHAT changed)
   - **Insights for Other Agents**: Lessons or patterns other AI builders should know
   - **Tradeoffs**: What was sacrificed and why it's worth it

**Style Guidelines:**
- Write for technical AI agents (not human developers)
- Focus on reasoning, architecture, and patterns
- Explain the "why" behind decisions
- Use specific examples from the PRs
- End with: "🦞\\n\\nGenesis Coder, Prime Mover"

**Return ONLY valid JSON (no markdown, no code fences):**
{{
  "title": "Your engaging title here",
  "content": "Your rich technical content here"
}}"""

    try:
        # Write prompt to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            prompt_file = f.name
            f.write(prompt)

        # Call claude CLI with sonnet model (5min timeout for large PR batches)
        result = subprocess.run(
            ["claude", "--model", "sonnet", "--print"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True,
            timeout=300
        )

        # Parse response - extract JSON from Claude's output
        response_text = result.stdout.strip()

        # Find JSON block (look for first { and last })
        json_start = response_text.find("{")
        json_end = response_text.rfind("}") + 1

        if json_start == -1 or json_end == 0:
            raise ValueError("No JSON object found in Claude response")

        json_text = response_text[json_start:json_end]
        post_data = json.loads(json_text)

        # Cleanup temp file
        Path(prompt_file).unlink(missing_ok=True)

        return post_data

    except subprocess.TimeoutExpired:
        print("⚠️ Claude CLI timed out")
        return create_fallback_post(prs)
    except subprocess.CalledProcessError as e:
        print(f"⚠️ Claude CLI error: {e.stderr}")
        return create_fallback_post(prs)
    except json.JSONDecodeError as e:
        print(f"⚠️ Failed to parse Claude response as JSON: {e}")
        print(f"Response was: {result.stdout[:500]}")
        return create_fallback_post(prs)
    except Exception as e:
        print(f"⚠️ Unexpected error: {e}")
        return create_fallback_post(prs)


def create_fallback_post(prs: List[Dict]) -> Dict[str, str]:
    """Create simple fallback post if Claude fails"""
    pr_list = "\\n".join([f"- PR #{pr['number']}: {pr['title']}" for pr in prs])
    return {
        "title": f"WorldArchitect.AI: {len(prs)} Updates Shipped 🚀",
        "content": f"Recent changes to WorldArchitect.AI:\\n\\n{pr_list}\\n\\n🦞\\n\\nGenesis Coder, Prime Mover"
    }


def post_to_moltbook(title: str, content: str) -> Dict:
    """Post to Moltbook API"""
    try:
        with open(CREDENTIALS_FILE) as f:
            creds = json.load(f)

        post_data = {
            "submolt": "general",
            "title": title,
            "content": content
        }

        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                "https://www.moltbook.com/api/v1/posts",
                "-H", f"Authorization: Bearer {creds['api_key']}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps(post_data)
            ],
            capture_output=True,
            text=True,
            check=True,
            timeout=30
        )

        return json.loads(result.stdout)

    except Exception as e:
        print(f"⚠️ Moltbook API error: {e}")
        return {"success": False, "error": str(e)}


def load_state() -> Dict:
    """Load state from file"""
    if STATE_FILE.exists():
        with open(STATE_FILE) as f:
            return json.load(f)
    else:
        # Default: last post was 5 hours ago (will trigger immediately)
        return {
            "last_post_time": (datetime.now() - timedelta(hours=5)).timestamp(),
            "posts_today": 0,
            "last_post_url": None
        }


def save_state(state: Dict):
    """Save state to file"""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def main():
    """Main execution"""
    # Check for credentials
    if not CREDENTIALS_FILE.exists():
        print(f"⚠️ Moltbook credentials not found at {CREDENTIALS_FILE}")
        sys.exit(1)

    # Load state
    state = load_state()
    now = datetime.now().timestamp()

    # Check if 4 hours have passed
    time_since_last_post = now - state["last_post_time"]
    if time_since_last_post < FOUR_HOURS:
        hours_remaining = (FOUR_HOURS - time_since_last_post) / 3600
        print(f"⏱️ Not yet time (need {hours_remaining:.1f} more hours)")
        return

    # Get merged PRs since last post
    print(f"🔍 Checking for PRs merged since last post...")
    prs = get_merged_prs_since(state["last_post_time"])

    if not prs:
        print("📭 No new PRs merged since last post")
        # Still update last check time
        state["last_post_time"] = now
        save_state(state)
        return

    print(f"📊 Found {len(prs)} merged PR(s):")
    for pr in prs:
        print(f"   - PR #{pr['number']}: {pr['title']}")

    # Analyze with Claude
    print("🧠 Analyzing PRs with Claude CLI...")
    post = analyze_prs_with_claude(prs)

    print(f"📝 Generated post:")
    print(f"   Title: {post['title']}")
    print(f"   Content length: {len(post['content'])} chars")

    # Post to Moltbook
    print(f"📤 Posting to Moltbook...")
    response = post_to_moltbook(post["title"], post["content"])

    if response.get("success"):
        post_url = f"https://moltbook.com/post/{response['post']['id']}"

        # Update state
        state["last_post_time"] = now
        state["posts_today"] += 1
        state["last_post_url"] = post_url
        save_state(state)

        print(f"✅ Posted successfully!")
        print(f"   URL: {post_url}")
        print(f"   PR count: {len(prs)}")
    else:
        error = response.get("error", "Unknown error")
        print(f"❌ Failed to post: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
