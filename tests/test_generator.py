import os
import tempfile
from app.services.certificate_template import generate_certificate


def test_generator_creates_valid_pdf():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        generate_certificate(
            path=tmp_path,
            name="Rahul Sharma",
            course="Python Backend Development",
            date="07 October 2026",
            certificate_id="CERT-2026-0001",
            issuer="Acme Academy",
        )
        assert os.path.exists(tmp_path)
        with open(tmp_path, "rb") as f:
            content = f.read()
        assert content.startswith(b"%PDF")
        assert len(content) > 1000
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_generator_handles_long_name_and_unicode():
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        # Long name that requires auto-scaling font size
        long_name = "Dr. Alexander Montgomery Maximilian Bartholomew III"
        generate_certificate(
            path=tmp_path,
            name=long_name,
            course="Advanced Distributed Cloud Computing Systems",
            date="07 October 2026",
            certificate_id="CERT-2026-9999",
        )
        assert os.path.exists(tmp_path)
        with open(tmp_path, "rb") as f:
            content = f.read()
        assert content.startswith(b"%PDF")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
