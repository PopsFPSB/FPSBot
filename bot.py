#!/usr/bin/env python3
# bot.py

import os
from asyncio import sleep
import json
import random
from copy import copy
import logging
from time import asctime, localtime

import discord
from discord.ext import commands, tasks
from discordTogether import DiscordTogether
from discord_components import DiscordComponents, Button, ButtonStyle, Select, SelectOption, InteractionType

from dotenv import load_dotenv

from scraper import *

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = int(os.getenv('DISCORD_GUILD'))
SELECT_VOICE_CHAN = int(os.getenv('DISCORD_VOICE_CHAN_ID'))
NOTIF_CHAN = int(os.getenv('DISCORD_NOTIF_CHAN_ID'))
VIDEO_CHAN = int(os.getenv('DISCORD_VIDEO_CHAN_ID'))

bot = commands.Bot(command_prefix='/', help_command=None)
together_control = DiscordTogether(bot)
intents = discord.Intents(messages=True, guilds=True, reactions=True, voice_states=True)


logging.basicConfig(format='%(asctime)s %(message)s')

@bot.event
async def on_ready():
	DiscordComponents(bot)
	print('Bot is ready', flush=True)
	for guild in bot.guilds:
		print(f'Connected to guild {guild}')
	activity = discord.Activity(type=discord.ActivityType.custom, name='Fais tourner son stylo', url='https://forum.penspinning-france.fr/')
	await bot.change_presence(activity=activity)


@bot.command()
async def ordre(ctx):
	with open('/home/discord/fpsb_bot/resources/ordre.png', 'rb') as img:
		to_send = discord.File(img)
		await ctx.send(f"Voici l\'ordre d\'apprentissage recommandé pour les tricks!", file=to_send)
		print(f'{asctime(localtime())} : {ctx.author} used command \'/ordre\'', flush=True)


@bot.command()
async def timer(ctx, temps: int, step: int=1):
	print('f{asctime(localtime())} : {ctx.author} used command \'/timer {temps} {step}\'', flush=True)
	if step > temps:
		step = 1
	await ctx.send(f'Timer lancé pour {str(temps)} secondes')
	message = await ctx.send(f'Temps restant : {str(temps)}')
	for t in range(temps, 0, -step):
		await message.edit(content=f'Temps restant : {str(t)}')
		await sleep(step)
	await message.edit(content='Temps écoulé!')

@bot.command()
async def time(ctx, temps: int, step: int=1):
	if step > temps:
		step = 1
	await ctx.send(f'Timer lancé pour {str(temps)} secondes')
	message = await ctx.send(f'Temps restant : {str(temps)}')
	while temps > 0:
		await message.edit(content=f'Temps restant : {str(temps)}')
		rand_step = random.uniform(step/2, step*3/2)
		temps -= step
		await sleep(rand_step)
	await message.edit(content='Temps écoulé !')

@bot.command()
async def connect(ctx):
	channel = ctx.author.voice.channel
	await channel.connect()

@bot.command()
async def disconnect(ctx):
	await ctx.voice_client.disconnect()

@bot.command()
async def yt(ctx):
	link = await together_control.create_link(ctx.author.voice.channel.id, 'youtube')
	await ctx.send(f"Clique le lien pour rejoindre la party!\n{link}")


@bot.event
async def on_voice_state_update(member, before, after):
	print(f'{asctime(localtime())} : {member.display_name}\'s voice status was updated from {before} to {after}', flush=True)
	with open('/home/discord/fpsb_bot/json/temporary_channels.json') as temp_chan_list_file:
		temp_chan_list = json.load(temp_chan_list_file)
	if before.channel is not None:
		if before.channel.id in temp_chan_list:
			if len(before.channel.members) == 0:
				temp_chan_list.remove(before.channel.id)
				with open('/home/discord/fpsb_bot/json/temporary_channels.json', 'w') as temp_chan_list_file:
					json.dump(temp_chan_list, temp_chan_list_file)
				print(f'Deleted channel {before.channel}', flush=True)
				await before.channel.delete()
	guild = member.guild
	if after.channel == guild.get_channel(SELECT_VOICE_CHAN):
		print(f'User {member} went in voice creation channel', flush=True)
		voice_category = member.voice.channel.category
		chan_name = f'Salon de {member.display_name}'
		temporary_channel = await guild.create_voice_channel(chan_name, category=voice_category)
		temp_chan_list.append(temporary_channel.id)
		with open('/home/discord/fpsb_bot/json/temporary_channels.json', 'w') as temp_chan_list_file:
			json.dump(temp_chan_list, temp_chan_list_file)
		await member.move_to(temporary_channel)

@bot.command()
async def trade(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/trade\'', flush=True)
	await ctx.send("""Pour avoir des mods il y a 4 possibilités:

- Te les faire toi même avec des stylos que tu as chez toi ou en magasins : l'avantage c'est que c'est pas cher, mais en France on n'a pas énormément de stuff connu donc si tu débutes ce sera sûrement un truc bricolé.

- Suivre un tuto de mod français et le faire avec le matériel de chez toi ou trouvable en magasin (le LePen, le marine, le grip aviaire, etc.) : ça t'assure d'avoir un bon mod sans aucun risque niveau arnaque etc. mais en contre partie c'est à toi de le modder toi même.

- Acheter en ligne sur des shops : ça paraît pro si tes parents sont pas vraiment ok mais certains shops n'utilisent pas forcément les parts réelles pour certains mods, les délais de livraisons ne sont pas toujours optimaux et t'as souvent des frais de ports importants vu que c'est à l'étranger.

- Acheter aux "traders" : c'est des gars de la communauté qui font les mods eux même avec les vraies parts, tes parents seront peut être pas rassurés d'acheter à des inconnus, mais niveau qualité/prix c'est ce qu'il y a de mieux, et ceux de la fpsb sont vraiment sérieux.""")

@bot.command()
async def yt_button(ctx):
	await ctx.send("Clique le bouton pour accéder à YouTube", components=[Button(style=ButtonStyle.red, label="Obtenir le lien", custom_id="yt_button")])


@tasks.loop()
async def yt_button_press():
	interaction = await bot.wait_for("button_click", check=lambda i: i.component.custom_id == "yt_button")
	user_id = interaction.author.id
	guild = interaction.guild
	author = await guild.fetch_member(user_id)
	if author.voice is None:
		await interaction.respond(type=InteractionType.ChannelMessageWithSource, content='Tu dois être connecté à un salon vocal !')
		return
	link = await together_control.create_link(author.voice.channel.id, 'youtube')
	await interaction.respond(type=InteractionType.ChannelMessageWithSource, content=f"{link}")

yt_button_press.start()


@bot.command()
async def v5(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/v5\'', flush=True)
	fpsb_emoji = discord.utils.get(ctx.guild.emojis, name='fpsb')
	await ctx.send(f'{fpsb_emoji} Voici le lien de la V5 : https://www.penspinning-france.fr')

@bot.command()
async def v4(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/v4\'', flush=True)
	fpsb_emoji = discord.utils.get(ctx.guild.emojis, name='fpsb')
	await ctx.send(f'{fpsb_emoji} Voici le lien de la V4 : https://thefpsb.1fr1.net/')

@bot.command()
async def v3(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/v3\'', flush=True)
	fpsb_emoji = discord.utils.get(ctx.guild.emojis, name='fpsb')
	await ctx.send(f'{fpsb_emoji} Voici de lien de la V3 : https://thefpsb.penspinning.fr/index.php?sid=6347c1d3d780810f4b52a70f5323c167')

@bot.command()
async def v2(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/v2\'', flush=True)
	fpsb_emoji = discord.utils.get(ctx.guild.emojis, name='fpsb')
	await ctx.send(f'{fpsb_emoji} Voici le lien de la V2 : https://thefpsbv2.penspinning.fr/')

def format_posts(posts):
	formatted = ""
	if len(posts) > 1:
		nb_posts = len(posts)
		formatted += f"{nb_posts} nouvelles collabs arrivent !\n\n"
	elif len(posts) == 1:
		formatted += f"Une nouvelle collab arrive !\n\n"
	for p in posts:
		title = p['title']
		author = p['author']
		link = p['link']
		formatted += f"**Organisateur** {author}\n**Titre** : {title}\n\nInformations supplémentaires : {link}\n\n"
	if len(formatted) > 2000:
		formatted = formatted[:1999]
	return formatted


@tasks.loop(seconds=300)
async def discourse_notif():
	new_posts = get_new_discourse_posts()
	if len(new_posts) > 0:
		chan = await bot.fetch_channel(NOTIF_CHAN)
		await chan.send(format_posts(new_posts))

discourse_notif.start()


def format_videos(videos):
	formatted = ""
	if len(videos) > 1:
		formatted += "Nouvelles vidéos de PS Academy !\n\n"
	elif len(videos) == 1:
		formatted += f"Nouvele vidéo de PS Academy !\n\n"
	for v in videos:
		title = v['title']
		link = v['link']
		formatted += f"**{title}**\n\n{link}\n\n"
	if len(formatted) > 2000:
		formatted = formatted[:1999]
	return formatted



@tasks.loop(seconds=300)
async def ps_academy_notif():
	new_videos = get_new_ps_academy_posts()
	if len(new_videos) > 0:
		chan = await bot.fetch_channel(VIDEO_CHAN)
		await chan.send(format_videos(new_videos))

ps_academy_notif.start()


@bot.command()
async def spinner(ctx, s: str):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/social {s}\'', flush=True)
	embed = discord.Embed(
		title = s,
		colour = discord.Colour.blue()
	)
	embed.add_field(name='YouTube', value='https://www.youtube.com/user/ebanNG', inline=False)
	embed.add_field(name='Twitter', value='https://twitter.com/aleuzac_eban', inline=False)
	await ctx.send(embed=embed)



@bot.command(aliases=['tuto', 'psa'])
async def academy(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/academy\'', flush=True)
	await ctx.send("""Penspinning Academy est une chaîne de tutoriels communautaire de la FPSB. Cela signifie que chacun est libre d'y faire ses propres tutoriels !
La chaîne est disponible ici : https://www.youtube.com/channel/UC5chm7XPK_snAZYgG7c6srg""")


@bot.group(invoke_without_command=True)
async def aide(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/aide\'', flush=True)
	embed = discord.Embed(
	title = 'Liste des commandes',
	colour = discord.Colour.blue()
	)
	embed.add_field(name='Commandes d\'information', value="""`/ordre`
`/trade`
`/v5`
`/v4`
`/v3`
`/v2`
`/academy`
`/spinner <spinner>`""", inline=True)
	embed.add_field(name='Commandes utilitaires', value="""`/timer`""", inline=True)
	await ctx.send(embed=embed)

@aide.command(name='timer')
async def timer_help(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/aide timer\'', flush=True)
	await ctx.reply('`/timer <durée> (intervalle)` lance un timer de la durée spécifiée qui se mettra à jour selon l\'intervalle précisé. Si aucun intervalle n\'est donné ou que celui ci est supérieur à la durée du timer, il prendra la valeur 1 par défaut.')

@aide.command(name='ordre')
async def ordre_help(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/aide ordre\'', flush=True)
	await ctx.reply('`/ordre` renvoie l\'image de l\'ordre d\'apprentissage des tricks recommandé pour les débutants.')

@aide.command(name='trade')
async def trade_help(ctx):
	print(f'{asctime(localtime())} : {ctx.author} used command \'/aide trade\'', flush=True)
	await ctx.reply('`/trade` renvoie des informations sur l\'achat de mods ou de parts pour faire des mods')


@bot.command()
async def test(ctx):
	channel = ctx.channel
	author = ctx.author
	command = ctx.command
	await ctx.reply('coucou', reference=discord.Message(author=author, channel=channel, content=f'used {command}'))


@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.errors.CommandNotFound):
		print(f'{asctime(localtime())} : {ctx.author} used a command that does not exist', flush=True)
		command_used = ctx.message.content.split()[0]
		embed = discord.Embed(
		title = 'Liste des commandes',
		colour = discord.Colour.blue()
		)
		embed.add_field(name='Commandes d\'information', value="""`/ordre`
`/trade`
`/v5`
`/v4`
`/v3`
`/v2`
`/academy`
`/spinner <spinner>`""", inline=True)
		embed.add_field(name='Commandes utilitaires', value="""`/timer`""", inline=True)
		await ctx.send(f'La commande `{command_used}` n\'existe pas ! Voici la liste des commandes disponibles :', embed=embed)
	else:
		logging.error(error)
		raise error


bot.run(TOKEN)
