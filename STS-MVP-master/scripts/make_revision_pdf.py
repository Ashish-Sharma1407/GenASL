from pathlib import Path
import textwrap


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "GenASL_Project_Revision_Guide.md"
OUTPUT = ROOT / "docs" / "GenASL_Project_Revision_Guide.pdf"

PAGE_W, PAGE_H = 595, 842  # A4 points
LEFT, RIGHT, TOP, BOTTOM = 56, 56, 58, 54
CONTENT_W = PAGE_W - LEFT - RIGHT


def clean_text(text: str) -> str:
    replacements = {
        "\u2013": "-",
        "\u2014": "-",
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text.encode("latin-1", "replace").decode("latin-1")


def pdf_escape(text: str) -> str:
    return clean_text(text).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def wrap_line(text: str, size: int) -> list[str]:
    if not text:
        return [""]
    avg_char = size * 0.52
    width = max(28, int(CONTENT_W / avg_char))
    return textwrap.wrap(text, width=width, break_long_words=False) or [text]


def parse_markdown(md: str):
    blocks = []
    in_code = False
    for raw in md.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            blocks.append(("code", line))
        elif line.startswith("# "):
            blocks.append(("title", line[2:].strip()))
        elif line.startswith("## "):
            blocks.append(("heading", line[3:].strip()))
        elif line.startswith("- "):
            blocks.append(("bullet", line[2:].strip()))
        elif line.strip():
            blocks.append(("para", line.strip()))
        else:
            blocks.append(("space", ""))
    return blocks


def paginate(blocks):
    pages = []
    current = []
    y = TOP

    styles = {
        "title": ("F2", 24, 32, 18),
        "heading": ("F2", 14, 19, 10),
        "para": ("F1", 10, 14, 5),
        "bullet": ("F1", 10, 14, 5),
        "code": ("F3", 9, 13, 4),
        "space": ("F1", 10, 8, 0),
    }

    def new_page():
        nonlocal current, y
        if current:
            pages.append(current)
        current = []
        y = TOP

    for kind, text in blocks:
        font, size, leading, after = styles[kind]
        prefix = "- " if kind == "bullet" else ""
        lines = []
        for wrapped in wrap_line(prefix + text, size):
            lines.append((font, size, leading, wrapped))

        needed = len(lines) * leading + after
        if y + needed > PAGE_H - BOTTOM:
            new_page()

        for item in lines:
            current.append(item)
            y += item[2]
        y += after

    if current:
        pages.append(current)
    return pages


def build_pdf(pages):
    objects = []

    def add(obj: str) -> int:
        objects.append(obj)
        return len(objects)

    catalog_id = add("<< /Type /Catalog /Pages 2 0 R >>")
    pages_id = add("PAGES_PLACEHOLDER")
    font1_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    font2_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>")
    font3_id = add("<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>")

    page_ids = []
    for page_no, lines in enumerate(pages, start=1):
        commands = ["BT"]
        cursor_y = PAGE_H - TOP
        for font, size, leading, text in lines:
            commands.append(f"/{font} {size} Tf")
            commands.append(f"{LEFT} {cursor_y:.2f} Td")
            commands.append(f"({pdf_escape(text)}) Tj")
            commands.append(f"{-LEFT} {-leading:.2f} Td")
            cursor_y -= leading
        commands.append("/F1 8 Tf")
        commands.append(f"{PAGE_W / 2 - 20:.2f} {BOTTOM / 2:.2f} Td")
        commands.append(f"(Page {page_no}) Tj")
        commands.append("ET")
        stream = "\n".join(commands)
        stream_bytes = stream.encode("latin-1", "replace")
        content_id = add(
            f"<< /Length {len(stream_bytes)} >>\nstream\n{stream}\nendstream"
        )
        page_id = add(
            f"<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {PAGE_W} {PAGE_H}] "
            f"/Resources << /Font << /F1 {font1_id} 0 R /F2 {font2_id} 0 R /F3 {font3_id} 0 R >> >> "
            f"/Contents {content_id} 0 R >>"
        )
        page_ids.append(page_id)

    objects[pages_id - 1] = (
        f"<< /Type /Pages /Kids [{' '.join(f'{pid} 0 R' for pid in page_ids)}] "
        f"/Count {len(page_ids)} >>"
    )

    out = bytearray()
    out.extend(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
    offsets = [0]
    for i, obj in enumerate(objects, start=1):
        offsets.append(len(out))
        out.extend(f"{i} 0 obj\n{obj}\nendobj\n".encode("latin-1", "replace"))
    xref = len(out)
    out.extend(f"xref\n0 {len(objects) + 1}\n".encode("ascii"))
    out.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        out.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    out.extend(
        f"trailer\n<< /Size {len(objects) + 1} /Root {catalog_id} 0 R >>\n"
        f"startxref\n{xref}\n%%EOF\n".encode("ascii")
    )
    return out


def main():
    blocks = parse_markdown(SOURCE.read_text(encoding="utf-8"))
    pages = paginate(blocks)
    OUTPUT.write_bytes(build_pdf(pages))
    print(f"Created {OUTPUT}")
    print(f"Pages: {len(pages)}")


if __name__ == "__main__":
    main()
