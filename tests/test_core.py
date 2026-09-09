import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfWriter

from scan2doc_core import JobConfig, _safe_name, run_job


class FakeImage:
    def save(self, path):
        Path(path).write_bytes(b"fake-image")


class FakeResult:
    def __init__(self, page_name):
        self.page_name = page_name
        self.markdown = {
            "markdown_texts": f"# {page_name}\n\n![image](../../escape.png)",
            "markdown_images": {"../../escape.png": FakeImage()},
        }

    def save_to_word(self, save_path):
        from docx import Document

        destination = Path(save_path) / f"{self.page_name}.docx"
        destination.parent.mkdir(parents=True, exist_ok=True)
        doc = Document()
        doc.add_paragraph(self.page_name)
        doc.save(destination)

    def save_to_json(self, save_path):
        Path(save_path).write_text(json.dumps({"page": self.page_name}), encoding="utf-8")


class FakeEngine:
    calls = 0

    def __init__(self, _config):
        pass

    def process_page(self, page_pdf):
        type(self).calls += 1
        return FakeResult(Path(page_pdf).stem)


class FlakyEngine(FakeEngine):
    attempts = {}

    def process_page(self, page_pdf):
        key = Path(page_pdf).stem
        self.attempts[key] = self.attempts.get(key, 0) + 1
        if key.endswith("0002") and self.attempts[key] == 1:
            raise RuntimeError("temporary OCR failure")
        return FakeResult(key)


def make_pdf(path: Path, pages: int = 3):
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=612, height=792)
    with path.open("wb") as stream:
        writer.write(stream)


class CoreTests(unittest.TestCase):
    def setUp(self):
        FakeEngine.calls = 0
        FlakyEngine.attempts = {}

    def test_safe_name(self):
        self.assertEqual(_safe_name("../../A bad:name"), "A_bad_name")

    def test_processes_merges_and_resumes(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pdf = root / "source.pdf"
            output = root / "output"
            make_pdf(pdf)
            config = JobConfig(pdf, output)

            first = run_job(config, engine_factory=FakeEngine)
            self.assertEqual(first.completed_pages, 3)
            self.assertTrue(first.markdown_path.is_file())
            self.assertTrue(first.docx_path.is_file())
            self.assertEqual(FakeEngine.calls, 3)
            markdown = first.markdown_path.read_text(encoding="utf-8")
            self.assertIn("source-page: 3", markdown)
            self.assertIn("assets/page_0001/escape.png", markdown)
            self.assertFalse((root / "escape.png").exists())

            second = run_job(config, engine_factory=FakeEngine)
            self.assertEqual(second.skipped_pages, 3)
            self.assertEqual(FakeEngine.calls, 3)

    def test_page_retry(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pdf = root / "source.pdf"
            make_pdf(pdf, 2)
            summary = run_job(
                JobConfig(pdf, root / "output", retries=1),
                engine_factory=FlakyEngine,
            )
            self.assertEqual(summary.failed_pages, [])
            self.assertEqual(FlakyEngine.attempts["page_0002"], 2)

    def test_refuses_output_manifest_for_different_pdf(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            pdf1 = root / "a.pdf"
            pdf2 = root / "b.pdf"
            make_pdf(pdf1, 1)
            make_pdf(pdf2, 2)
            output = root / "output"
            run_job(JobConfig(pdf1, output), engine_factory=FakeEngine)
            with self.assertRaisesRegex(ValueError, "different PDF or settings"):
                run_job(JobConfig(pdf2, output), engine_factory=FakeEngine)


if __name__ == "__main__":
    unittest.main()
