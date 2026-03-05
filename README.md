# Terminal2HTML

Terminal output-unu copy-paste edib, gözəl görünüşlü HTML faylına çevirən alət.

## Xüsusiyyətlər

- İstənilən terminal formatını dəstəkləyir (Kali, Ubuntu, Bash, Zsh, PowerShell, CMD)
- Hostname/OS-dən asılı olmadan işləyir
- Prompt, komanda, flag, path, error, URL — fərqli rənglərlə göstərilir
- Real terminal pəncərəsi görünüşü
- Tək EXE fayl — quraşdırma lazım deyil

## İstifadə

1. `Terminal2HTML.exe` faylını açın
2. Terminal outputunu copy-paste edin
3. Yeni sətirdə `END` yazıb Enter basın
4. HTML fayl avtomatik yaranıb brauzerdə açılacaq

## Nümunə

Girdi:
```
┌──(kali㉿kali)-[~]
└─$ gzip -h
Usage: gzip [OPTION]... [FILE]...
```

Çıxış: Gözəl rəngli terminal görünüşü olan HTML fayl.

## Build

```bash
pip install pyinstaller
pyinstaller --onefile --console --name "Terminal2HTML" terminal2html.py
```

EXE fayl `dist/` qovluğunda yaranacaq.
