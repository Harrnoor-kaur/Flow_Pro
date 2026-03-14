import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import os
from dotenv import load_dotenv

load_dotenv() 
TOKEN = os.getenv('DISCORD_TOKEN')

if not TOKEN:
    print("❌ Error: DISCORD_TOKEN nahi mila! Check Variables.")

YDL_OPTIONS = {'format': 'bestaudio/best', 'noplaylist': 'True', 'quiet': True, 'default_search': 'auto'}
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.song_queue = deque()

    def play_next(self, ctx):
        if len(self.song_queue) > 0:
            url, title = self.song_queue.popleft()
            source = discord.FFmpegOpusAudio(url, **FFMPEG_OPTIONS)
            ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
            asyncio.run_coroutine_threadsafe(ctx.send(f"Next up: **{title}** 🌸"), self.bot.loop)

    @commands.command()
    async def play(self, ctx, *, search: str):
        if not ctx.author.voice:
            return await ctx.send("Pehle voice channel join karo, buddy!")
        
        # Step 1: Safe Connection
        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect(timeout=30.0, reconnect=True)
            except Exception as e:
                return await ctx.send(f"❌ Channel connect nahi ho pa raha. Error: {e}")

        async with ctx.typing():
            try:
                # Step 2: Stop blocking the Event Loop! (The Main Fix)
                loop = asyncio.get_event_loop()
                
                # Execute yt_dlp in a separate thread
                with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                    info = await loop.run_in_executor(
                        None, lambda: ydl.extract_info(f"ytsearch:{search}", download=False)
                    )
                
                if 'entries' in info:
                    info = info['entries'][0]
                    
                url2 = info['url']
                title = info.get('title', 'Unknown Song')

                # Step 3: Play or Queue
                if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                    self.song_queue.append((url2, title))
                    await ctx.send(f"Added to queue: **{title}** 📥")
                else:
                    source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                    ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
                    await ctx.send(f"🎶 Now playing: **{title}**")

            except Exception as e:
                print(f"Extraction Error: {e}")
                await ctx.send(f"❌ Error aa gaya bhai. Details: {e}")

    @commands.command()
    async def pause(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("Paused ⏸️")

    @commands.command()
    async def resume(self, ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("Resuming ⏯️")

    @commands.command()
    async def stop(self, ctx):
        self.song_queue.clear()
        if ctx.voice_client:
            ctx.voice_client.stop()
            await ctx.send("Stopped and Queue cleared ⏹️")

    @commands.command()
    async def leave(self, ctx):
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("Flow stopping... see you soon! 🌸")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f'✅ Flow is online as {bot.user}')

async def main():
    async with bot:
        await bot.add_cog(Music(bot))
        await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())