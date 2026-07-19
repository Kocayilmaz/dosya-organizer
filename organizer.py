#!/usr/bin/env python3
"""
dosya-organizer: Bir klasördeki dosyaları uzantılarına göre alt klasörlere ayırır.

Kullanım:
    python organizer.py /path/to/klasor
    python organizer.py /path/to/klasor --dry-run
"""
import argparse
import shutil
from pathlib import Path

EXTENSION_MAP = {
    "Resimler": {".jpg", ".jpeg", ".png", ".gif", ".svg", ".webp", ".bmp"},
    "Belgeler": {".pdf", ".doc", ".docx", ".txt", ".md", ".xlsx", ".pptx", ".csv"},
    "Videolar": {".mp4", ".mov", ".avi", ".mkv", ".webm"},
    "Muzik": {".mp3", ".wav", ".flac", ".aac", ".ogg"},
    "Arsivler": {".zip", ".rar", ".7z", ".tar", ".gz"},
    "Kod": {".py", ".js", ".ts", ".html", ".css", ".json", ".java", ".c", ".cpp"},
}


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


def plan_moves(folder: Path) -> list[tuple[Path, Path]]:
    """Klasördeki dosyalar için (kaynak, hedef) çiftlerini döner. Hiçbir şeyi taşımaz."""
    moves = []
    for item in folder.iterdir():
        if item.is_file():
            category = get_category(item.suffix)
            target_dir = folder / category
            target_path = target_dir / item.name
            moves.append((item, target_path))
    return moves


def organize(folder: Path, dry_run: bool = False) -> list[tuple[Path, Path]]:
    moves = plan_moves(folder)
    for src, dst in moves:
        if dry_run:
            print(f"[DRY-RUN] {src.name} -> {dst.parent.name}/")
            continue
        dst.parent.mkdir(exist_ok=True)
        dst = unique_destination(dst)
        shutil.move(str(src), str(dst))
        print(f"Taşındı: {src.name} -> {dst.parent.name}/")
    return moves


def main():
    parser = argparse.ArgumentParser(description="Dosyaları uzantılarına göre klasörlere ayırır.")
    parser.add_argument("folder", type=str, help="Düzenlenecek klasörün yolu")
    parser.add_argument("--dry-run", action="store_true", help="Sadece ne yapılacağını göster, taşıma")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Hata: '{folder}' bir klasör değil veya bulunamadı.")
        return

    organize(folder, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
