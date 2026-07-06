from dataclasses import dataclass


@dataclass
class Chunk:
    text: str
    page: int


def chunk_pages(pages: list[str], chunk_size: int = 1000, chunk_overlap: int = 150) -> list[Chunk]:
    """Recursively split each page's text into overlapping chunks, preferring paragraph
    and sentence boundaries before falling back to a hard character cut."""
    chunks: list[Chunk] = []
    for page_num, page_text in enumerate(pages, start=1):
        for piece in _split_text(page_text, chunk_size, chunk_overlap):
            piece = piece.strip()
            if piece:
                chunks.append(Chunk(text=piece, page=page_num))
    return chunks


def _split_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    separators = ["\n\n", "\n", ". ", " "]
    return _recursive_split(text, chunk_size, chunk_overlap, separators)


def _recursive_split(text: str, chunk_size: int, chunk_overlap: int, separators: list[str]) -> list[str]:
    if len(text) <= chunk_size:
        return [text]

    separator = separators[0] if separators else ""
    remaining_separators = separators[1:] if len(separators) > 1 else []

    if separator:
        parts = text.split(separator)
    else:
        parts = list(text)

    chunks: list[str] = []
    current = ""
    for part in parts:
        candidate = current + (separator if current else "") + part
        if len(candidate) <= chunk_size:
            current = candidate
        else:
            if current:
                chunks.append(current)
            if len(part) > chunk_size:
                chunks.extend(_recursive_split(part, chunk_size, chunk_overlap, remaining_separators))
                current = ""
            else:
                current = part
    if current:
        chunks.append(current)

    return _apply_overlap(chunks, chunk_overlap)


def _apply_overlap(chunks: list[str], chunk_overlap: int) -> list[str]:
    if chunk_overlap <= 0 or len(chunks) <= 1:
        return chunks

    overlapped = [chunks[0]]
    for i in range(1, len(chunks)):
        prev_tail = chunks[i - 1][-chunk_overlap:]
        overlapped.append(prev_tail + chunks[i])
    return overlapped
