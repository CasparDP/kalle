from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from pypdf import PdfReader, PdfWriter

from reviewer2 import pipeline


class PipelinePdfCacheTests(unittest.TestCase):
    def test_saved_extraction_is_reused_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work_dir = Path(temporary)
            pdf_path = work_dir / "original_source.pdf"
            pdf_path.write_bytes(b"paper")
            cache_path = pipeline._pdf_text_cache_path(pdf_path, work_dir)

            with patch.object(
                pipeline, "_docling_pdf", return_value="# Paper"
            ) as convert:
                first = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            self.assertEqual(first, "# Paper")
            convert.assert_called_once_with(str(pdf_path))
            self.assertEqual(cache_path.read_text(encoding="utf-8"), "# Paper")
            self.assertFalse(cache_path.with_suffix(".md.tmp").exists())

            with patch.object(pipeline, "_docling_pdf") as convert:
                resumed = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            self.assertEqual(resumed, "# Paper")
            convert.assert_not_called()

    def test_merged_supplements_reuse_cache_on_resume(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work_dir = Path(temporary)
            pdf_path = work_dir / "original_source.pdf"
            supplement_dir = work_dir / "supplements"
            supplement_dir.mkdir()

            for path in (pdf_path, supplement_dir / "supplement.pdf"):
                writer = PdfWriter()
                writer.add_blank_page(width=72, height=72)
                with path.open("wb") as pdf_file:
                    writer.write(pdf_file)

            merged_path, _ = pipeline.merge_pdfs_python(
                str(pdf_path), str(supplement_dir), str(work_dir)
            )
            self.assertEqual(Path(merged_path), pdf_path)
            self.assertGreaterEqual(len(PdfReader(merged_path).pages), 2)

            with patch.object(
                pipeline, "_docling_pdf", return_value="# Main\n\n# Supplement"
            ):
                first = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            with patch.object(pipeline, "_docling_pdf") as convert:
                resumed = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            self.assertEqual(resumed, first)
            convert.assert_not_called()

    def test_changed_pdf_does_not_reuse_stale_extraction(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work_dir = Path(temporary)
            pdf_path = work_dir / "original_source.pdf"
            pdf_path.write_bytes(b"first version")
            first_cache_path = pipeline._pdf_text_cache_path(pdf_path, work_dir)

            with patch.object(
                pipeline, "_docling_pdf", side_effect=["# First", "# Second"]
            ) as convert:
                first = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)
                pdf_path.write_bytes(b"second version")
                second_cache_path = pipeline._pdf_text_cache_path(pdf_path, work_dir)
                second = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            self.assertEqual(first, "# First")
            self.assertEqual(second, "# Second")
            self.assertNotEqual(first_cache_path, second_cache_path)
            self.assertEqual(convert.call_count, 2)

    def test_failed_extraction_is_not_saved(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work_dir = Path(temporary)
            pdf_path = work_dir / "original_source.pdf"
            pdf_path.touch()
            cache_path = pipeline._pdf_text_cache_path(pdf_path, work_dir)

            with patch.object(pipeline, "_docling_pdf", return_value="   \n"):
                result = pipeline._load_or_extract_pdf_text(pdf_path, work_dir)

            self.assertEqual(result, "")
            self.assertFalse(cache_path.exists())


if __name__ == "__main__":
    unittest.main()
