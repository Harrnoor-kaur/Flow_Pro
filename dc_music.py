import discord
from discord.ext import commands
import yt_dlp
import asyncio
from collections import deque
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

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
        
        if not ctx.voice_client:
            await ctx.author.voice.channel.connect()

        async with ctx.typing():
            with yt_dlp.YoutubeDL(YDL_OPTIONS) as ydl:
                info = ydl.extract_info(f"ytsearch:{search}", download=False)['entries'][0]
                url2, title = info['url'], info['title']

            if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
                self.song_queue.append((url2, title))
                await ctx.send(f"Added to queue: **{title}** 📥")
            else:
                source = await discord.FFmpegOpusAudio.from_probe(url2, **FFMPEG_OPTIONS)
                ctx.voice_client.play(source, after=lambda e: self.play_next(ctx))
                await ctx.send(f"🎶 Now playing: **{title}**")

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