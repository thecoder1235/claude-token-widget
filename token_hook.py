"""
Claude Code - Stop Hook
Her yanıt bitince token istatistiklerini JSON dosyasına yazar.
Claude Code bunu otomatik çalıştırır, elle çalıştırmaya gerek yok.
"""
import sys
import json
import os
from datetime import datetime

# Claude Code bu hook'u her "Stop" olayında çalıştırır.
# Konuşma verisi (transcript) stdin üzerinden JSON olarak gelir.

STATS_FILE = os.path.join(os.path.expanduser("~"), ".claude", "token_stats.json")

MODEL_LIMITS = {
    "claude-opus-4-7":   200_000,
    "claude-sonnet-4-6": 200_000,
    "claude-haiku-4-5":  200_000,
    "claude-opus-4-5":   200_000,
    "claude-sonnet-4-5": 200_000,
}
DEFAULT_LIMIT = 200_000


def count_tokens_approx(text: str) -> int:
    # 1 token ≈ 4 karakter (İngilizce/Türkçe için yeterince yakın)
    return max(1, len(text) // 4)


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    transcript_path = data.get("transcript_path", "")
    session_id      = data.get("session_id", "unknown")

    total_input  = 0
    total_output = 0
    model        = "claude-sonnet-4-6"
    last_input   = 0
    last_output  = 0

    # Transcript JSONL dosyasını oku
    if transcript_path and os.path.exists(transcript_path):
        try:
            with open(transcript_path, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]

            messages = []
            for line in lines:
                try:
                    messages.append(json.loads(line))
                except Exception:
                    continue

            for msg in messages:
                # Model bilgisini al
                if msg.get("type") == "assistant" and msg.get("model"):
                    model = msg["model"]

                # API usage alanı varsa direkt kullan (en doğrusu)
                usage = msg.get("usage") or msg.get("message", {}).get("usage", {})
                if usage:
                    inp = usage.get("input_tokens", 0) or 0
                    out = usage.get("output_tokens", 0) or 0
                    total_input  += inp
                    total_output += out
                    if msg.get("type") == "assistant":
                        last_input  = inp
                        last_output = out
                    continue

                # Usage yoksa içerikten tahmin et
                content = msg.get("content", "")
                if isinstance(content, list):
                    content = " ".join(
                        c.get("text", "") for c in content if isinstance(c, dict)
                    )
                tokens = count_tokens_approx(str(content))
                role = msg.get("role") or msg.get("type", "")
                if role in ("user", "human"):
                    total_input  += tokens
                    last_input    = tokens
                elif role in ("assistant",):
                    total_output += tokens
                    last_output   = tokens

        except Exception as e:
            pass  # Hata olsa da widget çalışmaya devam eder

    limit     = MODEL_LIMITS.get(model, DEFAULT_LIMIT)
    used      = total_input + total_output
    remaining = max(limit - used, 0)

    stats = {
        "session_id":    session_id,
        "model":         model,
        "limit":         limit,
        "total_input":   total_input,
        "total_output":  total_output,
        "used":          used,
        "remaining":     remaining,
        "pct":           round(used / limit * 100, 1),
        "last_input":    last_input,
        "last_output":   last_output,
        "updated_at":    datetime.now().isoformat(),
    }

    os.makedirs(os.path.dirname(STATS_FILE), exist_ok=True)
    with open(STATS_FILE, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
