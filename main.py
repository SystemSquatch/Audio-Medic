from youtubesearchpython.__future__ import VideosSearch

import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv
import YTDL

load_dotenv()
intents = discord.Intents.default()
intents.members = True
intents.message_content = True
description = "Music Bot for querying audio from YouTube"
bot_name = ""
queue = []
paused = False

bot = commands.Bot(command_prefix='$', description=description, help_command=None, intents=intents)


@bot.event
async def on_ready():
    global bot_name
    bot_name = bot.user.name
    print(f'Logged in as {bot.user}')


@bot.command(description='Lists commands (this command)')
async def help(ctx):
    embed = discord.Embed(
        title=bot_name + ' Commands',
        description='Here are the bots commands',
        color=discord.Color.green()
    )

    embed.set_thumbnail(url='https://staticg.sportskeeda.com/editor/2022/06/de8b0-16565003845927.png')

    for command in bot.commands:
        embed.add_field(
            name=bot.command_prefix + command.name,
            value=command.description,
            inline=False
        )

    await ctx.send(embed=embed)


@bot.command(description='To make the bot leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is not None and voice_client.is_connected():
        await voice_client.disconnect()
    else:
        await ctx.send(bot_name + " is not connected to a voice channel.")


@bot.command(description='Bot Joins channel and starts playing whatever is asked')
async def play(ctx, *, video_search):

    videos_search = VideosSearch(video_search, limit=2)
    videos_result = await videos_search.next()
    url = videos_result.get("result")[0].get("link")

    voice_client = ctx.message.guild.voice_client

    if not ctx.message.author.voice:
        await ctx.send("{} is not connected to a voice channel".format(ctx.message.author.name))
        return
    elif voice_client is None:
        channel = ctx.message.author.voice.channel
        await channel.connect()

    if voice_client is not None and voice_client.is_playing():
        await ctx.send("Song Queued {}".format(url))
        if len(queue) <= 1:
            queue.append(url)
            await start_queue_check(ctx, voice_client)
        else:
            queue.append(url)
    else:
        try:
            await play_song(ctx, url)
        except:
            await ctx.send(bot_name + " is not connected to a voice channel.")


@bot.command(description='This command pauses the song')
async def pause(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send(bot_name + " is not in the channel")
    elif voice_client.is_playing():
        global paused
        paused = True
        voice_client.pause()
    else:
        await ctx.send(bot_name + " is not playing anything at the moment.")


@bot.command(description='Resumes the song')
async def resume(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send(bot_name + " is not connected to a voice channel.")
    elif voice_client.is_paused():
        global paused
        paused = False
        voice_client.resume()
    elif voice_client.is_playing():
        await ctx.send(bot_name + " is already playing")
    else:
        await ctx.send(bot_name + " was not playing anything before this. Use play_song command")


@bot.command(description='Skips to the next song')
async def skip(ctx):
    voice_client = ctx.message.guild.voice_client
    global paused

    if len(queue) == 0:
        await ctx.send("No Songs Queued")
        return
    else:
        await ctx.send("Skipping song...")

    if voice_client is None:
        await ctx.send(bot_name + " is not connected to a voice channel.")
    elif voice_client.is_playing() or paused:
        if paused:
            paused = False
        else:
            voice_client.stop()
    else:
        await ctx.send(bot_name + " is not playing anything at the moment.")


@bot.command(description='Stops playing, dequeues all songs')
async def stop(ctx):
    voice_client = ctx.message.guild.voice_client
    if voice_client is None:
        await ctx.send(bot_name + " is not connected to a voice channel.")
    elif voice_client.is_playing():
        voice_client.stop()
    else:
        await ctx.send(bot_name + " is not playing anything at the moment.")
    queue.clear()
    await leave(ctx)


async def play_song(ctx, url):
    async with ctx.typing():
        player = await YTDL.YTDLSource.from_url(url, stream=True)
        ctx.voice_client.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
    await ctx.send('Now playing: {}'.format(player.title))
    await ctx.send(url)


async def start_queue_check(ctx, voice_client):
    while voice_client.is_connected:
        if not voice_client.is_playing() and not paused:
            await play_song(ctx, queue.pop(0))
            if len(queue) == 0:
                break
        else:
            print(bot_name + " finished playing")
            print(queue)
            await asyncio.sleep(5)


bot.run('bot token')
