#!/usr/bin/env python3
from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery
from requests import post as rpost
from markdown import markdown
from random import choice
from datetime import datetime
from calendar import month_name
from pycountry import countries as conn
from urllib.parse import quote as q
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
LOGGER = logging.getLogger(__name__)

# Bot configuration
api_id = 25713073  # Replace with your Telegram API ID
api_hash = "65a23aaa7a97f42475de52ed240af2f3"  # Replace with your Telegram API hash
bot_token = "8243250670:AAF8dIc3CqAWTn7Ex6jWp5nPgmMdE3kIB4U"  # Replace with your bot token

# Initialize the bot
bot = Client("anime_bot", api_id=api_id, api_hash=api_hash, bot_token=bot_token)

# Bot commands class
class BotCommands:
    AniListCommand = "anime"
    AnimeHelpCommand = "animehelp"

# Custom filters (simplified for this example)
class CustomFilters:
    @staticmethod
    def authorized(_, __):
        return True
    
    @staticmethod
    def blacklisted(_, __):
        return False

# Helper functions
def get_readable_time(seconds):
    periods = [('d', 86400), ('h', 3600), ('m', 60), ('s', 1)]
    result = []
    for period_name, period_seconds in periods:
        if seconds >= period_seconds:
            period_value, seconds = divmod(seconds, period_seconds)
            result.append(f"{int(period_value)}{period_name}")
    return ' '.join(result) if result else "0s"

# Button builder class
class ButtonMaker:
    def __init__(self):
        self.button = []
        self.header_button = []
    
    def ibutton(self, text, data, position=None):
        self.button.append((text, data, position))
    
    def ubutton(self, text, url, position=None):
        if position == "header":
            self.header_button.append((text, url))
        else:
            self.button.append((text, url))
    
    def build_menu(self, b_cols=1):
        menu = []
        if self.header_button:
            menu.append(self.header_button)
        if self.button:
            menu += [self.button[i:i + b_cols] for i in range(0, len(self.button), b_cols)]
        return menu

# Message utils (simplified)
async def sendMessage(message: Message, text, buttons=None, photo=None):
    if photo:
        return await message.reply_photo(photo=photo, caption=text, reply_markup=buttons)
    return await message.reply(text, reply_markup=buttons)

async def editMessage(message: Message, text, buttons=None):
    return await message.edit(text, reply_markup=buttons)

# Emoji mapping for genres
GENRES_EMOJI = {
    "Action": "👊",
    "Adventure": choice(["🪂", "🧗‍♀"]),
    "Comedy": "🤣",
    "Drama": "🎭",
    "Ecchi": choice(["💋", "🥵"]),
    "Fantasy": choice(["🧞", "🧞‍♂", "🧞‍♀", "🌗"]),
    "Hentai": "🔞",
    "Horror": "☠",
    "Mahou Shoujo": "☯",
    "Mecha": "🤖",
    "Music": "🎸",
    "Mystery": "🔮",
    "Psychological": "♟",
    "Romance": "💞",
    "Sci-Fi": "🛸",
    "Slice of Life": choice(["☘", "🍁"]),
    "Sports": "⚽️",
    "Supernatural": "🫧",
    "Thriller": choice(["🥶", "🔪", "🤯"]),
}

# GraphQL queries
ANIME_GRAPHQL_QUERY = """
query ($id: Int, $idMal: Int, $search: String) {
  Media(id: $id, idMal: $idMal, type: ANIME, search: $search) {
    id
    idMal
    title {
      romaji
      english
      native
    }
    type
    format
    status(version: 2)
    description(asHtml: false)
    startDate {
      year
      month
      day
    }
    endDate {
      year
      month
      day
    }
    season
    seasonYear
    episodes
    duration
    chapters
    volumes
    countryOfOrigin
    source
    hashtag
    trailer {
      id
      site
      thumbnail
    }
    updatedAt
    coverImage {
      large
    }
    bannerImage
    genres
    synonyms
    averageScore
    meanScore
    popularity
    trending
    favourites
    tags {
      name
      description
      rank
    }
    relations {
      edges {
        node {
          id
          title {
            romaji
            english
            native
          }
          format
          status
          source
          averageScore
          siteUrl
        }
        relationType
      }
    }
    characters {
      edges {
        role
        node {
          name {
            full
            native
          }
          siteUrl
        }
      }
    }
    studios {
      nodes {
         name
         siteUrl
      }
    }
    isAdult
    nextAiringEpisode {
      airingAt
      timeUntilAiring
      episode
    }
    airingSchedule {
      edges {
        node {
          airingAt
          timeUntilAiring
          episode
        }
      }
    }
    externalLinks {
      url
      site
    }
    rankings {
      rank
      year
      context
    }
    reviews {
      nodes {
        summary
        rating
        score
        siteUrl
        user {
          name
        }
      }
    }
    siteUrl
  }
}
"""

CHARACTER_QUERY = """
query ($id: Int, $search: String) {
    Character (id: $id, search: $search) {
        id
        name {
            first
            last
            full
            native
        }
        siteUrl
        image {
            large
        }
        description
    }
}
"""

MANGA_QUERY = """
query ($id: Int,$search: String) { 
    Media (id: $id, type: MANGA,search: $search) { 
        id
        title {
            romaji
            english
            native
        }
        description (asHtml: false)
        startDate{
            year
        }
        type
        format
        status
        siteUrl
        averageScore
        genres
        bannerImage
    }
}
"""

# AniList API URL
ANILIST_URL = "https://graphql.anilist.co"

# Global variable for spoiler text
sptext = ""

# Configuration dictionary
config_dict = {
    "ANIME_TEMPLATE": """<b>{ro_title}</b> (<code>{na_title}</code>)
<b>📌 ID</b>: <code>{siteid}</code>
<b>📅 Aired</b>: <code>{season}</code>
<b>⏳ Duration</b>: <code>{duration}</code>
<b>📊 Episodes</b>: <code>{episodes}</code>
<b>📡 Status</b>: <code>{status}</code>
<b>🏆 Score</b>: <code>{avgscore}</code>
<b>🎭 Genres</b>: {genres}

<b>📖 Synopsis</b>: <i>{description}</i>"""
}

# User data storage
user_data = {}

async def anilist(_, msg: Message, aniid=None, u_id=None):
    if not aniid:
        user_id = msg.from_user.id
        squery = msg.text.split(" ", 1)
        if len(squery) == 1:
            await sendMessage(msg, "<i>Provide AniList ID / Anime Name / MyAnimeList ID</i>")
            return
        vars = {"search": squery[1]}
    else:
        user_id = int(u_id)
        vars = {"id": aniid}
    
    try:
        response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": vars})
        animeResp = response.json()["data"].get("Media", None)
        
        if not animeResp:
            await sendMessage(msg, "No anime found with that query!")
            return
            
        ro_title = animeResp["title"]["romaji"]
        na_title = animeResp["title"]["native"]
        en_title = animeResp["title"]["english"] or ro_title
        format = animeResp["format"].capitalize() if animeResp["format"] else "N/A"
        status = animeResp["status"].capitalize() if animeResp["status"] else "N/A"
        year = animeResp["seasonYear"] or "N/A"
        
        try:
            sd = animeResp["startDate"]
            startdate = f"{month_name[sd['month']]} {sd['day']}, {sd['year']}" if sd["day"] and sd["year"] else ""
        except Exception:
            startdate = ""
            
        try:
            ed = animeResp["endDate"]
            enddate = f"{month_name[ed['month']]} {ed['day']}, {ed['year']}" if ed["day"] and ed["year"] else ""
        except Exception:
            enddate = ""
            
        season = f"{animeResp['season'].capitalize()} {animeResp['seasonYear']}" if animeResp.get('season') else "N/A"
        
        try:
            country = f"#{conn.get(alpha_2=animeResp['countryOfOrigin']).name}"
        except:
            country = "N/A"
            
        episodes = animeResp.get("episodes", "N/A")
        duration = f"{get_readable_time(animeResp['duration']*60)}" if animeResp.get('duration') else "N/A"
        avgscore = f"{animeResp['averageScore']}%" if animeResp.get('averageScore') else "N/A"
        
        genres = ", ".join(
            f"{GENRES_EMOJI.get(x, '🎭')} #{x.replace(' ', '_').replace('-', '_')}"
            for x in animeResp.get("genres", [])
        )
        
        studios = ", ".join(
            f"""<a href="{x['siteUrl']}">{x['name']}</a>"""
            for x in animeResp["studios"]["nodes"]
        ) if animeResp.get("studios", {}).get("nodes") else "N/A"
        
        source = animeResp["source"] or "-"
        hashtag = animeResp["hashtag"] or "N/A"
        synonyms = ", ".join(animeResp["synonyms"]) if animeResp.get("synonyms") else ""
        siteurl = animeResp.get("siteUrl", "")
        
        trailer = None
        if animeResp.get("trailer") and animeResp["trailer"].get("site") == "youtube":
            trailer = f"https://youtu.be/{animeResp['trailer']['id']}"
            
        description = animeResp.get("description", "N/A")
        if len(description) > 500:
            description = f"{description[:500]}...."
            
        siteid = animeResp.get("id")
        coverimg = animeResp["coverImage"]["large"] if animeResp.get("coverImage") else ""
        title_img = f"https://img.anili.st/media/{siteid}"
        
        btns = ButtonMaker()
        btns.ubutton("AniList Info 🎬", siteurl, "header")
        btns.ibutton("Reviews 📑", f"anime {user_id} rev {siteid}")
        btns.ibutton("Tags 🎯", f"anime {user_id} tags {siteid}")
        btns.ibutton("Relations 🧬", f"anime {user_id} rel {siteid}")
        btns.ibutton("Streaming Sites 📊", f"anime {user_id} sts {siteid}")
        btns.ibutton("Characters 👥️️", f"anime {user_id} cha {siteid}")
        
        if trailer:
            btns.ubutton("Trailer 🎞", trailer, "header")
            
        aniListTemp = user_data.get(user_id, {}).get("ani_temp", "") or config_dict["ANIME_TEMPLATE"]
        
        try:
            template = aniListTemp.format(**locals()).replace("<br>", "")
        except Exception as e:
            LOGGER.error(f"AniList Error: {e}")
            template = config_dict["ANIME_TEMPLATE"].format(**locals()).replace("<br>", "")
            
        if aniid:
            return template, btns.build_menu(3)
            
        try:
            await sendMessage(msg, template, btns.build_menu(3), photo=title_img)
        except Exception as e:
            LOGGER.error(f"Error sending message: {e}")
            await sendMessage(msg, template, btns.build_menu(3))
            
    except Exception as e:
        LOGGER.error(f"AniList Error: {e}")
        await sendMessage(msg, f"An error occurred: {e}")

async def setAnimeButtons(client: Client, query: CallbackQuery):
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
        return
        
    await query.answer()
    siteid = data[3]
    btns = ButtonMaker()
    btns.ibutton("⌫ Back", f"anime {data[1]} home {siteid}")
    
    try:
        if data[2] == "tags":
            response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": {"id": siteid}})
            aniTag = response.json()["data"].get("Media", None)
            msg = "<b>Tags :</b>\n\n" + "\n".join(
                f"""<a href="https://anilist.co/search/anime?genres={q(x['name'])}">{x['name']}</a> {x['rank']}%"""
                for x in aniTag["tags"]
            )
            
        elif data[2] == "sts":
            response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": {"id": siteid}})
            links = response.json()["data"].get("Media", None)
            msg = "<b>External & Streaming Links :</b>\n\n" + "\n".join(
                f"""<a href="{x['url']}">{x['site']}</a>""" 
                for x in links["externalLinks"]
            )
            
        elif data[2] == "rev":
            response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": {"id": siteid}})
            animeResp = response.json()["data"].get("Media", None)
            reList = animeResp["reviews"]["nodes"]
            msg = "<b>Reviews :</b>\n\n" + "\n\n".join(
                f"""<a href="{x['siteUrl']}">{x['summary']}</a>\n<b>Score :</b> <code>{x['score']} / 100</code>\n<i>By {x['user']['name']}</i>"""
                for x in reList[:8]
            )
            
        elif data[2] == "rel":
            response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": {"id": siteid}})
            animeResp = response.json()["data"].get("Media", None)
            msg = "<b>Relations :</b>\n\n" + "\n\n".join(
                f"""<a href="{x['node']['siteUrl']}">{x['node']['title']['english']}</a> ({x['node']['title']['romaji']})\n<b>Format</b>: <code>{x['node']['format'].capitalize()}</code>\n<b>Status</b>: <code>{x['node']['status'].capitalize()}</code>\n<b>Average Score</b>: <code>{x['node']['averageScore']}%</code>\n<b>Source</b>: <code>{x['node']['source'].capitalize()}</code>\n<b>Relation Type</b>: <code>{x.get('relationType', 'N/A').capitalize()}</code>"""
                for x in animeResp["relations"]["edges"]
            )
            
        elif data[2] == "cha":
            response = rpost(ANILIST_URL, json={"query": ANIME_GRAPHQL_QUERY, "variables": {"id": siteid}})
            animeResp = response.json()["data"].get("Media", None)
            msg = "<b>List of Characters :</b>\n\n" + "\n\n".join(
                f"""• <a href="{x['node']['siteUrl']}">{x['node']['name']['full']}</a> ({x['node']['name']['native']})\n<b>Role :</b> {x['role'].capitalize()}"""
                for x in (animeResp["characters"]["edges"])[:8]
            )
            
        elif data[2] == "home":
            msg, btns = await anilist(client, message, siteid, data[1])
            await editMessage(message, msg, btns)
            return
            
        await editMessage(message, msg, btns.build_menu(1))
        
    except Exception as e:
        LOGGER.error(f"Error in setAnimeButtons: {e}")
        await query.answer("An error occurred!", show_alert=True)

async def character(_, message: Message, aniid=None, u_id=None):
    global sptext
    rlp_mk = None
    
    if not aniid:
        search = message.text.split(" ", 1)
        if len(search) == 1:
            await sendMessage(
                message,
                "<b>Format :</b>\n<code>/character</code> <i>[search AniList Character]</i>",
            )
            return
        vars = {"search": search[1]}
        user_id = message.from_user.id
    else:
        vars = {"id": aniid}
        user_id = int(u_id)
        
    try:
        response = rpost(ANILIST_URL, json={"query": CHARACTER_QUERY, "variables": vars})
        json = response.json()["data"].get("Character", None)
        
        if not json:
            await sendMessage(message, "No character found with that query!")
            return
            
        msg = f"<b>{json.get('name').get('full')}</b> (<code>{json.get('name').get('native')}</code>)\n\n"
        description = json["description"]
        site_url = json.get("siteUrl")
        siteid = json.get("id")
        
        if "~!" in description and "!~" in description:
            btn = ButtonMaker()
            sptext = (
                description.split("~!", 1)[1]
                .rsplit("!~", 1)[0]
                .replace("~!", "")
                .replace("!~", "")
            )
            btn.ibutton("🔍 View Spoiler", f"cha {user_id} spoil {siteid}")
            rlp_mk = btn.build_menu(1)
            description = description.split("~!", 1)[0]
            
        if len(description) > 700:
            description = f"{description[:700]}...."
            
        msg += markdown(description).replace("<p>", "").replace("</p>", "")
        img = json.get("image", {}).get("large") if json.get("image") else None
        
        if aniid:
            return msg, rlp_mk
            
        if img:
            await sendMessage(message, msg, rlp_mk, img)
        else:
            await sendMessage(message, msg, rlp_mk)
            
    except Exception as e:
        LOGGER.error(f"Character Error: {e}")
        await sendMessage(message, f"An error occurred: {e}")

async def setCharacButtons(client: Client, query: CallbackQuery):
    global sptext
    message = query.message
    user_id = query.from_user.id
    data = query.data.split()
    
    if user_id != int(data[1]):
        await query.answer("Not Yours!", show_alert=True)
        return
        
    await query.answer()
    btns = ButtonMaker()
    btns.ibutton("⌫ Back", f"cha {data[1]} home {data[3]}")
    
    try:
        if data[2] == "spoil":
            await query.answer("Alert !! Shh")
            if len(sptext) > 900:
                sptext = f"{sptext[:900]}..."
            await editMessage(
                message,
                f"<b>Spoiler Ahead :</b>\n\n<tg-spoiler>{markdown(sptext).replace('<p>', '').replace('</p>', '')}</tg-spoiler>",
                btns.build_menu(1),
            )
        elif data[2] == "home":
            msg, btns = await character(client, message, data[3], data[1])
            await editMessage(message, msg, btns)
            
    except Exception as e:
        LOGGER.error(f"Error in setCharacButtons: {e}")
        await query.answer("An error occurred!", show_alert=True)

async def manga(_, message: Message):
    search = message.text.split(" ", 1)
    if len(search) == 1:
        await sendMessage(
            message, "<b>Format :</b>\n<code>/manga</code> <i>[search manga]</i>"
        )
        return
        
    search = search[1]
    variables = {"search": search}
    
    try:
        response = rpost(ANILIST_URL, json={"query": MANGA_QUERY, "variables": variables})
        json = response.json()["data"].get("Media", None)
        
        if not json:
            await sendMessage(message, "No manga found with that query!")
            return
            
        title = json["title"].get("romaji", False)
        title_native = json["title"].get("native", False)
        start_date = json["startDate"].get("year", False)
        status = json.get("status", False)
        score = json.get("averageScore", False)
        
        msg = ""
        if title:
            msg += f"*{title}*"
            if title_native:
                msg += f"(`{title_native}`)"
                
        if start_date:
            msg += f"\n*Start Date* - `{start_date}`"
        if status:
            msg += f"\n*Status* - `{status}`"
        if score:
            msg += f"\n*Score* - `{score}`"
            
        msg += "\n*Genres* - "
        for x in json.get("genres", []):
            msg += f"#{x}, "
        msg = msg[:-2]
        
        info = json["siteUrl"]
        buttons = ButtonMaker()
        buttons.ubutton("AniList Info", info)
        
        description = json.get('description', '')
        msg += f"\n\n_{description}_"
        msg = msg.replace("<br>", "").replace("<i>", "").replace("</i>", "")
        
        image = f"https://img.anili.st/media/{json.get('id')}"
        
        try:
            await sendMessage(message, msg, buttons.build_menu(1), image)
        except Exception as e:
            LOGGER.error(f"Error sending manga: {e}")
            msg += f" [〽️]({image})"
            await sendMessage(message, msg, buttons.build_menu(1))
            
    except Exception as e:
        LOGGER.error(f"Manga Error: {e}")
        await sendMessage(message, f"An error occurred: {e}")

async def anime_help(_, message: Message):
    help_string = """
<u><b>🔍 Anime Help Guide</b></u>
• /anime : <i>[search AniList]</i>
• /character : <i>[search AniList Character]</i>
• /manga : <i>[search manga]</i>"""
    await sendMessage(message, help_string)

# Add handlers
bot.add_handler(
    filters.command(BotCommands.AniListCommand) & filters.private,
    anilist
)
bot.add_handler(
    filters.command("character") & filters.private,
    character
)
bot.add_handler(
    filters.command("manga") & filters.private,
    manga
)
bot.add_handler(
    filters.command(BotCommands.AnimeHelpCommand) & filters.private,
    anime_help
)
bot.add_handler(
    filters.regex(r"^anime"),
    setAnimeButtons
)
bot.add_handler(
    filters.regex(r"^cha"),
    setCharacButtons
)

if __name__ == "__main__":
    LOGGER.info("Starting Anime Bot...")
    bot.run()
