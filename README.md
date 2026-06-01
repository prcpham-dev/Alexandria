# Alexandria – Transcript Cleaner

Removes line numbers and timestamps from Word documents, and fixes paragraph merging based on capitalisation.

---

## How to use (for mom)

### Step 1 – Download

1. Click the green **Code** button on this page
2. Click **Download ZIP**
3. Extract (unzip) the folder somewhere easy to find, like your Desktop

### Step 2 – First-time setup (only once)

You need **Python 3** installed on your computer.

- **Windows**: Download from [python.org](https://www.python.org/downloads/) — during install, check **"Add Python to PATH"**
- **Mac**: Python 3 is usually already installed

### Step 3 – Run

| Your computer | What to double-click |
|---|---|
| **Windows** | `Start.bat` |
| **Mac** | `Run Filter.command` *(right-click → Open the first time)* |

The first time you run it, it will set itself up automatically (takes about 30 seconds). Every time after that it opens straight away.

---

## What it does

- Strips leading **line numbers** — `1.` `2)` `[3]` etc.
- Strips **timestamps** — `00:12` `1:23:45` etc.
- If a line starts with a **lowercase** letter → joined to the paragraph above
- If a line starts with an **Uppercase** letter → starts a new paragraph

Cleaned files are saved to your **Desktop** in a folder called `Alexandria Output`.

---

## Example

**Before:**
```
1. Hello my name is John.
00:12 i am a student at school.
2. She is very kind.
3. and helpful too.
```

**After:**
```
Hello my name is John. i am a student at school.
She is very kind. and helpful too.
```
