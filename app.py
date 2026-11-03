"""Hanzi Stroke Studio: show class exercises sentence by sentence and draw each character's stroke order."""
import json
import re
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

ROOT = Path(__file__).parent
EXERCISE_DIR = ROOT / "exercises"
TEMPLATE = (ROOT / "component.html").read_text(encoding="utf-8")

HAN = re.compile(r"[㐀-鿿豈-﫿\U00020000-\U0002ebef]")
END = "。！？!?；;"
CLOSERS = "”\"’」』）)"

st.set_page_config(page_title="Hanzi Stroke Studio", page_icon="✍️", layout="wide")


def split_sentences(line: str) -> list[str]:
    out, buf, i = [], "", 0
    while i < len(line):
        buf += line[i]
        if line[i] in END:
            while i + 1 < len(line) and line[i + 1] in CLOSERS:
                i += 1
                buf += line[i]
            out.append(buf.strip())
            buf = ""
        i += 1
    if buf.strip():
        out.append(buf.strip())
    return [s for s in out if HAN.search(s)]


def parse(text: str, default_title: str) -> list[dict]:
    """'# Title' lines start a new exercise; everything else is split into sentences."""
    exercises, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("#"):
            cur = {"title": line.lstrip("#").strip() or default_title, "lines": []}
            exercises.append(cur)
        elif line:
            if cur is None:
                cur = {"title": default_title, "lines": []}
                exercises.append(cur)
            cur["lines"].append(line)
    result = []
    for ex in exercises:
        sentences = [s for ln in ex["lines"] for s in split_sentences(ln)]
        if sentences:
            result.append({"title": ex["title"], "sentences": sentences})
    return result


def read_text(data: bytes) -> str:
    for enc in ("utf-8-sig", "gb18030", "big5"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="ignore")


# ---------- Collect exercises ----------
exercises: list[dict] = []
for f in sorted(EXERCISE_DIR.glob("*.txt")):
    exercises += parse(read_text(f.read_bytes()), f.stem.replace("_", " ").title())

with st.sidebar:
    st.header("Exercises")
    uploads = st.file_uploader("Upload class exercises (.txt)", type=["txt"], accept_multiple_files=True)
    for up in uploads or []:
        exercises = parse(read_text(up.getvalue()), Path(up.name).stem) + exercises
    pasted = st.text_area("…or paste text here", height=140, placeholder="# Lesson 6\n我们今天学习汉字。你喜欢中文吗？")
    if pasted.strip():
        exercises = parse(pasted, "Pasted text") + exercises

    if not exercises:
        st.warning("No Chinese sentences found yet. Upload or paste an exercise.")
        st.stop()

    titles = [f"{e['title']} ({len(e['sentences'])} sentences)" for e in exercises]
    start = st.selectbox("Start with", range(len(exercises)), format_func=lambda i: titles[i])
    height = st.slider("Box height", 700, 1600, 1000, 20, help="Make this taller on a phone, where the two panels stack.")

    with st.expander("File format"):
        st.markdown(
            "- One `.txt` file can hold several exercises.\n"
            "- Start each with a line like `# Lesson 3`.\n"
            "- Sentences are split at `。！？；` and line breaks.\n"
            "- Put files in the repo's `exercises/` folder to keep them permanently."
        )

html = (
    TEMPLATE.replace("__EXERCISES_JSON__", json.dumps(exercises, ensure_ascii=False))
    .replace("__START_EX__", str(int(start)))
    # Relative to the app's URL, so it also works under Streamlit Cloud's path prefix.
    .replace("__STATIC__", "app/static")
)
components.html(html, height=height, scrolling=True)
