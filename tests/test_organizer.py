import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest

from organizer import get_category, plan_moves, organize, unique_destination, load_extension_map, undo, watch


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


def test_custom_config_overrides_categories(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"OzelKategori": [".xyz"]}))

    extension_map = load_extension_map(str(config_path))
    assert get_category(".xyz", extension_map) == "OzelKategori"


def test_organize_with_custom_config(tmp_path):
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps({"OzelKategori": [".xyz"]}))
    (tmp_path / "not.xyz").write_text("x")

    extension_map = load_extension_map(str(config_path))
    organize(tmp_path, dry_run=False, extension_map=extension_map)

    assert (tmp_path / "OzelKategori" / "not.xyz").exists()


def test_undo_restores_moved_files(tmp_path):
    (tmp_path / "foto.jpg").write_text("merhaba")
    organize(tmp_path, dry_run=False)
    assert (tmp_path / "Resimler" / "foto.jpg").exists()

    restored = undo(tmp_path)

    assert restored == 1
    assert (tmp_path / "foto.jpg").read_text() == "merhaba"
    assert not (tmp_path / "Resimler" / "foto.jpg").exists()
    assert not (tmp_path / ".organizer_log.json").exists()


def test_undo_without_log_returns_zero(tmp_path):
    assert undo(tmp_path) == 0


def test_organize_prints_summary(tmp_path, capsys):
    (tmp_path / "foto.jpg").write_text("x")
    (tmp_path / "rapor.pdf").write_text("x")

    organize(tmp_path, dry_run=False)

    output = capsys.readouterr().out
    assert "Özet (2 dosya)" in output
    assert "Resimler: 1" in output
    assert "Belgeler: 1" in output


def test_organize_with_dest_moves_to_separate_root(tmp_path):
    src = tmp_path / "kaynak"
    dest = tmp_path / "hedef"
    src.mkdir()
    (src / "foto.jpg").write_text("x")

    organize(src, dry_run=False, dest=dest)

    assert (dest / "Resimler" / "foto.jpg").exists()
    assert not (src / "foto.jpg").exists()
    assert not (src / "Resimler").exists()


def test_organize_without_dest_organizes_in_place(tmp_path):
    (tmp_path / "foto.jpg").write_text("x")

    organize(tmp_path, dry_run=False, dest=None)

    assert (tmp_path / "Resimler" / "foto.jpg").exists()


def test_organize_recursive_with_dest_does_not_reprocess_own_output(tmp_path):
    src = tmp_path / "kaynak"
    dest = tmp_path / "hedef"
    src.mkdir()
    (src / "kod.py").write_text("x")

    organize(src, dry_run=False, recursive=True, dest=dest)
    organize(src, dry_run=False, recursive=True, dest=dest)

    assert (dest / "Kod" / "kod.py").exists()
    assert not (dest / "Kod" / "Kod").exists()


def test_undo_restores_files_moved_to_custom_dest(tmp_path):
    src = tmp_path / "kaynak"
    dest = tmp_path / "hedef"
    src.mkdir()
    (src / "foto.jpg").write_text("merhaba")

    organize(src, dry_run=False, dest=dest)
    assert (dest / "Resimler" / "foto.jpg").exists()

    restored = undo(src)

    assert restored == 1
    assert (src / "foto.jpg").read_text() == "merhaba"
    assert not (dest / "Resimler" / "foto.jpg").exists()


def test_plan_moves_with_dest_targets_dest_root(tmp_path):
    src = tmp_path / "kaynak"
    dest = tmp_path / "hedef"
    src.mkdir()
    (src / "rapor.pdf").write_text("x")

    moves = plan_moves(src, dest=dest)

    assert moves[0][1] == dest / "Belgeler" / "rapor.pdf"


def test_watch_without_watchdog_exits_with_hint(tmp_path, capsys):
    try:
        import watchdog  # noqa: F401
        pytest.skip("watchdog kurulu, eksik-bağımlılık senaryosu test edilemiyor")
    except ImportError:
        pass

    with pytest.raises(SystemExit):
        watch(tmp_path)

    assert "pip install watchdog" in capsys.readouterr().out
