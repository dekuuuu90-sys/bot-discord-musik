# ============================================
# BOT DISCORD MUSIK - VERSI PEMULA
# ============================================

# Import library yang dibutuhkan
import discord
from discord.ext import commands
import yt_dlp
import asyncio

# ============================================
# KONFIGURASI - GANTI TOKEN DISINI!
# ============================================
PREFIX = ","  # Prefix command, bebas ganti

# ============================================
# SETUP BOT
# ============================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)

# Setup downloader musik
ytdl_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'
}

ytdl = yt_dlp.YoutubeDL(ytdl_options)

# Opsi FFmpeg buat streaming
ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# Variable buat nyimpen antrian lagu
music_queue = []

# ============================================
# EVENT: Bot online
# ============================================
@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ Bot {bot.user} sudah online!")
    print("=" * 50)
    # Ganti status bot
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.listening, 
            name=",help | Musik"
        )
    )

# ============================================
# COMMAND: Join voice channel
# ============================================
@bot.command(name="join")
async def join(ctx):
    """Bot masuk ke voice channel kamu"""
    
    # Cek apakah user ada di voice channel
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        
        # Cek apakah bot udah di voice channel
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await ctx.send(f"✅ Udah join ke **{channel.name}**!")
    else:
        await ctx.send("❌ Kamu harus masuk voice channel dulu dong!")

# ============================================
# COMMAND: Leave voice channel
# ============================================
@bot.command(name="leave")
async def leave(ctx):
    """Bot keluar dari voice channel"""
    
    if ctx.voice_client:
        music_queue.clear()  # Hapus antrian
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bye bye, aku keluar dulu!")
    else:
        await ctx.send("❌ Aku lagi ga di voice channel manapun...")

# ============================================
# FUNGSI: Putar lagu berikutnya di antrian
# ============================================
async def play_next(ctx):
    """Mainkan lagu berikutnya dari antrian"""
    
    global music_queue
    
    if len(music_queue) > 0:
        # Ambil lagu pertama
        url, title = music_queue.pop(0)
        
        try:
            # Download info lagu
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
                
            audio_url = data['url']
            
            # Putar lagu, setelah selesai panggil play_next lagi
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            ctx.voice_client.play(
                source, 
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            )
            
            await ctx.send(f"🎵 Sekarang main: **{title}**")
            
        except Exception as e:
            print(f"Error: {e}")
            await ctx.send(f"❌ Gagal mainin lagu, lanjut ke berikutnya...")
            await play_next(ctx)

# ============================================
# COMMAND: Play lagu
# ============================================
@bot.command(name="play", aliases=["p"])
async def play(ctx, *, search):
    """Mainkan lagu dari YouTube"""
    
    # Cek user di voice channel
    if not ctx.author.voice:
        return await ctx.send("❌ Masuk voice channel dulu ya!")
    
    # Join jika belum di voice channel
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    # Cari lagu
    await ctx.send(f"🔍 Nyari: **{search}**...")
    
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, 
            lambda: ytdl.extract_info(f"ytsearch:{search}", download=False)
        )
        
        # Ambil hasil pertama
        if 'entries' in data:
            data = data['entries'][0]
        
        url = data['webpage_url']
        title = data['title']
        duration = data.get('duration', 0)
        
        # Cek apakah lagi ada yang main
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            # Tambah ke antrian
            music_queue.append((url, title))
            menit = duration // 60
            detik = duration % 60
            await ctx.send(f"📝 **{title}** [{menit}:{detik:02d}] ditambah ke antrian (#{len(music_queue)})")
        else:
            # Mainkan langsung
            menit = duration // 60
            detik = duration % 60
            music_queue.append((url, title))
            await play_next(ctx)
            
    except Exception as e:
        await ctx.send(f"❌ Error: Ga ketemu lagunya nih... Coba kata kunci lain!")

# ============================================
# COMMAND: Skip lagu
# ============================================
@bot.command(name="skip")
async def skip(ctx):
    """Skip lagu yang lagi main"""
    
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ Diskip!")
    else:
        await ctx.send("❌ Ga ada lagu yang lagi main...")

# ============================================
# COMMAND: Pause lagu
# ============================================
@bot.command(name="pause")
async def pause(ctx):
    """Pause lagu"""
    
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ Dipause!")
    else:
        await ctx.send("❌ Ga ada yang lagi dimainin...")

# ============================================
# COMMAND: Resume lagu
# ============================================
@bot.command(name="resume")
async def resume(ctx):
    """Lanjutin lagu yang di-pause"""
    
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ Lanjut!")
    else:
        await ctx.send("❌ Ga ada yang di-pause...")

# ============================================
# COMMAND: Lihat antrian
# ============================================
@bot.command(name="queue", aliases=["q"])
async def queue(ctx):
    """Lihat daftar antrian lagu"""
    
    if not music_queue:
        return await ctx.send("📭 Antrian kosong nih...")
    
    queue_list = "📋 **Daftar Antrian:**\n"
    for i, (url, title) in enumerate(music_queue, 1):
        if i == 1:
            queue_list += f"▶️ **{title}** (lagi main)\n"
        else:
            queue_list += f"  {i}. {title}\n"
    
    await ctx.send(queue_list)

# ============================================
# COMMAND: Hapus antrian
# ============================================
@bot.command(name="clear")
async def clear(ctx):
    """Hapus semua antrian lagu"""
    
    if ctx.voice_client:
        ctx.voice_client.stop()
    music_queue.clear()
    await ctx.send("🗑️ Antrian dibersihkan!")

# ============================================
# COMMAND: Help
# ============================================
@bot.command(name="help2", aliases=["h"])
async def help_cmd(ctx):
    """Tampilkan bantuan"""
    ...
    
    help_text = """
🎵 **MUSIC BOT COMMANDS** 🎵

`!join` - Bot masuk voice channel
`!leave` - Bot keluar voice channel  
`!play <judul>` - Mainkan lagu (contoh: !play perfect)
`!p <judul>` - Alias play
`!skip` - Skip lagu saat ini
`!pause` - Pause lagu
`!resume` - Lanjutkan lagu
`!queue` / `!q` - Lihat antrian
`!clear` - Hapus antrian
`!help` - Tampilan ini

📌 **Cara pakai:**
1. Join voice channel dulu
2. Ketik `!join`
3. Ketik `!play judul lagu`
    """
    await ctx.send(help_text)

# ============================================
# JALANKAN BOT
# ============================================
if __name__ == "__main__":
    print("Memulai bot...")
    bot.run(TOKEN)