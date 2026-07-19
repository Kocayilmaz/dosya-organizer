# dosya-organizer

Bir klasördeki dosyaları uzantılarına göre otomatik olarak alt klasörlere ayıran basit bir Python CLI aracı (Resimler, Belgeler, Videolar, Müzik, Arşivler, Kod, Diğer).

## Kullanım

```bash
python organizer.py /path/to/klasor
```

Sadece ne olacağını görmek için (hiçbir dosyayı taşımadan):

```bash
python organizer.py /path/to/klasor --dry-run
```

## Test

```bash
pip install pytest
pytest tests/
```

## Nasıl çalışır

`organizer.py` içindeki `EXTENSION_MAP` sözlüğü dosya uzantılarını kategorilere eşler. Bilinmeyen uzantılar `Diğer` klasörüne gider. `plan_moves` fonksiyonu hangi dosyanın nereye taşınacağını hesaplar (test edilebilir, yan etkisiz); `organize` fonksiyonu bunu gerçekten uygular.
