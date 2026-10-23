from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from kalle.mathpix import extract_equations_mathpix


class MathpixPrivacyTests(unittest.TestCase):
    def test_submission_opts_out_of_service_improvement(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            pdf = Path(temporary) / "paper.pdf"
            pdf.write_bytes(b"%PDF-test")
            response = SimpleNamespace(json=lambda: {})
            with patch.dict(
                "os.environ",
                {"MATHPIX_APP_ID": "id", "MATHPIX_APP_KEY": "key"},
                clear=False,
            ), patch("kalle.mathpix.requests.post", return_value=response) as post:
                self.assertIsNone(extract_equations_mathpix(str(pdf), "1-2"))

        options = json.loads(post.call_args.kwargs["data"]["options_json"])
        self.assertEqual(options["metadata"], {"improve_mathpix": False})


if __name__ == "__main__":
    unittest.main()
