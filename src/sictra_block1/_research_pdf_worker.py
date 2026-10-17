"""Trusted local subprocess; PDF data is never executable code or a URL fetch."""
from io import BytesIO
import json
import sys


def extract(raw):
    from pypdf import PdfReader, filters
    from pypdf.generic import ArrayObject, DictionaryObject, IndirectObject, StreamObject
    filters.ZLIB_MAX_OUTPUT_LENGTH = 8 * 1024 * 1024
    filters.ZLIB_MAX_RECOVERY_INPUT_LENGTH = 1024
    if not raw.startswith(b'%PDF-') or not 0 < len(raw) <= 256 * 1024:
        raise ValueError('size/format')
    reader = PdfReader(BytesIO(raw), strict=True)
    if reader.is_encrypted or len(reader.pages) != 4:
        raise ValueError('encryption/pages')
    seen, count, decoded = set(), 0, 0
    forbidden = {'/OpenAction', '/AA', '/JS', '/JavaScript', '/Launch',
                 '/RichMedia', '/XFA', '/EmbeddedFiles', '/EF'}
    actions = {'/JavaScript', '/Launch', '/GoToR', '/SubmitForm', '/ImportData', '/Rendition'}

    def visit(value, depth=0):
        nonlocal count, decoded
        if depth > 32:
            raise ValueError('depth')
        token = (('indirect', value.idnum, value.generation) if isinstance(value, IndirectObject)
                 else ('direct', id(value)))
        if token in seen:
            return
        seen.add(token)
        count += 1
        if count > 4096:
            raise ValueError('objects')
        if isinstance(value, IndirectObject):
            visit(value.get_object(), depth + 1)
        elif isinstance(value, DictionaryObject):
            if forbidden.intersection(value) or value.get('/S') in actions:
                raise ValueError('active/embedded')
            if isinstance(value, StreamObject):
                filter_value = value.get('/Filter')
                allowed = filter_value is None or filter_value == '/FlateDecode'
                if isinstance(filter_value, ArrayObject):
                    allowed = list(filter_value) == ['/FlateDecode']
                if not allowed:
                    raise ValueError('unsupported stream filter')
                decoded += len(value.get_data())
                if decoded > 8 * 1024 * 1024:
                    raise ValueError('decoded streams')
            for child in value.values():
                visit(child, depth + 1)
        elif isinstance(value, ArrayObject):
            for child in value:
                visit(child, depth + 1)

    visit(reader.trailer)
    pages, text_bytes = [], 0
    for page in reader.pages:
        content = page.get_contents()
        if content is None or len(content.get_data()) > 512 * 1024:
            raise ValueError('page content limit')
        text = page.extract_text()
        text_bytes += len(text.encode('utf-8'))
        if text_bytes > 128 * 1024:
            raise ValueError('text limit')
        pages.append(text)
    return pages


def main():
    try:
        raw = sys.stdin.buffer.read(256 * 1024 + 1)
        pages = extract(raw)
        sys.stdout.buffer.write(json.dumps(pages, ensure_ascii=True).encode('ascii'))
        return 0
    except Exception:
        # Never leak PDF text, parser internals or private paths via stderr.
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
