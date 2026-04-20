This is a small script that uses ollama to summarize pdfs, images, and text files. handy for quickly getting the gist of a bunch of documents.

What it does

- takes a folder full of files
- runs each file through a local llm (gemma)
- spits out a one-sentence summary for each file
- saves results to a cache so you don't have to reprocess

Requirements

- python 3.x
- ollama installed and running
- the gemma model: `ollama pull gemma4:e4b`
- pymupdf: `pip install pymupdf`

Usage

python summarize_files.py /path to folder

or just run it and type the folder path when asked.

What it handles

- pdfs
- txt, md, py, js, json, html, css, xml, csv, log
- images (png, jpg, jpeg)

Notes

- uses a cache file (PDF_Summaries.txt) so you don't have to rerun everything each time
- if you change a file, delete its entry from the cache or the whole cache file to reprocess it
