import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organizer import get_category, plan_moves, organize


def test_get_category_resim():
    assert get_category(".jpg") == "Resimler"
    assert get_category(".PNG") == "Resimler"


def test_get_category_belge():
    assert get_category(".pdf") == "Belgeler"


def test_get_category_bilinmeyen():
    assert get_category(".xyz") == "Diger"


def test_plan_moves(tmp_path):
    (tmp_path / "foto.jpg").write_text("x")
    (tmp_path / "rapor.pdf").write_text("x")
    (tmp_path / "not.xyz").write_text("x")

    moves = plan_moves(tmp_path)
    targets = {src.name: dst.parent.name for src, dst in moves}

    assert targets["foto.jpg"] == "Resimler"
    assert targets["rapor.pdf"] == "Belgeler"
    assert targets["not.xyz"] == "Diger"


def test_organize_moves_files(tmp_path):
    (tmp_path / "foto.jpg").write_text("x")
    organize(tmp_path, dry_run=False)

    assert (tmp_path / "Resimler" / "foto.jpg").exists()
    assert not (tmp_path / "foto.jpg").exists()


def test_organize_dry_run_does_not_move(tmp_path):
    (tmp_path / "foto.jpg").write_text("x")
    organize(tmp_path, dry_run=True)

    assert (tmp_path / "foto.jpg").exists()
    assert not (tmp_path / "Resimler").exists()
