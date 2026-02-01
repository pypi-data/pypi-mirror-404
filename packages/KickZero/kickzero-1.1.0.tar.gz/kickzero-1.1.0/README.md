# ⚔️ KickZero Framework

Kick.com platformu için geliştirilmiş, yüksek performanslı, asenkron ve **Context** tabanlı modern bir bot framework'ü.

## ✨ Öne Çıkan Özellikler

* 🚀 **Tamamen Asenkron:** `aiohttp` ve `websockets` tabanlı motoruyla takılmadan çalışır.
* 🧠 **Context Yapısı:** `ctx.reply()` ve `ctx.author` gibi kolaylıklarla kod yazımını hızlandırır.
* 🔍 **Gelişmiş Debug:** Mesaj gönderim hatalarını dosyadaki satır numarasına kadar raporlar.
* 🛡️ **Spam Koruması:** Botun kendi mesajlarına cevap vererek sonsuz döngüye girmesini engeller.

## 🛠️ Kurulum

Projenizi bilgisayarınıza çekin:
```bash
git clone [https://github.com/KULLANICI_ADIN/KickZero.git](https://github.com/KULLANICI_ADIN/KickZero.git)
cd KickZero
pip install -r requirements.txt

📖 Örnek Kullanım
import asyncio
from KickZero import KickBot

# Botu başlat
bot = KickBot(
    user_name="BotAdınız",
    app_key="KICK_APP_KEY",
    chat_id="CHAT_ID",
    bearer_token="BEARER_TOKEN"
)

@bot.command(name="ping")
async def ping_komutu(ctx, args):
    await ctx.reply("Pong! Zoro asenkron nöbette! ⚔️")

@bot.on_message()
async def mesaj_takibi(ctx):
    # Gelen her mesajı konsola yazdırır
    print(f"💬 [{ctx.author}]: {ctx.content}")

if __name__ == "__main__":
    asyncio.run(bot.start())

## 🤝 Katkıda Bulunma (Contributing)
Bu proje geliştirmeye açıktır ancak büyük değişiklikler veya yeni özellikler eklemek isterseniz lütfen önce bir **Issue** açın veya benimle iletişime geçin. İzin alınmadan yapılan büyük değişikliklerin ana projeye dahil edilmesi garanti edilmez.