# Web Forum Diskusi (Aplikasi Web Sengaja Rentan)

Aplikasi forum sederhana yang dibangun dengan Python & Flask, dibuat dengan kerentanan yang disengaja untuk tujuan pembelajaran keamanan web.

---

> ## ⚠️ PERINGATAN KEAMANAN
> **APLIKASI INI TIDAK AMAN.** Jangan gunakan di lingkungan produksi atau dengan data nyata.
>
> Mengandung kerentanan seperti **SQL Injection, Stored XSS, Plain Text Password, dan IDOR**.

---

### Teknologi

- Python
- Flask & SQLAlchemy
- Bootstrap 5
- SQLite

---

### Cara Menjalankan

**1. Clone & Install**
```bash
git clone [https://github.com/DimasFigo/ForumDiskusi.git](https://github.com/DimasFigo/ForumDiskusi.git)
cd ForumDiskusi
pip install -r requirements.txt
2. Jalankan Server
Perintah ini akan membuat file database.db secara otomatis.

Bash

python app.py
3. Buat Admin Pertama

Hentikan server (Ctrl+C), lalu jalankan flask shell.

Masukkan perintah berikut:

Python

from app import db, User; admin = User(username='admin', password='admin', role='admin'); db.session.add(admin); db.session.commit(); exit()
Jalankan kembali server (python app.py) dan login sebagai admin.

Dibuat oleh Dimas Figo
