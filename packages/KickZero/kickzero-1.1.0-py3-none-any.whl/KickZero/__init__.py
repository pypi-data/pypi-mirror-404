import asyncio
import aiohttp
import websockets
import json
import inspect
import colorama
from typing import Optional,Dict, Callable, Any
from colorama import Fore,Style

class Context:
    def __init__(self,user,content,bot_class):
        self.author = user
        self.content = content
        self.bot = bot_class
    async def send_message(self,message):
        return await self.bot.send_message(message)
    async def reply(self,message):
        return await self.bot.send_message(f"@{self.author} {message}")
class KickBot():
    """
    Args:
        user_name (str) : Botun kullanıcı adı
        app_key (str) : Kick'in Pusher servisi için kullandığı genel anahtar (Public Key).
        cluster (str): Pusher servisinin çalıştığı bölge (Genelde 'us2').
        chat_id (int): Mesajların okunacağı kanalın idsi.
        bearer_token (str): Kick hesabınıza mesaj gönderme yetkisi veren özel erişim anahtarı
        prefix (str): Botun komutlarını tetiklemek için kullanılan ön ek (Örn: '!', '.', '/'). 
            Varsayılan değer: '!'
        live_chat (Boolean) : Terminalde yazılan mesajları göstetir 
            Varsayılan değeri: True
    """
    user_name: str = None
    app_key: str = None
    cluster: Optional[str] = "us2"
    chat_id: int = None
    bearer_token: str = None
    prefix: Optional[str]  = "!"
    live_chat: Optional[bool] = True
    commands: Dict[str, Callable] = {}
    on_message_func: Optional[Callable] = None
    on_ready_func: Optional[Callable] = None

    def __init__(self,user_name:str,app_key:str,cluster:str,chat_id:int,bearer_token:str,prefix:str,live_chat:bool):
        KickBot.user_name = user_name.lower()
        KickBot.app_key = app_key
        KickBot.cluster = cluster
        KickBot.chat_id = chat_id
        KickBot.bearer_token = bearer_token if bearer_token.startswith("Bearer ") else f"Bearer {bearer_token}"
        KickBot.prefix = prefix
        KickBot.live_chat = live_chat
    @classmethod
    def message(cls,content:str,exact: bool = True,lower: bool = True):
        """
        Args:
            content (str) : Gelen mesajın içeriği
            exact (boolean) : Gelen mesajın kesinliği | Eğer true ise mesaj birebir eşitmi diye bakar, Eğer false ise mesaj o stringi içeriyormu diye bakar.
            lower (boolean) : Mesajın harflerinin büyklüğüne bakmadan fonksiyonu tetikler | Eğer true ise : (sa Sa sA ve SA) aynı fonkisyonu çağırır ama false ilse hepsi ayrı fonksiyonlar tarafından çağrılabilir.
        """
        def decorator(fx: Callable[..., Any]) -> Callable[..., Any]:
            if not hasattr(cls,'message_responses'):
                cls.message_responses = {}
            cls.message_responses[content] = {
                "func":fx,
                "exact":exact,
                "lower":lower
            }
            return fx
        return decorator
    @classmethod
    def command(cls, name=None):
        """
        Args:
            name (str) : Komutun adı
        """
        def decorator(func):
            cmd_name = name if name else func.__name__
            cls.commands[cmd_name] = func
            return func
        return decorator
    @classmethod
    def on_message(cls):
        def decorator(func):
            cls.on_message_func = func
            return func
        return decorator
    @classmethod
    def on_ready(cls):
        def decorator(func):
            cls.on_ready_func = func
            return func
        return decorator
    #### Luffffy Sempaiii
    @classmethod
    def timer_task(cls, hours: int = 0, minutes: int = 0, seconds: int = 0):
        """
        Belirli zaman aralıklarıyla bir fonksiyonu (görevi) çalıştırır.
        """
        def decorator(fx: Callable[..., Any]) -> Callable[..., Any]:
            if not hasattr(cls, 'timer_tasks'):
                cls.timer_tasks = []
            
            total_time = (hours * 3600) + (minutes * 60) + seconds
            
            if total_time <= 0:
                print(f"{Fore.YELLOW}⚠️ Uyarı: {fx.__name__} süresi 0 olduğu için başlatılmadı.")
                return fx

            cls.timer_tasks.append({
                "func": fx,
                "interval": total_time
            })
            return fx
        return decorator
    @staticmethod
    async def send_message(ctx:str):
        url = f"https://kick.com/api/v2/messages/send/{KickBot.chat_id}"
        headers = {
                "Authorization": KickBot.bearer_token,
                "Content-Type": "application/json; charset=utf-8", # UTF-8 olduğunu belirttik
                "Accept": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
            }
        payload = {
        "content": str(ctx),
        "type": "message"
            }
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers, timeout=10) as response:
                    status_code = response.status 
                    try:
                        response_json = await response.json()
                        response_text = response_json.get("message", "Bilinmeyen Hata")
                    except:
                        response_text = await response.text()
                    if status_code in [200, 201]:
                        return 0
                    else:
                        caller = inspect.stack()[1]
                        print(f'{Fore.RED}❌ Mesaj gönderilemedi!')
                        print(f'Satır: {caller.lineno} | Fonksiyon: {caller.function} ') 
                        print(f'Hata kodu: {status_code} | Yanıt: {response_text} \n')
                        if "User is not authenticated" in str(response_text):
                            print('HATA: Bearer token geçersiz veya süresi dolmuş!')
                        return 1
        except Exception as e:
            print(f'API Hatası: {e}')
            return 1
    ## Task Manager
    async def _run_timer_task(self, task):
        while True:
            await asyncio.sleep(task["interval"])
            
            # Yapay bir Context oluşturuyoruz (Fonksiyonun mesaj atabilmesi için)
            fake_ctx = Context(user="Sistem", content="Zamanlayıcı", bot_class=self)

            sig = inspect.signature(task["func"])
            if len(sig.parameters) == 1:
                await task["func"](fake_ctx) # Fonksiyon ctx.send_message kullanabilir
            else:
                await task["func"]()
    @staticmethod 
    async def start():
        uri = f"wss://ws-{KickBot.cluster}.pusher.com/app/{KickBot.app_key}?protocol=7&client=js&version=7.6.0&flash=false"
        colorama.init(autoreset=True)
        print(f"{Fore.CYAN}{Style.BRIGHT}⚔️ KickZero Framework Başlatılıyor...")
        print(f"{Fore.YELLOW}Prefix: {KickBot.prefix} | Canlı Sohbet: {KickBot.live_chat}")
        while True:
            try:
                async with websockets.connect(uri,ping_interval=20,ping_timeout=20) as ws:
                    # Sup To CH
                    await ws.send(json.dumps({
                        "event": "pusher:subscribe",
                        "data": {"channel": f"chatrooms.{KickBot.chat_id}.v2"}
                        }))
                    if KickBot.on_ready_func:
                        asyncio.create_task(KickBot.on_ready_func())
                    else:
                        print(f"{Fore.GREEN}Bot {Fore.BLACK}{KickBot.user_name}{Fore.GREEN} adıyla giriş yaptı ve prefixi {KickBot.prefix}")
                    if hasattr(KickBot, 'timer_tasks'):
                            bot_instance = KickBot(KickBot.user_name, KickBot.app_key, KickBot.cluster,KickBot.chat_id, KickBot.bearer_token, KickBot.prefix, KickBot.live_chat)
                            for task in KickBot.timer_tasks:
                                asyncio.create_task(bot_instance._run_timer_task(task))
                    while True:
                        raw_data = await ws.recv()
                        msg = json.loads(raw_data)
                        if msg.get("event") == "App\\Events\\ChatMessageEvent":
                            inner_data = json.loads(msg["data"])
                            user = inner_data['sender']['username']
                            content = inner_data['content']
                            if user.lower() == KickBot.user_name:
                                print(f"Bot: {content}")
                                continue
                            ctx = Context(user, content, KickBot)
                            if KickBot.live_chat:
                                print(f'{Fore.CYAN}💬 [{ctx.author}] : {ctx.content}')
                            if KickBot.on_message_func:
                                await KickBot.on_message_func(ctx)
                            if hasattr(KickBot, 'message_responses'):
                                for trigger, data in KickBot.message_responses.items():
                                    check_content = content.lower() if data.get("lower", True) else content
                                    check_trigger = trigger.lower() if data.get("lower", True) else trigger
                                    args = []
                                    is_triggered = False
                                    if data["exact"]:
                                        if check_content == check_trigger:
                                            is_triggered = True
                                    else:
                                        if check_trigger in check_content:
                                            parts = check_content.split(check_trigger, 1)
                                            args = parts[1].strip().split() if len(parts) > 1 else []
                                            is_triggered = True
                                    if is_triggered:
                                        sig = inspect.signature(data["func"])
                                        params_count = len(sig.parameters)
                                        if params_count == 2:
                                            await data["func"](ctx, args)
                                        else:
                                            await data["func"](ctx)
                                        if data["exact"]: break # Tam eşleşmede döngüyü kır
                            if content.startswith(KickBot.prefix):
                                parts = content[len(KickBot.prefix):].split()
                                if parts:
                                    cmd_name = parts[0].lower()
                                    args = parts[1:]
                                    if cmd_name in KickBot.commands:
                                        await KickBot.commands[cmd_name](ctx,args)
                            elif msg.get("event") == "pusher:ping":
                                await ws.send(json.dumps({"event":"pusher:pong"}))
            except Exception as e:
                print(f"{Fore.RED}Hata {e} 5 saniye sonra tekrar denenicek")
                await asyncio.sleep(5)