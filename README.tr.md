# Claude Token Widget

Claude Code'un kalan context window token sayısını gerçek zamanlı olarak masaüstünde gösteren hafif bir Windows widget'ı — API call yok, internet bağlantısı gerekmez.

> 🇬🇧 English installation → [README.md](README.md)

![Platform](https://img.shields.io/badge/platform-Windows-blue)
![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Nasıl Çalışır?

```
Claude Code bir yanıt bitirir
        │
        ▼
  token_hook.py otomatik çalışır
  (Claude Code'un Stop hook'u tarafından tetiklenir)
        │  JSON'a yazar
        ▼
  ~/.claude/token_stats.json
        │  her 2.5 saniyede okunur
        ▼
  claude_token_widget.py
  (masaüstünde her zaman altta duran widget)
```

İki betik birbirleriyle doğrudan konuşmaz — ortak bir JSON dosyası paylaşırlar. API call yok, token harcanmaz.

---

## Özellikler

- **Her zaman masaüstü katmanında** — tüm pencerelerin arkasında, duvar kağıdının önünde durur
- **Otomatik solar** — üstüne pencere gelince solar, açılınca geri döner
- **Dairesel arc gauge** — kullanım yüzdesini gösterir
- **Yuvarlak köşeler** (Windows 11 native DWM / Windows 10 region fallback)
- **Sürüklenebilir** — konum oturumlar arasında kaydedilir
- **Windows ile başlar** — ilk çalıştırmada startup registry'e kaydeder
- **Görev çubuğunda görünmez**, odak çalmaz

---

## Gereksinimler

- Windows 10 veya 11
- Python 3.8+
- [Claude Code](https://claude.ai/code) CLI kurulu ve yapılandırılmış

Üçüncü taraf Python paketi gerekmez — sadece standart kütüphane.

---

## Kurulum

### 1. Klonla veya indir

```bash
git clone https://github.com/YOUR_USERNAME/claude-token-widget.git
```

Ya da ZIP olarak indirip istediğin bir yere çıkart.

### 2. Claude Code hook'unu ayarla

`~/.claude/settings.json` dosyasını aç (yoksa oluştur) ve aşağıdaki bloğu ekle — path'i dosyaların bulunduğu yere göre düzenle:

```json
{
  "hooks": {
    "Stop": [
      {
        "matcher": "",
        "hooks": [
          {
            "type": "command",
            "command": "python \"C:/dosyalarin/oldugu/yol/token_hook.py\""
          }
        ]
      }
    ]
  }
}
```

Zaten başka hook'ların varsa `Stop` bloğunu onların yanına ekle.

### 3. Claude Code'u yeniden başlat

Hook'un devreye girmesi için Claude Code'u kapatıp yeniden aç.

### 4. Widget'ı çalıştır

```bash
pythonw "C:/dosyalarin/oldugu/yol/claude_token_widget.py"
```

Konsol penceresi açılmaması için `python` yerine `pythonw` kullan.

Test veya sorun giderme için:

```bash
python "C:/dosyalarin/oldugu/yol/claude_token_widget.py"
```

Widget ilk çalıştırmada kendini Windows başlangıcına otomatik kaydeder.

---

## Dosyalar

| Dosya | Görev |
|-------|-------|
| `claude_token_widget.py` | Masaüstü widget'ı — bir kez elle çalıştır |
| `token_hook.py` | Claude Code hook'u — otomatik çalışır, dokunma |

---

## Kaldırma

1. Widget'ı kapat (✕ butonuna tıkla)
2. `~/.claude/settings.json` dosyasından hook girişini sil
3. Startup girişini sil: **Kayıt Defteri Düzenleyicisi** → `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` → `ClaudeTokenWidget` girdisini sil
4. Proje klasörünü sil

---

## Lisans

MIT — bkz. [LICENSE](LICENSE)
