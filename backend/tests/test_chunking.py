from app.services.chunking import chunk_pages


def test_short_page_is_single_chunk():
    chunks = chunk_pages(["short text"], chunk_size=1000, chunk_overlap=150)
    assert len(chunks) == 1
    assert chunks[0].text == "short text"
    assert chunks[0].page == 1


def test_long_page_splits_into_multiple_chunks_with_page_number():
    text = ("sentence one. " * 200).strip()
    chunks = chunk_pages([text], chunk_size=200, chunk_overlap=20)
    assert len(chunks) > 1
    assert all(c.page == 1 for c in chunks)
    # chunk_size + overlap is a soft target, not a hard cap (a boundary-preserving
    # splitter can slightly overshoot when appending overlap context)
    assert all(len(c.text) <= 300 for c in chunks)


def test_page_numbers_tracked_across_multiple_pages():
    chunks = chunk_pages(["page one text", "page two text"], chunk_size=1000)
    pages = {c.page for c in chunks}
    assert pages == {1, 2}


def test_empty_pages_produce_no_chunks():
    chunks = chunk_pages(["", "   "])
    assert chunks == []
