#!/usr/bin/env python3
"""
dosya-organizer: Bir klasördeki dosyaları uzantılarına göre alt klasörlere ayırır.

Kullanım:
    python organizer.py /path/to/klasor
    python organizer.py /path/to/klasor --dry-run
"""
import argparse
import json
import shutil
import sys
import time
from collections import Counter
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

LOG_FILENAME = ".organizer_log.json"


def get_category(extension: str, extension_map: dict = EXTENSION_MAP) -> str:
    ext = extension.lower()
    for category, extensions in extension_map.items():
        if ext in extensions:
            return category
    return "Diger"


def load_extension_map(config_path: str | None) -> dict:
    """--config ile verilen JSON dosyasından {kategori: [uzantılar]} eşlemesini yükler.
    Verilmezse varsayılan EXTENSION_MAP kullanılır."""
    if not config_path:
        return EXTENSION_MAP
    with open(config_path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    return {category: set(extensions) for category, extensions in raw.items()}


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


def plan_moves(folder: Path, recursive: bool = False, by_date: bool = False,
               extension_map: dict = EXTENSION_MAP) -> list[tuple[Path, Path]]:
    """Klasördeki dosyalar için (kaynak, hedef) çiftlerini döner. Hiçbir şeyi taşımaz."""
    moves = []
    for item in iter_source_files(folder, recursive):
        category = get_category(item.suffix, extension_map)
        target_dir = folder / category
        if by_date:
            mtime = datetime.fromtimestamp(item.stat().st_mtime)
            target_dir = target_dir / mtime.strftime("%Y-%m")
        target_path = target_dir / item.name
        moves.append((item, target_path))
    return moves


def organize(folder: Path, dry_run: bool = False, recursive: bool = False, by_date: bool = False,
             extension_map: dict = EXTENSION_MAP) -> list[tuple[Path, Path]]:
    moves = plan_moves(folder, recursive=recursive, by_date=by_date, extension_map=extension_map)
    performed = []
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
        performed.append((str(src), str(dst)))

    if not dry_run and performed:
        write_log(folder, performed)

    print_summary(moves, dry_run)
    return moves


def print_summary(moves: list[tuple[Path, Path]], dry_run: bool) -> None:
    if not moves:
        print("Taşınacak dosya bulunamadı.")
        return
    counts = Counter(dst.parent.name for _, dst in moves)
    prefix = "[DRY-RUN] " if dry_run else ""
    print(f"\n{prefix}Özet ({len(moves)} dosya):")
    for category, count in sorted(counts.items()):
        print(f"  {category}: {count}")


def write_log(folder: Path, performed: list[tuple[str, str]]) -> None:
    log_path = folder / LOG_FILENAME
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(performed, f, ensure_ascii=False, indent=2)


def undo(folder: Path) -> int:
    """Son organize() çalışmasında yapılan taşımaları geri alır. Kaç dosya geri alındığını döner."""
    log_path = folder / LOG_FILENAME
    if not log_path.exists():
        return 0
    with open(log_path, "r", encoding="utf-8") as f:
        performed = json.load(f)

    restored = 0
    for src, dst in reversed(performed):
        src_path, dst_path = Path(src), Path(dst)
        if dst_path.exists():
            src_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(dst_path), str(src_path))
            restored += 1

    log_path.unlink()
    return restored


def watch(folder: Path, recursive: bool = False, by_date: bool = False,
          extension_map: dict = EXTENSION_MAP) -> None:
    """Klasörü sürekli izler, yeni dosya düştükçe otomatik organize eder. Ctrl+C ile durur."""
    try:
        from watchdog.events import FileSystemEventHandler
        from watchdog.observers import Observer
    except ImportError:
        print("--watch için 'watchdog' paketi gerekli: pip install watchdog")
        sys.exit(1)

    class Handler(FileSystemEventHandler):
        def on_created(self, event):
            if not event.is_directory:
                organize(folder, dry_run=False, recursive=recursive, by_date=by_date, extension_map=extension_map)

    print(f"'{folder}' izleniyor... Durdurmak için Ctrl+C.")
    observer = Observer()
    observer.schedule(Handler(), str(folder), recursive=recursive)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def main():
    parser = argparse.ArgumentParser(description="Dosyaları uzantılarına göre klasörlere ayırır.")
    parser.add_argument("folder", type=str, help="Düzenlenecek klasörün yolu")
    parser.add_argument("--dry-run", action="store_true", help="Sadece ne yapılacağını göster, taşıma")
    parser.add_argument("-r", "--recursive", action="store_true", help="Alt klasörleri de tara")
    parser.add_argument("--by-date", action="store_true", help="Kategori içinde ayrıca YYYY-AA klasörlerine ayır")
    parser.add_argument("--config", type=str, default=None, help="Özel kategori/uzantı eşlemesi içeren JSON dosyası")
    parser.add_argument("--undo", action="store_true", help="Son organize işlemini geri al")
    parser.add_argument("--watch", action="store_true", help="Klasörü sürekli izleyip yeni dosyaları otomatik organize et")
    args = parser.parse_args()

    folder = Path(args.folder).expanduser().resolve()
    if not folder.is_dir():
        print(f"Hata: '{folder}' bir klasör değil veya bulunamadı.")
        return

    if args.undo:
        restored = undo(folder)
        print(f"{restored} dosya geri alındı." if restored else "Geri alınacak bir işlem kaydı bulunamadı.")
        return

    extension_map = load_extension_map(args.config)

    if args.watch:
        watch(folder, recursive=args.recursive, by_date=args.by_date, extension_map=extension_map)
        return

    organize(folder, dry_run=args.dry_run, recursive=args.recursive, by_date=args.by_date, extension_map=extension_map)


if __name__ == "__main__":
    main()
