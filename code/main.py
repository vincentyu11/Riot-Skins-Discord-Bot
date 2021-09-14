# Created by Vincent Yu

import discord
import os
import praw
import random
import json
import requests
import sqlite3
import numpy as np
from discord.ext import commands

db_league = sqlite3.connect('league.sqlite')
cursor_league = db_league.cursor()
cursor_league.execute('''
               CREATE TABLE IF NOT EXISTS skins(
               champion_name TEXT,
               skin_name TEXT,
               skin_id TEXT,
               skin_no TEXT,
               chroma TEXT,
               img_url TEXT,
               UNIQUE(skin_name, skin_id, img_url)
               )
               ''')
db_league.commit()
cursor_league.close()

db_valorant = sqlite3.connect('valorant.sqlite')
cursor_valorant = db_valorant.cursor()
cursor_valorant.execute('''
               CREATE TABLE IF NOT EXISTS skins(
               skin_name TEXT,
               weapon_name TEXT,
               img_url TEXT,
               UNIQUE(skin_name, weapon_name, img_url)
               )
               ''')
db_valorant.commit()
cursor_valorant.close()


# list = np.loadtxt('code\weapons.txt', dtype='U')
# np.asarray(list)
# print(list)


client = commands.Bot(command_prefix='!')

reddit = praw.Reddit(client_id = 'uUekxQ-fOdGu6q366PLoyQ',
                     client_secret = 'BHiDvT8tJjUpVPF-DYVU3JO8DEQ-Qg',
                     username = 'valowant_bot',
                     password = 'Valowantbot123*',
                     user_agent = 'valowant_bot v1.0',
                     check_for_async = False)

def val_skin_data():    
    with open('code\weapons.txt', 'r') as f:
        weapon_list = [line.strip() for line in f]

    r = requests.get('https://valorant-api.com/v1/weapons/skins')
    dict = r.json()

    sqlite_entries = []

    for i in weapon_list:
        for j in range(len(dict['data'])):
            if i in dict['data'][j]['displayName']:
                for k in range(len(dict['data'][j]['chromas'])):
                    sqlite_row = []
                    if dict['data'][j]['chromas'][k]['displayName'] != "Standard":
                        sqlite_row.append(dict['data'][j]['chromas'][k]['displayName'])
                    else: 
                        sqlite_row.append(dict['data'][j]['displayName'])
                    sqlite_row.append(i)
                    sqlite_row.append(dict['data'][j]['chromas'][k]['fullRender'])
                    sqlite_entries.append(sqlite_row)
    for i in range(len(dict['data'])):
        if any(word in dict['data'][i]['displayName'] for word in weapon_list):
            pass
        else:
            for j in range(len(dict['data'][i]['chromas'])):
                sqlite_row = []
                if dict['data'][i]['chromas'][j]['displayName'] != "Standard":
                    sqlite_row.append(dict['data'][i]['chromas'][j]['displayName'])
                else: 
                    sqlite_row.append(dict['data'][i]['displayName'])
                sqlite_row.append('Knife')
                sqlite_row.append(dict['data'][i]['chromas'][j]['fullRender'])
                sqlite_entries.append(sqlite_row)
    
    db_valorant = sqlite3.connect('valorant.sqlite')
    cursor_valorant = db_valorant.cursor()
    for i in range(len(sqlite_entries)):
        cursor_valorant.execute('INSERT OR IGNORE INTO skins values (?,?,?)', sqlite_entries[i])
    
    db_valorant.commit()
    cursor_valorant.close()

def league_skin_data():
    with open('code\champions.txt', 'r') as f:
        champion_list = [line.strip() for line in f]    

    r = requests.get('http://ddragon.leagueoflegends.com/cdn/11.16.1/data/en_US/championFull.json')
    dict = r.json()
    
    sqlite_entries = []

    for i in champion_list:
        for j in range(len(dict['data'][i]['skins'])):
            sqlite_row = []
            sqlite_row.append(dict['data'][i]['id'])
            sqlite_row.append(dict['data'][i]['skins'][j]['name'])
            sqlite_row.append(dict['data'][i]['skins'][j]['id'])
            sqlite_row.append(dict['data'][i]['skins'][j]['num'])
            sqlite_row.append(dict['data'][i]['skins'][j]['chromas'])

            skin_num = str(dict['data'][i]['skins'][j]['num'])
            img_url = "http://ddragon.leagueoflegends.com/cdn/img/champion/splash/" + i + "_" + skin_num + ".jpg"
            sqlite_row.append(img_url)

            sqlite_entries.append(sqlite_row)

    db_league = sqlite3.connect('league.sqlite')
    cursor_league = db_league.cursor()
    for i in range(len(sqlite_entries)):
        cursor_league.execute('INSERT OR IGNORE INTO skins values (?,?,?,?,?,?)', sqlite_entries[i])
    
    db_league.commit()
    cursor_league.close()

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.command()
async def hello(ctx, user: discord.Member = None):
    if user is None:
        user = ctx.author
    await ctx.send("Hello, " + user.mention)

@client.command()
async def meme(ctx):
    subreddit = reddit.subreddit("memes")
    all_submissions = []

    top = subreddit.top(limit=25)

    for submission in top:
        all_submissions.append(submission)

    random_submission = random.choice(all_submissions)

    name = random_submission.title
    url = random_submission.url

    em = discord.Embed(title = name)
    em.set_image(url = url)

    await ctx.send(embed = em)


@client.command()
async def lolskins(ctx, champion_name):

    with open('code\champions.txt', 'r') as f:
        champion_list = [line.strip() for line in f]   

    champname_formal = champion_name.capitalize()
    get_titles = []
    get_img_urls = []

    db = sqlite3.connect('league.sqlite')
    cursor = db.cursor()

    if champname_formal in champion_list: 
        cursor.execute('SELECT skin_name FROM skins WHERE champion_name = ?', (champname_formal,))
        db.commit()
        for row in cursor:
            get_titles.append(row)
        cursor.execute('SELECT img_url FROM skins WHERE champion_name = ?', (champname_formal,))
        db.commit()
        for row in cursor:
            get_img_urls.append(row)
    else:
        var = "%" + champname_formal + "%"
        cursor.execute('SELECT skin_name FROM skins WHERE skin_name LIKE ?', (var,))
        db.commit()
        for row in cursor:
            get_titles.append(row)
        cursor.execute('SELECT img_url FROM skins WHERE skin_name LIKE ?', (var,))
        db.commit()
        for row in cursor:
            get_img_urls.append(row)
    cursor.close()

    titles = [i[0] for i in get_titles]
    img_urls = [i[0] for i in get_img_urls]


    pages = []

    for i in range(len(titles)):
        page = discord.Embed(
            title = titles[i],
        )
        page.set_footer(text = str((i+1)) + '/' + str((len(titles))))
        page.set_image(url=img_urls[i])
        pages.append(page)

    message = await ctx.send(embed = pages[0])
    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author
    i = 0
    reaction = None

    while True:
        if str(reaction) == '⏮':
            i = 0
            await message.edit(embed = pages[i])
        elif str(reaction) == '◀':
            if i > 0:
                i -= 1
                await message.edit(embed = pages[i])
            else:
                await message.edit(embed = pages[i])
        elif str(reaction) == '▶':
            if i < len(titles)-1:
                i += 1
                await message.edit(embed = pages[i])
            else:
                await message.edit(embed = pages[i])
        elif str(reaction) == '⏭':
            i = len(titles)-1
            await message.edit(embed = pages[i])
        
        try:
            reaction, user = await client.wait_for('reaction_add', timeout = 30.0, check = check)
            await message.remove_reaction(reaction, user)
        except:
            break

    await message.clear_reactions()


@client.command()
async def valskins(ctx, keyword):

    with open('code\weapons.txt', 'r') as f:
        weapon_list = [line.strip() for line in f]

    keyword_formal = keyword.capitalize()
    get_titles = []
    get_img_urls = []

    db = sqlite3.connect('valorant.sqlite')
    cursor = db.cursor()

    if keyword_formal in weapon_list: 
        cursor.execute('SELECT skin_name FROM skins WHERE weapon_name = ?', (keyword_formal,))
        db.commit()
        for row in cursor:
            get_titles.append(row)
        cursor.execute('SELECT img_url FROM skins WHERE weapon_name = ?', (keyword_formal,))
        db.commit()
        for row in cursor:
            get_img_urls.append(row)
    else: 
        var = "%" + keyword_formal + "%"
        cursor.execute('SELECT skin_name FROM skins WHERE skin_name LIKE ?', (var,))
        db.commit()
        for row in cursor:
            get_titles.append(row)
        cursor.execute('SELECT img_url FROM skins WHERE skin_name LIKE ?', (var,))
        db.commit()
        for row in cursor:
            get_img_urls.append(row)
    cursor.close()

    titles = [i[0] for i in get_titles]
    img_urls = [i[0] for i in get_img_urls]


    pages = []

    for i in range(len(titles)):
        page = discord.Embed(
            title = titles[i],
        )
        page.set_footer(text = str((i+1)) + '/' + str((len(titles))))
        page.set_image(url=img_urls[i])
        pages.append(page)

    message = await ctx.send(embed = pages[0])
    await message.add_reaction('⏮')
    await message.add_reaction('◀')
    await message.add_reaction('▶')
    await message.add_reaction('⏭')

    def check(reaction, user):
        return user == ctx.author
    i = 0
    reaction = None

    while True:
        if str(reaction) == '⏮':
            i = 0
            await message.edit(embed = pages[i])
        elif str(reaction) == '◀':
            if i > 0:
                i -= 1
                await message.edit(embed = pages[i])
            else:
                await message.edit(embed = pages[i])
        elif str(reaction) == '▶':
            if i < len(titles)-1:
                i += 1
                await message.edit(embed = pages[i])
            else:
                await message.edit(embed = pages[i])
        elif str(reaction) == '⏭':
            i = len(titles)-1
            await message.edit(embed = pages[i])
        
        try:
            reaction, user = await client.wait_for('reaction_add', timeout = 30.0, check = check)
            await message.remove_reaction(reaction, user)
        except:
            break

    await message.clear_reactions()

@client.command()
async def chest(ctx):

    hextech_img = 'images\Hextech_Crafting_Hextech_Chest.png'
    masterwork_img = 'images\Hextech_Crafting_Masterwork_Chest.png'

    chest_roll = random.randint(0,9)
    if chest_roll == 0:
        em = discord.Embed(title="Congratulations!", 
                           description="You have obtained a " + "**Masterwork Chest**" + "!",
                           colour = discord.Colour.orange()
                          )
        file = discord.File(masterwork_img, filename="image.png")
        em.set_image(url="attachment://image.png")
    else:
        em = discord.Embed(title="Congratulations!", 
                           description="You have obtained a " + "**Hextech Chest**" + "!",
                           colour = discord.Colour.blue()
                           )
        file = discord.File(hextech_img, filename="image.png")
        em.set_image(url="attachment://image.png")

    await ctx.send(file = file, embed = em)

def main():
    print("hi")
    # lol_skin_data()
    # val_skin_data()
    

if __name__ == "__main__":
    main()


client.run()
