# Üretim hattı

- `kaynak-fotograflar/`: asiyansanat.com ürün sayfasından (ürün kodu PBH11937, 29x50) çerçeve varyantlarının ana fotoğrafları (1080×1080, gri stüdyo fon).
- `crops.json`: fotoğraftan kesilen çerçeve kutusu, en-boy oranı ve yan renk (gen_models.py girdisi).
- `gen_models.py`: gerçek ölçülü (50 cm en, 3 cm derinlik varsayımı) GLB (Android/WebXR, dik, arka yüz z=0) ve USDZ (iPhone Quick Look, dikey yüzey çapası; 64 bayt hizalı zip) üretir. `-yatik` USDZ yalnızca yön testi içindir.
- `odanda-gor.template.html` + `build.py`: aynı şablondan Artifact (tek dosya, gömülü veri) ve barındırılan (dosya yollu) sürümü üretir. Yollar betiklerin içinde sabit; taşırsan güncelle.
- `urun-verisi-ikas.json`: ürün sayfasındaki gömülü `__NEXT_DATA__` ürün nesnesi (varyant tipleri, görsel kimlikleri, fiyat).
