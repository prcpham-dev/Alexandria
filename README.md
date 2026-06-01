# Doc Cleaner

A simple web app that cleans up Word documents exported from transcript tools.

Upload a `.docx` file → timestamps and time labels are removed → preview the result → download the cleaned file.

## What it removes

Lines that are **only** a timestamp or duration are deleted:

| Example | Removed? |
|---|---|
| `13:45` | ✅ Yes |
| `1:23:45` | ✅ Yes |
| `5 minutes, 30 seconds` | ✅ Yes |
| `2 hours, 1 minute, 5 seconds` | ✅ Yes |
| `She arrived at 13:45` | ❌ No — kept as-is |

Paragraphs are also joined/split based on capitalisation (lowercase continuation → joined to previous paragraph).

## Project structure

```
├── index.html        Web page
├── style.css         Styles
├── app.js            Frontend logic
├── api/
│   └── process.py    Vercel serverless function
├── requirements.txt  Python dependency (python-docx)
└── vercel.json       Vercel config
```
