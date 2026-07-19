import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from organizer import get_category, plan_moves, organize, unique_destination


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


def test_organize_conflict_renames_instead_of_overwrite(tmp_path):
    (tmp_path / "Resimler").mkdir()
    (tmp_path / "Resimler" / "foto.jpg").write_text("eski")
    (tmp_path / "foto.jpg").write_text("yeni")

    organize(tmp_path, dry_run=False)

    assert (tmp_path / "Resimler" / "foto.jpg").read_text() == "eski"
    assert (tmp_path / "Resimler" / "foto(1).jpg").read_text() == "yeni"


def test_organize_recursive_finds_subfolder_files(tmp_path):
    sub = tmp_path / "alt"
    sub.mkdir()
    (sub / "video.mp4").write_text("x")

    organize(tmp_path, dry_run=False, recursive=True)

    assert (tmp_path / "Videolar" / "video.mp4").exists()
    assert not (sub / "video.mp4").exists()


def test_organize_recursive_does_not_reprocess_own_output(tmp_path):
    (tmp_path / "kod.py").write_text("x")
    organize(tmp_path, dry_run=False, recursive=True)

    # ikinci çalıştırma zaten organize edilmiş dosyayı tekrar taşımaya çalışmamalı
    organize(tmp_path, dry_run=False, recursive=True)

    assert (tmp_path / "Kod" / "kod.py").exists()
    assert not (tmp_path / "Kod" / "Kod").exists()


def test_organize_by_date_creates_month_subfolder(tmp_path):
    (tmp_path / "belge.txt").write_text("x")
    organize(tmp_path, dry_run=False, by_date=True)

    belgeler_dir = tmp_path / "Belgeler"
    subfolders = list(belgeler_dir.iterdir())
    assert len(subfolders) == 1
    assert subfolders[0].is_dir()
    assert (subfolders[0] / "belge.txt").exists()
