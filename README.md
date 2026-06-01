# Alexandria – Transcript Cleaner

Removes line numbers and timestamps from Word documents, and merges/splits paragraphs based on capitalisation.

---

## Download

Go to the **[Releases page](../../releases/latest)** and download the file for your computer:

| Your computer | Download |
|---|---|
| **Windows** | `Alexandria.exe` |
| **Mac** | `Alexandria-Mac.zip` |

No installation needed. Everything is included in the file.

---

## How to use

**Windows**
1. Download `Alexandria.exe`
2. Double-click it — the window opens

**Mac**
1. Download `Alexandria-Mac.zip` and extract it
2. Double-click `Alexandria.app`
3. First time only: if Mac blocks it, right-click → **Open** → **Open**

---

## What it does

- Removes leading **line numbers** — `1.` `2)` `[3]` etc.
- Removes **timestamps** — `00:12` `1:23:45` `13 minutes, 38 seconds` etc.
- Lines starting with a **lowercase** letter → joined to the paragraph above
- Lines starting with an **Uppercase** letter → new paragraph with a blank line above

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
