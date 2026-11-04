"""Class assistant: answers questions about the exercises using retrieval over the lesson data (RAG).

The knowledge base is built from what the app already knows: every exercise sentence with its pinyin
and English, every character with its pinyin, meanings and stroke count, and every dictionary word
found in the sentences. For each question we pick the most relevant entries with a small keyword
search (Chinese characters, pinyin and English words) and give only those to Claude.
"""
from __future__ import annotations

import json
import math
import os
import re
import unicodedata
from collections import Counter
from pathlib import Path

import streamlit as st

MODEL = "claude-opus-5-5"
TOP_K = 18
HAN = re.compile(r"[㐀-鿿豈-﫿]")
WORD = re.compile(r"[a-z]+")
STOP = set("a an the of to in on is are am be do does did i you he she it we they what which who how why "
           "and or for with this that these those me my your mean means meaning say said can could "
           "please tell about give show".split())


def _plain(s: str) -> str:
    """Lower-case and drop tone marks, so 'xìng', 'xing' and 'Xing' match."""
    return "".join(c for c in unicodedata.normalize("NFD", s.lower()) if unicodedata.category(c) != "Mn").replace("ü", "v")


def _tokens(text: str) -> list[str]:
    t = _plain(text)
    return HAN.findall(text) + [w for w in WORD.findall(t) if w not in STOP and len(w) > 1]


def _stroke_count(root: Path, ch: str) -> int | None:
    f = root / "static" / "data" / f"c{ord(ch) % 128}.json"
    try:
        data = _chunk(str(f))
        return len(data[ch]["strokes"]) if ch in data else None
    except Exception:
        return None


@st.cache_data(show_spinner=False)
def _chunk(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def build_docs(root: Path, exercises: list[dict], chars: dict, pinyin_of) -> list[dict]:
    """One small text document per sentence, character and word."""
    docs: list[dict] = []
    seen_words: dict[str, dict] = {}
    where: dict[str, list[str]] = {}
    for ex in exercises:
        for i, s in enumerate(ex["sentences"]):
            en = ex.get("en", [""] * len(ex["sentences"]))[i]
            py = pinyin_of(s)
            docs.append({
                "kind": "sentence",
                "text": f"[{ex['title']}, sentence {i + 1}] {s} ({py}){' = ' + en if en else ''}",
            })
            for c in s:
                if HAN.match(c):
                    where.setdefault(c, [])
                    if ex["title"] not in where[c]:
                        where[c].append(ex["title"])
            for start, n, wpy, wdef in ex.get("words", [[]] * len(ex["sentences"]))[i]:
                seen_words.setdefault(s[start:start + n], {"py": wpy, "def": wdef, "eg": s})
    for c, info in chars.items():
        meanings = "; ".join(f"{p}: {d}" for p, d in info.get("d", [])[:3])
        strokes = _stroke_count(root, c)
        docs.append({
            "kind": "character",
            "text": (f"Character {c}: class meaning '{info.get('g') or '-'}'. Dictionary: {meanings}. "
                     f"{f'{strokes} strokes. ' if strokes else ''}Appears in: {', '.join(where.get(c, []))}."),
        })
    notes = root / "data" / "class_notes.txt"
    if notes.exists():
        for line in notes.read_text(encoding="utf-8").splitlines():
            if line.strip() and not line.startswith("#"):
                docs.append({"kind": "note", "text": f"Class note: {line.strip()}"})
    for w, info in seen_words.items():
        docs.append({"kind": "word", "text": f"Word {w} ({info['py']}): {info['def']}. Example: {info['eg']}"})
    # Pre-compute token counts for scoring.
    for d in docs:
        d["tf"] = Counter(_tokens(d["text"]))
    return docs


def retrieve(docs: list[dict], question: str, k: int = TOP_K) -> list[dict]:
    q = _tokens(question)
    if not q:
        return docs[:k]
    n = len(docs)
    df = Counter(t for d in docs for t in set(d["tf"]))
    scored = []
    for d in docs:
        s = 0.0
        for t in q:
            if t in d["tf"]:
                idf = math.log(1 + n / (1 + df[t]))
                s += idf * (1 + math.log(d["tf"][t]))
        # A character entry is the best answer for a question that names that character.
        if d["kind"] == "character" and d["text"][10] in q:
            s += 3
        if s > 0:
            scored.append((s, d))
    scored.sort(key=lambda x: -x[0])
    return [d for _, d in scored[:k]]


SYSTEM = """You are the class assistant inside Hanzi Stroke Studio, a practice app for a beginner Mandarin Chinese class (HSK 1 level, lessons 1-5 so far).
The student is an English-speaking learner. Answer questions about the class exercises: characters, pinyin, tones, meanings, words, sentences, grammar points and stroke counts.

Rules:
- Base your answer on the class material in <class_material>. Quote the exact sentences, characters and translations from it when they help.
- If the material doesn't cover the question, you may use general knowledge of beginner Chinese, but say that it isn't from the class exercises.
- Always write Chinese with pinyin (tone marks) and English, e.g. 高兴 (gāoxìng, happy).
- Keep answers short and friendly: a few sentences or a short list. Use Markdown.
- For stroke order, tell the student to click the character in the app above, which animates it."""


def _api_key() -> str | None:
    try:
        key = st.secrets.get("ANTHROPIC_API_KEY")
    except Exception:
        key = None
    return key or os.environ.get("ANTHROPIC_API_KEY")


def render(docs: list[dict]) -> None:
    st.divider()
    st.subheader("💬 Class assistant")
    st.caption("Ask about any character, word or sentence from your exercises, e.g. *What does 都 mean?* "
               "or *How do I say how many people are in your family?*")

    key = _api_key()
    if not key:
        st.info(
            "The assistant needs an Anthropic API key. On Streamlit Cloud: open your app → **⋮ → Settings → Secrets** "
            "and add `ANTHROPIC_API_KEY = \"sk-ant-...\"`. Running locally: put the same line in "
            "`.streamlit/secrets.toml`. Get a key at console.anthropic.com."
        )
        return

    import anthropic  # imported here so the rest of the app works even before the package is installed

    history = st.session_state.setdefault("chat", [])
    for m in history:
        with st.chat_message(m["role"]):
            st.markdown(m["content"])
            if m.get("sources"):
                with st.expander("Class material used"):
                    st.markdown("\n".join(f"- {s}" for s in m["sources"]))

    question = st.chat_input("Ask the class assistant…")
    if not question:
        if history and st.button("Clear chat"):
            st.session_state["chat"] = []
            st.rerun()
        return

    hits = retrieve(docs, question)
    material = "\n".join(f"- {d['text']}" for d in hits) or "- (nothing matched)"
    history.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    # Earlier turns go in as plain text; the retrieved material is attached to the newest question only.
    messages = [{"role": m["role"], "content": m["content"]} for m in history[:-1]][-10:]
    messages.append({
        "role": "user",
        "content": f"<class_material>\n{material}\n</class_material>\n\nQuestion: {question}",
    })
    if messages[0]["role"] != "user":
        messages = messages[1:]

    client = anthropic.Anthropic(api_key=key)

    def stream():
        with client.beta.messages.stream(
            model=MODEL,
            max_tokens=4000,
            system=SYSTEM,
            messages=messages,
            output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
        ) as s:
            for text in s.text_stream:
                yield text
            final = s.get_final_message()
            if final.stop_reason == "refusal":
                yield "\n\n*Sorry, I can't help with that one. Try asking about the class material.*"

    with st.chat_message("assistant"):
        try:
            answer = st.write_stream(stream())
        except anthropic.AuthenticationError:
            answer = "The API key in the app's secrets was rejected. Check that it's correct and active."
            st.error(answer)
        except anthropic.RateLimitError:
            answer = "Too many questions at once. Wait a minute and ask again."
            st.warning(answer)
        except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
            answer = f"The assistant couldn't answer right now ({type(e).__name__}). Please try again."
            st.warning(answer)
        sources = [d["text"] for d in hits]
        with st.expander("Class material used"):
            st.markdown("\n".join(f"- {s}" for s in sources))
    history.append({"role": "assistant", "content": answer if isinstance(answer, str) else "".join(answer), "sources": sources})
