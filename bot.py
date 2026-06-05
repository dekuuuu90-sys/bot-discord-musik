# ============================================
# BOT DISCORD MUSIK - VERSI LENGKAP
# ============================================

# Import library yang dibutuhkan
import discord
from discord.ext import commands, tasks
import yt_dlp
import asyncio
import random

# ============================================
# KONFIGURASI - GANTI TOKEN DISINI!
# ============================================
PREFIX = ","  # Prefix koma

# ============================================
# SETUP BOT
# ============================================
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=PREFIX, intents=intents)
bot.remove_command('help')

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
loop_mode = False

# ============================================
# EVENT: Bot online
# ============================================
@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ Bot {bot.user} sudah online!")
    print("=" * 50)
    ganti_status.start()  # ← mulai ganti status

# ============================================
# FUNGSI: Ganti status tiap 30 detik
# ============================================
@tasks.loop(seconds=30)
async def ganti_status():
    status_list = [
        "halo",
        "mau dengar musik?",
        ",help buat bantuan",
        "kalo mau musik panggli aku",
        "aku suka kamu ❤",
    ]
    
    text = random.choice(status_list)
    
    await bot.change_presence(
        status=discord.Status.idle,
        activity=discord.Activity(
            type=discord.ActivityType.playing,
            name=text
        )
    )

# ============================================
# COMMAND: Join voice channel
# ============================================
@bot.command(name="join", aliases=["masuk", "j"])
async def join_cmd(ctx):
    """Bot masuk ke voice channel kamu"""
    
    if ctx.author.voice:
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is not None:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect()
            
        await ctx.send(f"✅ apansih manggil manggil **{channel.name}**!")
    else:
        await ctx.send("❌ Kamu dimana?")

# ============================================
# COMMAND: Leave voice channel
# ============================================
@bot.command(name="leave", aliases=["keluar", "l"])
async def leave_cmd(ctx):
    """Bot keluar dari voice channel"""
    
    if ctx.voice_client:
        music_queue.clear()
        await ctx.voice_client.disconnect()
        await ctx.send("👋 Bye bye, aku keluar dulu!")
    else:
        await ctx.send("❌ Aku lagi aku lagi sendiri nih")

# ============================================
# FUNGSI: Putar lagu berikutnya di antrian
# ============================================
async def play_next(ctx):
    """Mainkan lagu berikutnya dari antrian"""
    
    global music_queue, loop_mode
    
    if len(music_queue) > 0:
        # Kalo loop nyala, masukin lagi lagu ke antrian
        if loop_mode and hasattr(play_next, 'last_song'):
            music_queue.append(play_next.last_song)
        
        # Ambil lagu pertama
        url, title = music_queue.pop(0)
        play_next.last_song = (url, title)
        
        try:
            loop = asyncio.get_event_loop()
            data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
            
            if 'entries' in data:
                data = data['entries'][0]
                
            audio_url = data['url']
            
            source = discord.FFmpegPCMAudio(audio_url, **ffmpeg_options)
            ctx.voice_client.play(
                source, 
                after=lambda e: asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
            )
            
            await ctx.send(f"🎵 Sekarang main: **{title}**")
            
        except Exception as e:
            print(f"Error: {e}")
            await ctx.send(f"❌ lagu ini gak bisa, aku skip ya")
            await play_next(ctx)
    else:
        await ctx.send("📭 udah gak ada lagunya ini")

# ============================================
# COMMAND: Play lagu
# ============================================
@bot.command(name="play", aliases=["putar", "p"])
async def play_cmd(ctx, *, search):
    """Mainkan lagu dari YouTube"""
    
    if not ctx.author.voice:
        return await ctx.send("❌ Masuk voice dulu!")
    
    if not ctx.voice_client:
        await ctx.author.voice.channel.connect()
    
    await ctx.send(f"🔍 Nyari: **{search}**...")
    
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, 
            lambda: ytdl.extract_info(f"ytsearch:{search}", download=False)
        )
        
        if 'entries' in data:
            data = data['entries'][0]
        
        url = data['webpage_url']
        title = data['title']
        duration = data.get('duration', 0)
        
        if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
            music_queue.append((url, title))
            menit = duration // 60
            detik = duration % 60
            await ctx.send(f"📝 **{title}** [{menit}:{detik:02d}] ditambah ke antrian (#{len(music_queue)})")
        else:
            music_queue.append((url, title))
            await play_next(ctx)
            
    except Exception as e:
        await ctx.send(f"❌ Error: Ga ketemu lagunya nih... Coba cari yang bener!")

# ============================================
# COMMAND: Skip lagu
# ============================================
@bot.command(name="skip", aliases=["lewati", "s"])
async def skip_cmd(ctx):
    """Skip lagu yang lagi main"""
    
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.stop()
        await ctx.send("⏭️ apalah malah diskip lagi asik loh")
    else:
        await ctx.send("❌ udah gak ada lagu ngapin coba")

# ============================================
# COMMAND: Pause lagu
# ============================================
@bot.command(name="pause", aliases=["jeda"])
async def pause_cmd(ctx):
    """Pause lagu"""
    
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("⏸️ kok malah dipaused lagi asik juga")
    else:
        await ctx.send("❌ apaasih")

# ============================================
# COMMAND: Resume lagu
# ============================================
@bot.command(name="resume", aliases=["lanjut", "r"])
async def resume_cmd(ctx):
    """Lanjutin lagu yang di-pause"""
    
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("▶️ hore dilanjut")
    else:
        await ctx.send("❌ orang lagi diem malah disuru diem")

# ============================================
# COMMAND: Lihat antrian
# ============================================
@bot.command(name="queue", aliases=["antrian", "q"])
async def queue_cmd(ctx):
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
@bot.command(name="clear", aliases=["hapus"])
async def clear_cmd(ctx):
    """Hapus semua antrian lagu"""
    
    if ctx.voice_client:
        ctx.voice_client.stop()
    music_queue.clear()
    await ctx.send("🗑️ siapa sih yang hapus")

# ============================================
# COMMAND: Loop
# ============================================
@bot.command(name="loop", aliases=["ulang"])
async def loop_cmd(ctx):
    """Loop/ulang lagu yang lagi main"""
    
    global loop_mode
    
    if not ctx.voice_client:
        return await ctx.send("❌ aku belum masuk voice channel!")
    
    if not ctx.voice_client.is_playing():
        return await ctx.send("❌ apalah")
    
    loop_mode = not loop_mode
    
    if loop_mode:
        title = play_next.last_song[1] if hasattr(play_next, 'last_song') else "Lagu"
        await ctx.send(f"🔁 **LOOP ON** - **{title}** diulang terus!")
    else:
        await ctx.send("➡️ **LOOP OFF** - Lagu ga diulang lagi")

# ============================================
# COMMAND: Help
# ============================================
@bot.command(name="help", aliases=["bantuan", "h"])
async def help_cmd(ctx):
    """Tampilkan bantuan"""
    
    help_text = """
🎵 **MUSIC BOT COMMANDS** 🎵

`,join` / `,masuk` - Bot masuk voice channel
`,leave` / `,keluar` - Bot keluar voice channel  
`,play <judul>` / `,putar` - Mainkan lagu
`,p <judul>` - Singkatan play
`,skip` / `,lewati` - Skip lagu
`,pause` / `,jeda` - Pause lagu
`,resume` / `,lanjut` - Lanjutkan lagu
`,queue` / `,antrian` / `,q` - Lihat antrian
`,clear` / `,hapus` - Hapus antrian
`,loop` / `,ulang` - Ulang lagu (ON/OFF)
`,help` / `,bantuan` - Tampilan ini

📌 **udah pada tau kali cara pakenya:**
1. Join voice channel dulu
2. Ketik `,join`
3. Ketik `,play judul lagu`
4. Ketik `,loop` buat ngulang lagu
    """
    await ctx.send(help_text)

# ============================================
# JALANKAN BOT
# ============================================
if __name__ == "__main__":
    print("Memulai bot...")
    bot.run(TOKEN)
