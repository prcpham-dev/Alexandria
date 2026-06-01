# Alexandria

A simple web app that cleans up Word documents exported from transcript tools.

Upload a `.docx` file → timestamps and time labels are removed → preview the result → download the cleaned file.


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
