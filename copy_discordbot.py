import asyncio
import discord
from discord.ext import commands
import os
import traceback
import re
import json
from google.cloud import texttospeech
import urllib.parse

prefix = os.getenv('DISCORD_BOT_PREFIX', default='🦑')
tts_lang = os.getenv('DISCORD_BOT_LANG', default='ja-JP')
tts_voice = os.getenv('DISCORD_BOT_VOICE', default='ja-JP-Wavenet-B')
token = os.environ['DISCORD_BOT_TOKEN']
client = commands.Bot(command_prefix=prefix)
channel_id = []
voice_flag = True

google_type = os.environ['GOOGLE_TYPE']
google_project_id = os.environ['GOOGLE_PROJECT_ID']
google_private_key_id = os.environ['GOOGLE_PRIVATE_KEY_ID']
google_private_key = os.environ['GOOGLE_PRIVATE_KEY'].replace('\\n', '\n')
google_client_email = os.environ['GOOGLE_CLIENT_EMAIL']
google_client_id = os.environ['GOOGLE_CLIENT_ID']
google_auth_uri = os.environ['GOOGLE_AUTH_URI']
google_token_uri = os.environ['GOOGLE_TOKEN_URI']
google_auth_provider_x509_cert_url = os.environ['GOOGLE_AUTH_PROVIDER_X509_CERT_URL']
google_client_x509_cert_url = os.environ['GOOGLE_CLIENT_X509_CERT_URL']

credentials = {}
credentials['type'] = google_type
credentials['project_id'] = google_project_id
credentials['private_key_id'] = google_private_key_id
credentials['private_key'] = google_private_key
credentials['client_email'] = google_client_email
credentials['client_id'] = google_client_id
credentials['auth_uri'] = google_auth_uri
credentials['token_uri'] = google_token_uri
credentials['auth_provider_x509_cert_uri'] = google_auth_provider_x509_cert_url
credentials['client_x509_cert_url'] = google_client_x509_cert_url

with open('/tmp/credentials.json', 'w') as file:
    json.dump(credentials, file, indent=2, ensure_ascii=False)
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/tmp/credentials.json'
tts_client = texttospeech.TextToSpeechClient()

@client.event
async def on_ready():
    presence = f'{prefix}ヘルプ | 0/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.event
async def on_guild_join(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.event
async def on_guild_remove(guild):
    presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
    await client.change_presence(activity=discord.Game(name=presence))

@client.command()
async def s(ctx):
    global channel_id
    channel_id.append(ctx.channel.id)
    if ctx.message.guild:
        if ctx.author.voice is None:
            await ctx.send('ボイスチャンネルに接続してから呼び出してください。')
        else:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    await ctx.send('接続済みです。')
                else:
                    await ctx.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await ctx.author.voice.channel.connect()
            else:
                await ctx.author.voice.channel.connect()

@client.command()
async def dc(ctx):
    if ctx.message.guild:
        if ctx.voice_client is None:
            await ctx.send('ボイスチャンネルに接続していません。')
        else:
            await ctx.voice_client.disconnect()

@client.command()
async def dc(invoke):
    global voice_flag
    if voice_flag:
        voice_flag = False
    else:
        voice_flag = True

@client.event
async def on_message(message):
    if message.channel.id in channel_id:
        if message.content.startswith(prefix):
            pass
        else:
            if message.guild.voice_client:
                text = message.content
                text = text.replace('\n', '、')
                pattern = r'<@(\d+)>'
                match = re.findall(pattern, text)
                for user_id in match:
                    user = await client.fetch_user(user_id)
                    user_name = f'、{user.name}へのメンション、'
                    text = re.sub(f'<@{user_id}>', user_name, text)
                pattern = r'<@&(\d+)>'
                match = re.findall(pattern, text)
                for role_id in match:
                    role = message.guild.get_role(int(role_id))
                    role_name = f'、{role.name}へのメンション、'
                    text = re.sub(f'<@&{role_id}>', role_name, text)
                pattern = r'<:([a-zA-Z0-9_]+):\d+>'
                match = re.findall(pattern, text)
                for emoji_name in match:
                    emoji_read_name = emoji_name.replace('_', ' ')
                    text = re.sub(rf'<:{emoji_name}:\d+>', f'、{emoji_read_name}、', text)
                pattern = r'https://tenor.com/view/[\w/:%#\$&\?\(\)~\.=\+\-]+'
                text = re.sub(pattern, '画像', text)
                pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+(\.jpg|\.jpeg|\.gif|\.png|\.bmp)'
                text = re.sub(pattern, '、画像', text)
                pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'
                text = re.sub(pattern, '、URL', text)
                text = text
                if text[-1:] == 'w' or text[-1:] == 'W' or text[-1:] == 'ｗ' or text[-1:] == 'W':
                    while text[-2:-1] == 'w' or text[-2:-1] == 'W' or text[-2:-1] == 'ｗ' or text[-2:-1] == 'W':
                        text = text[:-1]
                    text = text[:-1] + '、ワラ'
                if message.attachments:
                    text += '、添付ファイル'
                while message.guild.voice_client.is_playing():
                    await asyncio.sleep(0.5)
                if voice_flag:
                    tts(text)
                    source = discord.FFmpegPCMAudio('/tmp/message.mp3')
                    message.guild.voice_client.play(source)
                else: 
                    if len(text) < 100:
                        s_quote = urllib.parse.quote(text)
                        mp3url = f'http://translate.google.com/translate_tts?ie=UTF-8&q={s_quote}&tl={lang}&client=tw-ob'
                        message.guild.voice_client.play(discord.FFmpegPCMAudio(mp3url))
            else:
                pass
    await client.process_commands(message)

@client.event
async def on_voice_state_update(member, before, after):
    if before.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client is None:
                await asyncio.sleep(0.5)
                await after.channel.connect()
                text = 'ハロー、みょすただよ'
                while member.guild.voice_client.is_playing():
                    await asyncio.sleep(0.5)
                tts(text)
                source = discord.FFmpegPCMAudio('/tmp/message.mp3')
                member.guild.voice_client.play(source)

            else:
                if member.guild.voice_client.channel is after.channel:
                    text = member.name + 'さんが入室したよ'
                    while member.guild.voice_client.is_playing():
                        await asyncio.sleep(0.5)
                    tts(text)
                    source = discord.FFmpegPCMAudio('/tmp/message.mp3')
                    member.guild.voice_client.play(source)
    elif after.channel is None:
        if member.id == client.user.id:
            presence = f'{prefix}ヘルプ | {len(client.voice_clients)}/{len(client.guilds)}サーバー'
            await client.change_presence(activity=discord.Game(name=presence))
        else:
            if member.guild.voice_client:
                if member.guild.voice_client.channel is before.channel:
                    if len(member.guild.voice_client.channel.members) == 1:
                        await asyncio.sleep(0.5)
                        await member.guild.voice_client.disconnect()
                    else:
                        text = member.name + 'さんが退室したよ'
                        while member.guild.voice_client.is_playing():
                            await asyncio.sleep(0.5)
                        tts(text)
                        source = discord.FFmpegPCMAudio('/tmp/message.mp3')
                        member.guild.voice_client.play(source)
    elif before.channel != after.channel:
        if member.guild.voice_client:
            if member.guild.voice_client.channel is before.channel:
                if len(member.guild.voice_client.channel.members) == 1 or member.voice.self_mute:
                    await asyncio.sleep(0.5)
                    await member.guild.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await after.channel.connect()

@client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    await ctx.send(error_msg)

@client.command()
async def ヘルプ(ctx):
    message = f'''◆◇◆{client.user.name}の使い方◆◇◆
{prefix}＋コマンドで命令できます。
{prefix}接続：ボイスチャンネルに接続します。
{prefix}切断：ボイスチャンネルから切断します。'''
    await ctx.send(message)

def tts(message):
    synthesis_input = texttospeech.SynthesisInput(text=message)
    voice = texttospeech.VoiceSelectionParams(
        language_code=tts_lang, name=tts_voice
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=1.2
    )
    response = tts_client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    with open('/tmp/message.mp3', 'wb') as out:
        out.write(response.audio_content)


client.run(token)
