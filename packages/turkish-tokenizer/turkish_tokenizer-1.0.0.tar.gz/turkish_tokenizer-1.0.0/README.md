# Turkish Tokenizer

**PyPI version** | **Python 3.8+** | **License: MIT**

Dilbilim kurallarını temel alarak, çok dilli metinleri işlemek ve anlam bütünlüğünü korumak için gelişmiş bir tokenizer altyapısı.

## Kurulum

PyPI üzerinden kurulum (Önerilen)

```bash
pip install turkish-tokenizer
```

## Özellikler (v1.0.0)

- **Yüksek Performans**: Rust ile yeniden yazılmış motor (Python versiyonuna göre ~100x hız).
- **Tam Uyumluluk**: Python versiyonu ile %99.8+ aynı çıktı.
- **Dilbilim Kuralları**: Ünlü uyumu, yumuşama ve diğer ses olaylarını destekler.

## Kullanım

```python
from turkish_tokenizer import TurkishTokenizer

tokenizer = TurkishTokenizer()
tokens = tokenizer.encode("Merhaba dünya")
text = tokenizer.decode(tokens)
print(text)
```
