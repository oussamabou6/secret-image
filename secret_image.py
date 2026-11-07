"""
المطوّر: Boucetta Oussama  |  https://portfolio.formeevent.com

إخفاء رسالة أو ملف مشفّر داخل صورة (متوافق مع موقع صورة سرّية، الصيغة STG2).

pip install pillow cryptography
python secret_image.py hide photo.jpg out.png                 (رسالة نصية)
python secret_image.py hide photo.jpg out.png --file report.pdf  (txt / Word / Excel / PDF)
python secret_image.py reveal out.png
"""
import argparse
import os
import struct
import sys
from getpass import getpass

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from PIL import Image

MAGIC = b"STG2"
HEADER = 36  # الشارة 4 + salt 16 + iv 12 + الطول 4


def make_key(password, salt):
    kdf = PBKDF2HMAC(hashes.SHA256(), length=32, salt=salt, iterations=210_000)
    return kdf.derive(password.encode())


def read_bytes(pixels, start, count):
    out = bytearray()
    for j in range(start, start + count):
        v = 0
        for b in range(8):
            v = (v << 1) | (pixels[j * 8 + b] & 1)
        out.append(v)
    return bytes(out)


def hide(args):
    if not args.cover.lower().endswith((".jpg", ".jpeg")):
        sys.exit("صورة الغلاف يجب أن تكون JPG")
    image = Image.open(args.cover).convert("RGB")

    if args.file:
        if not args.file.lower().endswith((".txt", ".doc", ".docx", ".xls", ".xlsx", ".pdf")):
            sys.exit("الصيغ المدعومة: txt, doc, docx, xls, xlsx, pdf")
        name = os.path.basename(args.file).encode()[:255]
        with open(args.file, "rb") as f:
            plain = b"\x01" + struct.pack(">H", len(name)) + name + f.read()
    else:
        plain = b"\x00" + (args.text or input("الرسالة: ")).encode()

    password = getpass("كلمة المرور: ")
    salt, iv = os.urandom(16), os.urandom(12)
    cipher = AESGCM(make_key(password, salt)).encrypt(iv, plain, MAGIC)
    data = MAGIC + salt + iv + struct.pack(">I", len(cipher)) + cipher

    pixels = bytearray(image.tobytes())
    if len(data) * 8 > len(pixels):
        sys.exit("المحتوى أكبر من سعة الصورة")
    for j, byte in enumerate(data):
        for b in range(8):
            k = j * 8 + b
            pixels[k] = (pixels[k] & 0xFE) | ((byte >> (7 - b)) & 1)

    # PNG لأن JPG يضغط الصورة ويمحو البيانات المخفية
    Image.frombytes("RGB", image.size, bytes(pixels)).save(args.out, "PNG")
    print("تم الحفظ في", args.out)


def reveal(args):
    pixels = Image.open(args.image).convert("RGB").tobytes()
    if len(pixels) < HEADER * 8:
        sys.exit("لا توجد بيانات مخفية")
    header = read_bytes(pixels, 0, HEADER)
    if header[:4] != MAGIC:
        sys.exit("لا توجد بيانات مخفية في هذه الصورة")
    size = struct.unpack(">I", header[32:36])[0]
    if size < 17 or (HEADER + size) * 8 > len(pixels):
        sys.exit("البيانات تالفة")

    cipher = read_bytes(pixels, HEADER, size)
    try:
        plain = AESGCM(make_key(getpass("كلمة المرور: "), header[4:20])).decrypt(
            header[20:32], cipher, MAGIC
        )
    except InvalidTag:
        sys.exit("كلمة المرور خاطئة أو أن البيانات تعرّضت للتعديل")

    if plain[0] == 0:
        print("الرسالة:", plain[1:].decode())
    elif plain[0] == 1:
        n = struct.unpack(">H", plain[1:3])[0]
        name = os.path.basename(plain[3:3 + n].decode()) or "file"
        with open(name, "wb") as f:
            f.write(plain[3 + n:])
        print("تم حفظ الملف:", name)
    else:
        sys.exit("صيغة غير معروفة")


p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
sub = p.add_subparsers(dest="cmd", required=True)
h = sub.add_parser("hide")
h.add_argument("cover")
h.add_argument("out")
h.add_argument("--file")
h.add_argument("--text")
h.set_defaults(run=hide)
r = sub.add_parser("reveal")
r.add_argument("image")
r.set_defaults(run=reveal)

if __name__ == "__main__":
    a = p.parse_args()
    a.run(a)
