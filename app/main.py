"""Notes API — agent'ların üzerinde çalıştığı örnek uygulama."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI(title="Notes API")


class NoteIn(BaseModel):
    title: str
    body: str = ""


class Note(NoteIn):
    id: int


_notes: dict[int, Note] = {}
_next_id = 1


def reset_state() -> None:
    """Test izolasyonu için in-memory state'i sıfırlar."""
    global _next_id
    _notes.clear()
    _next_id = 1


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/notes", status_code=201)
def create_note(data: NoteIn) -> Note:
    global _next_id
    note = Note(id=_next_id, **data.model_dump())
    _notes[note.id] = note
    _next_id += 1
    return note


@app.get("/notes")
def list_notes(q: str | None = None) -> list[Note]:
    if q is None:
        return list(_notes.values())
    return [note for note in _notes.values() if q.lower() in note.title.lower()]


@app.get("/notes/{note_id}")
def get_note(note_id: int) -> Note:
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="note not found")
    return _notes[note_id]


@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int) -> None:
    if note_id not in _notes:
        raise HTTPException(status_code=404, detail="note not found")
    del _notes[note_id]
