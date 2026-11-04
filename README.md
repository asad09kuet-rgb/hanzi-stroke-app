# Hanzi Stroke Studio

A Streamlit app for practising the characters from class exercises. Click a character and the box on the right draws it stroke by stroke in a 田字格 grid.

When the app opens it asks which mode to use:

- **Mode 1 · All characters**: every character from the exercises once, sorted A to Z by pinyin and grouped by first letter. Choose all exercises or one.
- **Mode 2 · Sentence by sentence**: each exercise one sentence at a time, with pinyin above every character.

The **Change mode** button at the top goes back to the choice.

- **English meanings**: the clicked character's meaning sits above the drawing box, with the meaning of the word it belongs to (e.g. 高兴 happy). Mode 1 shows a short meaning under every character. Mode 2 shows the English translation under each sentence; untick *Show English* to test yourself.
- **Stroke order animation** with a numbered stroke sequence underneath.
- **Sound**: says the character (e.g. nǐ) and each stroke's name as it is drawn (héng, shù, piě…). Each can be switched off. Stroke names are worked out automatically from the stroke shape, so a few may be off.
- **Practice mode**: draw the character yourself with the mouse or a finger; it corrects wrong strokes.
- **Keyboard**: ← → change sentence, Space replays.

## Class assistant (AI)

Below the practice area is a chat box. Ask anything about your exercises, for example *What does 都 mean?*, *What's the difference between 几 and 多少?* or *How do I ask someone's surname politely?*

It uses retrieval-augmented generation (RAG): for each question, `assistant.py` searches a knowledge base built from the exercises (every sentence with pinyin and English, every character with meanings and stroke count, dictionary words, and the grammar notes in `data/class_notes.txt`), and sends only the best matches to Claude. Each answer has a **Class material used** section showing what it was based on.

It needs an Anthropic API key (from console.anthropic.com):

- **Streamlit Cloud:** app menu **⋮ → Settings → Secrets**, add `ANTHROPIC_API_KEY = "sk-ant-..."`.
- **Locally:** create `.streamlit/secrets.toml` with the same line (it's git-ignored).

Without a key the rest of the app works as usual. Each question costs a fraction of a cent.

## Run it locally

Install [Python 3.9+](https://www.python.org/downloads/), then double-click `run_windows.bat` (Windows) or run `./run_mac_linux.sh` (Mac/Linux). The app opens at http://localhost:8501. Or by hand:

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository `asad09kuet-rgb/hanzi-stroke-app`, branch `main`, main file `app.py`.
4. Click **Deploy**.

### Keeping it awake

Free Streamlit apps sleep after about 12 hours without visitors. `.github/workflows/keep-awake.yml` opens the app every 6 hours and clicks the wake-up button if needed. GitHub pauses scheduled jobs in repos with no commits for 60 days; if that happens, re-enable it under the repo's **Actions** tab.

## Adding exercises

Put a `.txt` file in the `exercises/` folder (UTF-8). One file can hold several exercises:

```text
# Exercise 4 · Lesson 6 · Dialogues
你今天去哪儿？ | Where are you going today?
我去图书馆。 | I'm going to the library.
```

The English after `|` is optional and shown under the sentence.

- A line starting with `#` starts a new exercise and gives it a title.
- Character meanings come from the bundled dictionary automatically. Short class-friendly meanings for the class characters are in `data/glosses.json`; add a line there to override one.
- Sentences are split at `。！？；` and at line breaks. Character lists like `家、有、口` stay on one line.
- You can also upload a `.txt` file or paste text in the app's sidebar for a quick try without changing the repo.

## How it works

- `app.py` reads the exercises and hands them to `component.html`, which runs in the page.
- Strokes are drawn with [Hanzi Writer](https://hanziwriter.org) (`static/hanzi-writer.min.js`); pinyin comes from [pinyin-pro](https://github.com/zh-lx/pinyin-pro) (`static/pinyin-pro.min.js`).
- `static/data/` holds Hanzi Writer's stroke data for about 9,500 characters, split into 128 files, so the app doesn't depend on an outside CDN.
- Speech uses the browser's built-in text-to-speech. Chrome and Edge include a Chinese voice; on other browsers you may need to install one.

Stroke data © Make Me a Hanzi / Arphic (Arphic Public License), via `hanzi-writer-data`.
Dictionary: [CC-CEDICT](https://cc-cedict.org) (CC BY-SA 4.0), in `data/cedict.json.gz`.
