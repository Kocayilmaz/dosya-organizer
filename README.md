# dosya-organizer

![Tests](https://github.com/Kocayilmaz/dosya-organizer/actions/workflows/test.yml/badge.svg)

Bir klasördeki dosyaları uzantılarına göre otomatik olarak alt klasörlere ayıran basit bir Python CLI aracı (Resimler, Belgeler, Videolar, Müzik, Arşivler, Kod, Diğer).

## Kullanım

```bash
python organizer.py /path/to/klasor
```

Sadece ne olacağını görmek için (hiçbir dosyayı taşımadan):

```bash
python organizer.py /path/to/klasor --dry-run
```

### Diğer bayraklar

| Bayrak | Açıklama |
| --- | --- |
| `-r`, `--recursive` | Alt klasörleri de tarar (kendi oluşturduğu kategori klasörlerini tekrar işlemez) |
| `--by-date` | Her kategori içinde ayrıca `YYYY-AA` alt klasörlerine ayırır (dosyanın değiştirilme tarihine göre) |
| `--config dosya.json` | Varsayılan kategori/uzantı eşlemesi yerine kendi JSON dosyanı kullanır, örn: `{"Tasarim": [".psd", ".ai"]}` |
| `--dest /baska/klasor` | Kategori klasörlerini kaynak yerine belirtilen hedef klasörün altında oluşturur (verilmezse kaynak klasörün içine organize edilir) |
| `--undo` | Son `organize` çalışmasında yapılan taşımaları geri alır (`.organizer_log.json` üzerinden) |
| `--watch` | Klasörü sürekli izler, yeni düşen dosyaları otomatik organize eder (`pip install watchdog` gerekir) |

Aynı isimde dosya hedefte zaten varsa üzerine yazılmaz, `isim(1).ext` gibi yeniden adlandırılır. Her çalıştırmanın sonunda kategori bazlı bir özet basılır.

## Test

```bash
pip install pytest
pytest tests/
```

Her push'ta testler GitHub Actions ile otomatik çalışır (`.github/workflows/test.yml`).

## Nasıl çalışır

`organizer.py` içindeki `EXTENSION_MAP` sözlüğü dosya uzantılarını kategorilere eşler (ya da `--config` ile verilen JSON). Bilinmeyen uzantılar `Diğer` klasörüne gider. `plan_moves` fonksiyonu hangi dosyanın nereye taşınacağını hesaplar (test edilebilir, yan etkisiz); `organize` fonksiyonu bunu gerçekten uygular ve yaptığı taşımaları `--undo` için loglar.
