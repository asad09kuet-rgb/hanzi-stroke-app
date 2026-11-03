# Hanzi Stroke Studio

A Streamlit app for practising the characters from class exercises. Click a character and the box on the right draws it stroke by stroke in a 田字格 grid.

When the app opens it asks which mode to use:

- **Mode 1 · All characters**: every character from the exercises once, sorted A to Z by pinyin and grouped by first letter. Choose all exercises or one.
- **Mode 2 · Sentence by sentence**: each exercise one sentence at a time, with pinyin above every character.

The **Change mode** button at the top goes back to the choice.

- **Stroke order animation** with a numbered stroke sequence underneath.
- **Sound**: says the character (e.g. nǐ) and each stroke's name as it is drawn (héng, shù, piě…). Each can be switched off. Stroke names are worked out automatically from the stroke shape, so a few may be off.
- **Practice mode**: draw the character yourself with the mouse or a finger; it corrects wrong strokes.
- **Keyboard**: ← → change sentence, Space replays.

## Run it locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Deploy on Streamlit Community Cloud

1. Go to <https://share.streamlit.io> and sign in with GitHub.
2. Click **Create app** → **Deploy a public app from GitHub**.
3. Repository `asad09kuet-rgb/hanzi-stroke-app`, branch `main`, main file `app.py`.
4. Click **Deploy**.

## Adding exercises

Put a `.txt` file in the `exercises/` folder (UTF-8). One file can hold several exercises:

```text
# Exercise 4 · Lesson 6 · Dialogues
你今天去哪儿？
我去图书馆。
```

- A line starting with `#` starts a new exercise and gives it a title.
- Sentences are split at `。！？；` and at line breaks. Character lists like `家、有、口` stay on one line.
- You can also upload a `.txt` file or paste text in the app's sidebar for a quick try without changing the repo.

## How it works

- `app.py` reads the exercises and hands them to `component.html`, which runs in the page.
- Strokes are drawn with [Hanzi Writer](https://hanziwriter.org) (`static/hanzi-writer.min.js`); pinyin comes from [pinyin-pro](https://github.com/zh-lx/pinyin-pro) (`static/pinyin-pro.min.js`).
- `static/data/` holds Hanzi Writer's stroke data for about 9,500 characters, split into 128 files, so the app doesn't depend on an outside CDN.
- Speech uses the browser's built-in text-to-speech. Chrome and Edge include a Chinese voice; on other browsers you may need to install one.

Stroke data © Make Me a Hanzi / Arphic (Arphic Public License), via `hanzi-writer-data`.
