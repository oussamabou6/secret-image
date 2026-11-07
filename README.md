# 🔐 Secret Image

Hide an **encrypted message or file** inside an ordinary photo, and extract it later with a password.
Runs entirely in your browser (nothing is uploaded), with a Python CLI that uses the same format.

Developed by **[Boucetta Oussama](https://portfolio.formeevent.com)**.

> بالعربية: أداة لإخفاء رسالة أو ملف (txt / Word / Excel / PDF) مشفّرين داخل صورة JPG، واستخراجهما لاحقًا بكلمة سر. الموقع بالعربية بالكامل ويتضمن شرحًا وكتالوجًا للخوارزميات.

## Features

- Pick a **JPG** cover image, then hide a **text message** or a **file** (`txt`, `doc/docx`, `xls/xlsx`, `pdf`)
- **AES-256-GCM** encryption, key derived with **PBKDF2 + SHA-256** (210,000 iterations, random salt)
- Data hidden in the image pixels with **LSB steganography**
- Wrong password **and** tampered data are detected (GCM authentication tag)
- The web page verifies the output image *before* offering the download
- Arabic interface with step-by-step guide and an algorithms catalog
- Responsive, dark mode, no dependencies, no server
- `secret_image.py`: command-line tool, 100% compatible with the web page

## Quick start

### Web page

```bash
git clone https://github.com/oussamabou6/secret-image.git
cd secret-image
python3 -m http.server 8000
```

Open <http://localhost:8000>. (Use `localhost`: browsers disable the crypto API on non-HTTPS addresses.)

**GitHub Pages:** repository *Settings → Pages → Deploy from a branch → `main` / root*. Your site will be at `https://oussamabou6.github.io/secret-image/`.

### Command line

```bash
pip install pillow cryptography          # on Kali/Debian: sudo apt install python3-pil python3-cryptography

python3 secret_image.py hide photo.jpg out.png                    # hide a typed message
python3 secret_image.py hide photo.jpg out.png --file report.pdf  # hide a file
python3 secret_image.py reveal out.png                            # extract
```

## How it works

1. Plaintext = `type byte` (0 text, 1 file) [+ file name] + data
2. Key = `PBKDF2-HMAC-SHA256(password, salt, 210000)` → 32 bytes
3. Ciphertext = `AES-256-GCM(key, iv, plaintext, aad="STG2")`
4. The payload is written into the least-significant bit of every R, G, B value, pixel by pixel

| Offset (bytes) | Size | Content |
|---|---|---|
| 0 | 4 | Magic `STG2` |
| 4 | 16 | PBKDF2 salt |
| 20 | 12 | AES-GCM IV |
| 32 | 4 | Ciphertext length (big-endian) |
| 36 | n | Ciphertext + 16-byte tag |

Bits are written most-significant first, in R→G→B order (alpha is skipped). Any tool implementing this layout can read the images.

**Capacity** ≈ `width × height × 3 / 8` bytes (a 12-megapixel photo holds about 4.5 MB).

## Important notes

- The output is **PNG**, not JPG. JPEG compression rewrites pixel values and destroys the hidden bits. Do not re-save or convert the PNG, and send it as a *file/document* (messaging apps compress photos).
- Some browsers randomize canvas pixels (anti-fingerprinting: Firefox *resistFingerprinting*, Brave, some extensions). The page detects this and warns you; use Chrome/Chromium or the Python CLI instead.
- Security equals password strength: choose a long passphrase. There is no recovery if you forget it.
- LSB hiding can be detected by statistical steganalysis, especially when the image is filled to capacity. Encryption still protects the content.
- Educational/privacy tool. Do not use it for anything illegal.

## Author

**Boucetta Oussama**: [portfolio.formeevent.com](https://portfolio.formeevent.com)

## License

MIT, see [LICENSE](LICENSE).
