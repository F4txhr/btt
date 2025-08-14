# BTT

## Konfigurasi Environment
Set environment variables berikut sebelum menjalankan bot:

- `BOT_TOKEN`: Token bot Telegram (WAJIB)
- `OWNER_ID`: User ID pemilik/admin (default: 5361605327)
- `DEVELOPER_CHAT_ID`: Chat ID untuk menerima error (default: sama dengan `OWNER_ID`)
- `CHANNEL_USERNAME`: Username channel untuk info maintenance (default: `@todconvert_bot`)

Contoh (bash):
```bash
export BOT_TOKEN=123456:ABCDEF...
export OWNER_ID=5361605327
export DEVELOPER_CHAT_ID=5361605327
export CHANNEL_USERNAME="@namachannel"
```

## Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Menjalankan
- Bot utama:
```bash
source .venv/bin/activate
python bot.py
```
- Mode maintenance ON/OFF:
```bash
python manager.py on
python manager.py off
```

## Catatan
- Token tidak lagi di-hardcode di kode. Pastikan variabel `BOT_TOKEN` di-set.
- Broadcast dibatasi dalam batch untuk menghindari rate limit Telegram.