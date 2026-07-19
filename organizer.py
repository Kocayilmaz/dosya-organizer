#!/usr/bin/env python3
"""
dosya-organizer: Bir klasördeki dosyaları uzantılarına göre alt klasörlere ayırır.

Kullanım:
    python organizer.py /path/to/klasor
    python organizer.py /path/to/klasor --dry-run
"""
import argparse
import shutil
from datetime import datetime
from pathlib import Path

EXTENSION_MAP = {
    "Resimler": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp"},
    "Belgeler": {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".pptx", ".csv"},
    "Videolar": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Muzik": {".mp3", ".wav", ".flac", ".aac", ".ogg"},
    "Arsivler": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Kod": {".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".c", ".cpp"},
}

CATEGORY_NAMES = set(EXTENSION_MAP) | {"Diger"}


def get_category(extension: str) -> str:
    ext = extension.lower()
    for category, extensions in EXTENSION_MAP.items():
        if ext in extensions:
            return category
    return "Diger"


def unique_destination(dst: Path) -> Path:
    """dst zaten varsa üzerine yazmak yerine 'isim(1).ext' gibi çakışmayan bir yol üretir."""
    if not dst.exists():
        return dst
    stem, suffix, parent = dst.stem, dst.suffix, dst.parent
    counter = 1
    candidate = parent / f"{stem}({counter}){suffix}"
    while candidate.exists():
        counter += 1
        candidate = parent / f"{stem}({counter}){suffix}"
    return candidate


def iter_source_files(folder: Path, recursive: bool):
    """Klasördeki (isteğe bağlı olarak alt klasörlerdeki) dosyaları dolaşır.
    Daha önce oluşturduğumuz kategori klasörlerinin içini tekrar işlemez."""
    if not recursive:
        yield from (item for item in folder.iterdir() if item.is_file())
        return
    for item in folder.rglob("*"):
        if not item.is_file():
            continue
        if item.parent.name in CATEGORY_NAMES and item.parent.parent == folder:
            continue
        yield item


def plan_moves(folder: Path, recursive: bool = False, by_date: bool = False) -> list[tuple[Path, Path]]:
    """Klasördeki dosyalar için (kaynak, hedef) çiftlerini döner. Hiçbir şeyi taşımaz."""
    moves = []
    for item in iter_source_files(folder, recursive):
        category = get_category(item.suffix)
        target_dir = folder / category
        if by_date:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            target_dir = target_dir / mtime.strftime("%Y-%m")
        target_path = target_dir / item.name
        moves.append((item, target_path))
    return moves


def organize(folder: Path, dry_run: bool = False, recursive: bool = False, by_date: bool = False) -> list[tuple[Path, Path]]:
    moves = plan_moves(folder, recursive=recursive, by_date=by_date)
    for src, dst in moves:
        if src == dst:
            continue
        if dry_run:
            print(f"[DRY-RUN] {src.name} -> {dst.parent.name}/")
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst = unique_destination(dst)
        shutil.move(str(src), str(dst))
        print(f"Taşındı: {src.name} -> {dst.parent.name}/")
    return moves


def main():
    parser = argparse.ArgumentParser(description="Dosyaları uzantılarına göre klasörlere ayırır.")
    parser.add_argument("folder", type=str, help="Düzenlenecek klasörün yolu")
    parser.add_argument("--dry-run", action="store_true", help="Sadece ne yapılacağını göster, taşıma")
    parser.add_argument("-r", "--recursive", action="store_true", help="Alt klasörleri de tara")
    parser.add_argument("--by-date", action="store_true", help="Kategori içinde ayrıca YYYY-AA klasörlerine ayır")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Hata: '{folder}' bir klasör değil veya bulunamadı.")
        return

    organize(folder, dry_run=args.dry_run, recursive=args.recursive, by_date=args.by_date)


if __name__ == "__main__":
    main()
