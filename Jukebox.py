import asyncio
import discord
import os
import youtube_dl

from discord.ext import commands

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0' # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

bot = commands.Bot(command_prefix='-')
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)

        self.data = data

        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

class Jukebox(commands.Cog):
    async def on_ready(self):
        print('Logged in as')
        print(self.user.name)
        print(self.user.id)
        print('------')

    async def on_message(self, message):
        # we do not want the bot to reply to itself
        if message.author.id == self.user.id:
            return

        if message.content.startswith('-hello'):
            return await message.reply('Hello!', mention_author=True)

    @bot.command()
    async def join(ctx):
        print(ctx.author, ctx.me, ctx.voice_client)

        if ctx.author.voice == None:
            return await ctx.reply("You ain't in no voice chat bro", mention_author=True)
        return await ctx.author.voice.channel.connect()

    @bot.command()
    async def fuckoff(ctx):
        if ctx.voice_client == None:
            return await ctx.reply("Chill bro I ain't in no voice chat", mention_author=True)
        
        return await ctx.voice_client.disconnect()

    @bot.command()
    async def play(ctx, *, url):
        """Streams from a url (same as yt, but doesn't predownload)"""
        print("here")
        print(url)
        async with ctx.typing():
            player = await YTDLSource.from_url(url, loop=False, stream=True)
            ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

        await ctx.send('Now playing: {}'.format(player.title))

# bot.add_cog(Jukebox(bot))
bot.run(os.environ.get('JUKEBOX_TOKEN'))
