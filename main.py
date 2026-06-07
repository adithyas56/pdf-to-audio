from fastapi import FastAPI, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import fitz
import re
import os
import sqlite3
import uuid

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

def init_db():
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS books
                 (id TEXT PRIMARY KEY,
                  title TEXT,
                  text TEXT,
                  progress REAL DEFAULT 0,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS notes
                 (id TEXT PRIMARY KEY,
                  book_id TEXT,
                  timestamp REAL,
                  chapter TEXT,
                  note_text TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

def extract_text(pdf_bytes):
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text() + "\n"
    doc.close()
    return full_text

def clean_text(text):
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'\d+\s', '', text)
    return text.strip()

def detect_chapters(text):
    chapters = []
    pattern = r'(Chapter\s+\d+[:\s][^\n.]{3,60}|CHAPTER\s+\d+[:\s][^\n.]{3,60})'
    matches = list(re.finditer(pattern, text))
    if not matches:
        words = text.split()
        chunk_size = max(1, len(words) // 10)
        for i in range(10):
            start = i * chunk_size
            chapters.append({
                "title": f"Part {i+1}",
                "text": ' '.join(words[start:start+chunk_size])
            })
    else:
        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i+1].start() if i+1 < len(matches) else len(text)
            chapters.append({
                "title": match.group().strip(),
                "text": text[start:end]
            })
    return chapters

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/index.html", "r") as f:
        return HTMLResponse(content=f.read())

@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        raw_text = extract_text(contents)
        clean = clean_text(raw_text)
        chapters = detect_chapters(clean)
        book_id = str(uuid.uuid4())
        title = file.filename.replace('.pdf', '')
        conn = sqlite3.connect("books.db")
        c = conn.cursor()
        c.execute("INSERT INTO books (id, title, text) VALUES (?, ?, ?)",
                  (book_id, title, clean))
        conn.commit()
        conn.close()
        return JSONResponse({
            "success": True,
            "book_id": book_id,
            "title": title,
            "chapters": chapters,
            "total_chars": len(clean)
        })
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)})

@app.get("/books")
async def get_books():
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("SELECT id, title, progress, created_at FROM books ORDER BY created_at DESC")
    books = [{"id": r[0], "title": r[1], "progress": r[2], "created_at": r[3]} for r in c.fetchall()]
    conn.close()
    return JSONResponse({"books": books})

@app.get("/book/{book_id}")
async def get_book(book_id: str):
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("SELECT id, title, text, progress FROM books WHERE id=?", (book_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        return JSONResponse({"error": "Book not found"})
    chapters = detect_chapters(row[2])
    return JSONResponse({
        "id": row[0],
        "title": row[1],
        "chapters": chapters,
        "progress": row[3]
    })

@app.post("/progress/{book_id}")
async def save_progress(book_id: str, data: dict):
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("UPDATE books SET progress=? WHERE id=?", (data.get("progress", 0), book_id))
    conn.commit()
    conn.close()
    return JSONResponse({"success": True})

@app.post("/note/{book_id}")
async def save_note(book_id: str, data: dict):
    note_id = str(uuid.uuid4())
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("INSERT INTO notes (id, book_id, timestamp, chapter, note_text) VALUES (?,?,?,?,?)",
              (note_id, book_id, data.get("timestamp", 0), data.get("chapter", ""), data.get("note", "")))
    conn.commit()
    conn.close()
    return JSONResponse({"success": True})

@app.get("/notes/{book_id}")
async def get_notes(book_id: str):
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("SELECT timestamp, chapter, note_text, created_at FROM notes WHERE book_id=? ORDER BY timestamp", (book_id,))
    notes = [{"timestamp": r[0], "chapter": r[1], "note": r[2], "created_at": r[3]} for r in c.fetchall()]
    conn.close()
    return JSONResponse({"notes": notes})

@app.delete("/book/{book_id}")
async def delete_book(book_id: str):
    conn = sqlite3.connect("books.db")
    c = conn.cursor()
    c.execute("DELETE FROM books WHERE id=?", (book_id,))
    c.execute("DELETE FROM notes WHERE book_id=?", (book_id,))
    conn.commit()
    conn.close()
    return JSONResponse({"success": True})
