from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
import fitz  # PyMuPDF
import tempfile
import os
import re

app = FastAPI()

@app.get("/")
def health():
    return {"status": "ok", "service": "Cookd PDF API"}

@app.post("/extract-chapter")
async def extract_chapter(
    file: UploadFile = File(...),
    chapter_number: str = Form(default=""),
    chapter_name: str = Form(default="")
):
    try:
        contents = await file.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(contents)
            tmp_path = tmp.name
        
        doc = fitz.open(tmp_path)
        full_text = ""
        
        for page in doc:
            full_text += page.get_text() + "\n"
        
        doc.close()
        os.unlink(tmp_path)
        
        # Find chapter
        search_terms = []
        if chapter_number:
            search_terms.append(f"Chapter {chapter_number}")
            search_terms.append(f"CHAPTER {chapter_number}")
            search_terms.append(f"chapter {chapter_number}")
        if chapter_name:
            search_terms.append(chapter_name)
        
        chapter_start = -1
        matched_term = ""
        
        for term in search_terms:
            idx = full_text.find(term)
            if idx != -1:
                chapter_start = idx
                matched_term = term
                break
        
        # Find next chapter
        chapter_end = len(full_text)
        if chapter_number and chapter_start != -1:
            next_num = int(chapter_number) + 1
            next_terms = [
                f"Chapter {next_num}",
                f"CHAPTER {next_num}",
                f"chapter {next_num}"
            ]
            for term in next_terms:
                idx = full_text.find(term, chapter_start + 200)
                if idx != -1:
                    chapter_end = idx
                    break
        
        # Extract chapter text
        if chapter_start != -1:
            chapter_text = full_text[chapter_start:chapter_end]
        else:
            chapter_text = full_text[:20000]
        
        # Cap at 15000 chars
        chapter_text = chapter_text[:50000].strip()
        
        word_count = len(chapter_text.split())
        
        return JSONResponse({
            "text": chapter_text,
            "chapter_found": chapter_start != -1,
            "matched_term": matched_term,
            "word_count": word_count,
            "status": "success"
        })
        
    except Exception as e:
        return JSONResponse({
            "text": "",
            "status": "error",
            "message": str(e)
        }, status_code=500)
