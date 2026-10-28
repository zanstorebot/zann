import asyncio
import random

from helpers import Quotly

DEFAULTUSER = "Nay"


NOBLE = [
    "╲╲╲┏━━┓╭━━━╮╱╱╱\n╲╲╲┗┓┏┛┃╭━╮┃╱╱╱\n╲╲╲╲┃┃┏┫┃╭┻┻┓╱╱\n╱╱╱┏╯╰╯┃╰┫┏━╯╱╱\n╱╱┏┻━┳┳┻━┫┗┓╱╱╱\n╱╱╰━┓┃┃╲┏┫┏┛╲╲╲\n╱╱╱╱┃╰╯╲┃┃┗━╮╲╲\n╱╱╱╱╰━━━╯╰━━┛╲╲",
    "┏━╮\n┃▔┃▂▂┏━━┓┏━┳━━━┓\n┃▂┣━━┻━╮┃┃▂┃▂┏━╯\n┃▔┃▔╭╮▔┃┃┃▔┃▔┗━┓\n┃▂┃▂╰╯▂┃┗╯▂┃▂▂▂┃\n┃▔┗━━━╮┃▔▔▔┃▔┏━╯\n┃▂▂▂▂▂┣╯▂▂▂┃▂┗━╮\n┗━━━━━┻━━━━┻━━━┛",
    "┏┓┏━┳━┳━┳━┓\n┃┗┫╋┣┓┃┏┫┻┫\n┗━┻━┛┗━┛┗━┛\n────­­­­­­­­­YOU────",
    "╦──╔╗─╗╔─╔ ─\n║──║║─║║─╠ ─\n╚═─╚╝─╚╝─╚ ─\n╦─╦─╔╗─╦╦   \n╚╦╝─║║─║║ \n─╩──╚╝─╚╝",
    "╔══╗....<3 \n╚╗╔╝..('\\../') \n╔╝╚╗..( •.• ) \n╚══╝..(,,)(,,) \n╔╗╔═╦╦╦═╗ ╔╗╔╗ \n║╚╣║║║║╩╣ ║╚╝║ \n╚═╩═╩═╩═╝ ╚══╝",
    "░I░L░O░V░E░Y░O░U░",
    "┈┈╭━╱▔▔▔▔╲━╮┈┈┈\n┈┈╰╱╭▅╮╭▅╮╲╯┈┈┈\n╳┈┈▏╰┈▅▅┈╯▕┈┈┈┈\n┈┈┈╲┈╰━━╯┈╱┈┈╳┈\n┈┈┈╱╱▔╲╱▔╲╲┈┈┈┈\n┈╭━╮▔▏┊┊▕▔╭━╮┈╳\n┈┃┊┣▔╲┊┊╱▔┫┊┃┈┈\n┈╰━━━━╲╱━━━━╯┈╳",
    "╔ღ═╗╔╗\n╚╗╔╝║║ღ═╦╦╦═ღ\n╔╝╚╗ღ╚╣║║║║╠╣\n╚═ღ╝╚═╩═╩ღ╩═╝",
    "╔══╗ \n╚╗╔╝ \n╔╝(¯'v'¯) \n╚══'.¸./\n╔╗╔═╦╦╦═╗ ╔╗╔╗ \n║╚╣║║║║╩╣ ║╚╝║ \n╚═╩═╩═╩═╝ ╚══╝",
    "╔╗ \n║║╔═╦═╦═╦═╗ ╔╦╗ \n║╚╣╬╠╗║╔╣╩╣ ║║║ \n╚═╩═╝╚═╝╚═╝ ╚═╝ \n╔═╗ \n║═╬═╦╦╦═╦═╦═╦═╦═╗ \n║╔╣╬║╔╣╩╬╗║╔╣╩╣╔╝ \n╚╝╚═╩╝╚═╝╚═╝╚═╩╝",
    "╔══╗ \n╚╗╔╝ \n╔╝╚╗ \n╚══╝ \n╔╗ \n║║╔═╦╦╦═╗ \n║╚╣║║║║╚╣ \n╚═╩═╩═╩═╝ \n╔╗╔╗ ♥️ \n║╚╝╠═╦╦╗ \n╚╗╔╣║║║║ \n═╚╝╚═╩═╝",
    "╔══╗╔╗  ♡ \n╚╗╔╝║║╔═╦╦╦╔╗ \n╔╝╚╗║╚╣║║║║╔╣ \n╚══╝╚═╩═╩═╩═╝\n­­­─────­­­­­­­­­YOU─────",
    "╭╮╭╮╮╭╮╮╭╮╮╭╮╮ \n┃┃╰╮╯╰╮╯╰╮╯╰╮╯ \n┃┃╭┳━━┳━╮╭━┳━━╮ \n┃┃┃┃╭╮┣╮┃┃╭┫╭╮┃ \n┃╰╯┃╰╯┃┃╰╯┃┃╰┻┻╮ \n╰━━┻━━╯╰━━╯╰━━━╯",
    "┊┊╭━╮┊┊┊┊┊┊┊┊┊┊┊ \n━━╋━╯┊┊┊┊┊┊┊┊┊┊┊ \n┊┊┃┊╭━┳╮╭┓┊╭╮╭━╮ \n╭━╋━╋━╯┣╯┃┊┃╰╋━╯ \n╰━╯┊╰━━╯┊╰━┛┊╰━━",
]

async def lopyu_cmd(client, message):
    await message.reply(
      """
      ⠀⠀⠀⠀⠀      ⣠⣄⡀
      ⠀⠀⠀⠀⡞⠉⠙⢳⣄⢀⡾⠁⠈⣿
      ⠀⠀⠀⠀⢻⡄⠀⠀⠙⢿⡇⠀⢰⠇
      ⠀⠀⠀⠀⠀⠙⣦⡀⠀⠀⠹⣦⡟
      ⠀⠀⠀⠀⠀⠀⠈⢳⣄⠀⠀⠈⠻⣄
      ⠀⠀⠀⠀⠀⠀⡞⠋⠛⢧⡀⠀⠀⠘⢷⡀
      ⠀⠀⠀⢠⡴⠾⣧⡀⠀⠀⠹⣦⠀⠀⠈⢿⡏
      ⠀⠀⣀⣿⠀⠀⠈⠻⣄⠀⠀⠀⠀⠀⠀⠌⣷
      ⢠⡟⠉⠛⢷⣄⠀⠀⠈⠀⠀⠀⠀⠀⢀⣱⠏
      ⠀⢷⡀⠀⠀⠉⠃⠀⠀⠀⠀⠀⠀⠀⣶⠏⠀
      ⠀⠈⠻⣦⡀⠀⠀⠀⠀⠀⠀⢀⣠⠞⠇⠀⠀
      ⠀⠀⠀⠈⠙⠶⣤⣤⣤⡤⠶⠋⠁
      """
    )

async def hot_cmd(client, message):
    await message.reply(
    """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠀⠊⠁⠈⢘⣒⣤⠠⠰⣤⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠐⠀⢀⠀⠀⢐⡩⡽⣿⣟⡄⠉⣻⣷⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⢌⣴⡴⠊⣁⢔⣈⣰⡜⢉⣿⣿⡻⣤⣹⣿⣿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣲⡿⢋⣤⣞⣵⣿⡟⣡⣔⣯⣿⣧⣯⣷⣿⣿⣿⣿⣿⣦⠐⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣮⣞⣵⢿⣿⣿⣿⣷⣿⣿⣿⡿⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⠐⢯⣿⣿⣿⣿⣿⣿⣿⣿⣿⡟⢡⠉⠜⣿⣿⣿⢻⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡸⣾⣿⣿⣿⣿⣿⣿⣿⣿⠟⠀⠂⠀⢈⣿⣷⣿⠀⣿⢻⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⣿⣟⣻⣿⣿⣿⣿⣿⣿⣏⣀⠀⠀⠀⠸⣿⢿⡶⢀⡟⠈⣼⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⢃⣿⣭⣿⣿⣿⣿⣿⣿⡏⢍⣙⠛⠷⠦⡄⢻⣼⠋⣼⣁⣀⣹⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎⢸⣿⣿⣿⣿⣿⣽⣿⠏⠻⠿⢿⣟⢦⢀⠀⠀⠉⠀⣉⣉⠉⢻⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃⣸⣿⣿⣿⣿⣿⣿⡟⡈⠀⠀⠀⠀⢀⢮⠀⠀⠀⠚⡛⠃⠿⣾⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣰⢳⣿⣿⣿⣿⣷⣿⣿⠱⠀⠁⠀⠀⠀⣨⠆⠃⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⢿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠃⢞⣿⣿⣿⣿⣿⣿⣟⠠⠁⠀⠀⠀⠘⠣⣼⠀⢀⠀⠀⠀⠀⠀⣼⣿⣿⣿⡻⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣼⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀⠈⢷⣤⡤⢤⣠⣀⣀⠨⠀⠀⣰⣿⣿⣿⠏⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⢼⡟⣽⣿⣿⣿⣿⣿⣿⣿⣆⢀⠀⠈⠱⠡⠔⠨⠎⠀⠀⣀⣼⣿⣿⣿⣻⠜⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠄⠀⢠⣿⢱⣿⣿⣿⣿⣿⣿⣿⣿⡜⠛⣧⡀⠀⠀⠀⠀⢀⢠⣾⣿⣿⣿⣿⣿⣯⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢼⣥⡿⣼⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠉⠒⠀⠐⠀⠀⢸⢿⣿⣿⣿⣿⣿⡤⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⠸⣼⠇⢸⣿⣿⣿⣿⣿⣿⢾⣯⡀⠀⠀⠀⠀⠀⠀⠀⠈⢸⣿⣟⣻⢟⣫⠥⠧⠤⠤⡀⠁⠐⠄⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡒⡀⠈⠻⡗⢹⣿⣿⣿⣿⣿⣿⣿⡇⣷⠀⠀⠀⠀⠀⣀⣀⣄⠾⠿⣷⠚⠉⠀⠘⡄⠣⠈⠔⠂⠀⠄⠀⠱⡄⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠈⠀⠀⢠⣤⡁⠉⢿⠿⣿⣿⣿⣿⣿⡟⠉⠂⠀⡐⠢⠁⠀⠀⠀⠀⠀⢿⡆⠀⠀⠐⠀⠁⠀⠀⠀⠀⠀⠀⠀⠘⠆⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠔⢁⡠⠤⠄⠂⠉⢫⡏⢷⣶⣷⣿⣿⣿⣿⣿⣟⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢫⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢘⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢊⡖⠉⠀⠀⠀⠀⠀⢈⢲⠾⢿⣿⣿⣿⣿⣿⢶⡚⢁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠈⣿⠠⠁⠀⠀⠀⠀⡀⠆⣤⠚⡉⢿⡿⢿⠿⠟⡉⠔⠠⠈⠀⠀⠀⠀⠀⢀⠠⠈⠄⡀⢀⠀⢿⣇⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣏⠆⡀⠀⠀⢠⢰⡡⢂⠁⠠⢉⣿⠇⠆⡘⢠⠀⢂⠀⠀⠀⠀⠀⢀⡐⢢⠁⢎⡐⠄⠂⠀⠸⣿⣆⠀⠀⠀⠀⠈⠆⠀⠀⠀⠀⠀⠀⡆⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢰⣏⠒⠠⢄⠣⣞⡟⡔⣂⠒⣀⢾⣿⢈⠱⣀⠃⠜⡀⠢⢀⠀⠀⢀⠲⣘⠢⡉⠤⠐⡈⠄⠁⠀⢸⣿⣄⠀⠀⠀⠀⠰⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣬⢧⠉⡒⣌⠳⣽⣟⣺⡴⠖⢫⠿⠇⡈⠐⠠⢈⠂⡐⠁⠂⠐⣀⢸⡳⢌⡁⠆⠁⢂⠀⠀⠀⠀⠈⣿⡿⣷⣄⠀⠀⠣⠀⠀⠀⠀⠀⠀⡇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢸⣃⠆⡱⢎⡽⣺⣿⠋⢀⠠⢻⣠⠀⠈⠡⠄⠀⠄⠀⠀⠈⠀⢈⣿⢆⢃⡐⠈⠀⠀⠀⠀⠀⠀⠀⣿⣏⣿⡝⣷⡀⠀⠁⠀⠀⠀⠀⠀⠇⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⢰⡇⢎⠵⣋⢶⡹⠁⠠⡀⢠⣻⣖⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠎⡠⢀⠀⠀⠀⠀⠀⠀⠀⢠⣿⢺⡵⣛⠼⣋⢦⠀⠐⡀⠀⠀⠀⠄⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠸⡝⡬⢳⡍⡞⠁⣤⣇⣶⣷⣿⣿⡖⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠆⠡⠀⠀⠀⠀⠀⠀⠀⠀⢸⡧⣗⢮⡱⢫⡜⢦⢣⠀⠄⠀⠀⢀⠃⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣟⡼⡱⢎⢇⣾⣿⣿⣿⣟⣧⣿⣷⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⢎⠡⠀⠀⠀⠀⠀⠀⠀⢀⣿⢫⡜⢎⡱⢣⠜⣢⢃⢆⠀⠀⠀⢰⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢹⢶⡙⣾⣮⣿⣿⣿⣻⡾⣽⣛⣿⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⢂⠀⠀⠀⠀⠀⠀⢀⣾⢣⠣⡜⣌⠲  ⡄⢎⢸⠀⠀⠀⡜⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠨⡷⡹⣌⣿⣿⣿⣿⣷⣻⢧⡛⡼⢿⣧⡀⠀⠀⠀⠀⠀⠀⠀⢸⣇⠂⠀⠀⠀⠀⠀⢀⣼⢏⡲⢱⠘⡄⠣⢸⠇⡈⠔⡸⠀⠀⢀⠃⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⣙⢦⣹⣿⣿⣿  ⢮⡕⡣⢍⣿⣧⡀⠀⠀⠀⠀⠀⠀⡌⠹⣧⡀⠀⠀⠀⢠⡾⣋⠎⡴⢁⠊⠄⡁⡾⠀⠐⢠⠁⠀⠀⣨⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣭⠖⡌⢿⣿⣿⣿⡽⣧⡛⡴⢃⠆⡋⡿⣦⡀⠀⠀⠀⡐⠀⠀⠀⠓⣄⣠⣼⣿⡳⣍⠚⠤⡁⠌⣀⠞⠀⢀⠜⠁⠀⠀⢀⠇⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⢌⠳⣈⠻⣟⣿⣿⣳⡽⣱⠍⡎⡔⡰⢨⢽⣷⣤⡼⠶⠖⠻⠛⠛⠋⠋⠺⣙⠻⠮⣏⣶⣼⣾⠭⠴⠒⠁⠀⠀⠀⠀⠘⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣎⡓⠄⡂⠌⢻⣽⣟⣿⣷⡿⣴⣣⣷⠿⢛⠩⠊⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⢸⡠⠀⠀⠀⡘⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢷⡉⢆⠡⢊⠦⣽⣾⣻⣟⡿⡻⡕⡒⢌⡁⠂⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡘⠀⠀⠀⢠⠃⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡵⢂⠑⢪⣽⣳⣿⣵⢾⣱⠓⣬⡱⢆⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠁⠀⠀⢀⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⠦⢌⢣⡟⣿⣿⣿⣯⣇⠋⢶⡹⢀⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠰⠀⠀⢀⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠻⣆⠥⡚⡽⢯⡿⣷⣏⠞⡈⢗⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠃⢀⠎⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢧⡱⣩⠟⣽⣻⣞⣯⠀⠍⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠪⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠐⠀⠀⠀⢀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⡛⣜⣳⣟⡦⣃⠐⡀⠆⡌⠀⢤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢄⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠁⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠳⣬⢋⡟⢶⢁⢂⠘⡴⣈⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠰⣀⠀⠀⠀⠀⠀⠀⠀⠀
⠌⡀⠀⡁⠀⢀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⢼⡻⣌⠢⠀⠎⡵⢂⠡⠀⠀⠀⠀⠀⠈⣤⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢢⠀⠀⠀⠀⠀⠀⠀
⠂⠄⠀⡀⠄⠀⢀⠀⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⡈⣷⣫⢕⠢⠄⡁⠎⡵⡉⠄⠀⠀⠀⠀⠀⢳⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡆⠀⠀⠀⠀⠀⠀
⠌⠠⠐⠀⠀⠌⠀⠀⠀⠀⠐⠀⠀⠁⠀⠀⠀⠠⠁⣾⠵⡊⢅⠂⠄⠓⡬⢑⠠⠀⠀⠀⠀⠀⠈⠛⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠼⡀⠀⠀⠀⠀⠀
⢂⠁⠠⢈⠀⠐⠈⢀⠠⠀⠀⠀⡀⠀⠀⠀⠀⠃⣼⣏⠳⠉⡄⠌⡀⠣⡘⠄⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⡿⠳⡀⠀⠀⠀⠀
⠂⠌⢀⠂⡀⢂⠠⠀⠀⡀⠐⠀⠀⠀⠀⠀⠀⢼⡷⢎⠆⠁⠀⢂⠁⢂⠱⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⠿⠁⠀⢣⠀⠀⠀⠀
⠡⢈⠀⢂⠐⢀⠀⠁⠄⠀⠀⠄⠀⠈⠀⠀⢀⠹⣿⡆⠌⠀⠀⠈⢂⠄⠂⠡⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⢤⣎⠗⠋⠀⠀⠀⠀⠇⠀⠀⠀
⣁⠂⡐⢀⠂⠄⢈⠀⠄⠈⡀⠄⠐⠀⠀⠀⡌⣠⠻⢿⣷⣦⣀⠀⠂⠠⠀⡁⠂⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⠤⡺⠭⠚⠁⠀⠀⠀⠀⠀⠀⠀⠡⡀
⠄⡂⠐⡀⢂⠈⠠⢀⠂⠐⡀⠐⠈⡀⠀⠀⣳⣯⣛⠤⡈⠙⠛⠻⠷⣶⣶⣤⣁⣂⡀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣀⣠⣴⠲⣋⡔⠉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢡
⢂⠅⢂⠐⠠⢈⠐⡀⠈⠄⡐⠈⠠⠀⠀⢀⣼⣳⢭⠲⣁⠂⠄⠀⠀⠀⠀⠙⢿⣿⣻⢿⡳⣖⠶⣶⣛⣿⣙⠳⣩⢡⢢⣱⠎⢀⡠⠆⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰
⡌⢂⠄⠌⡐⡀⠂⠄⠡⠀⠄⠡⠀⠁⠀⢀⢹⣧⢫⠱⣀⠊⢀⠀⠀⠀⠀⠤⡈⠹⢯⣿⣱⢏⡾⣰⡙⢦⢣⠓⡔⢢⣳⢃⡾⢋⠔⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⡄
⠆⡡⢈⠐⠠⢀⠡⠈⠄⠡⠈⠄⡁⠈⠀⠸⢸⣎⠧⢣⠐⡈⠀⠀⠀⠀⠀⠀⠈⠐⢌⡹⣟⣮⡳⣥⢫⢇⡏⠞⣌⣿⢷⠫⠜⡠⠈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⠜⣀⠂⠌⡐⢀⠂⠡⠈⠄⡁⢂⠄⠡⠀⡇⡿⡼⣙⠦⡑⠄⡁⠀⠀⠀⠀⠀⠀⠀⠀⠈⠢⣟⣿⣖⢯ ⣭⣿⣾⢛⡌⢣⠘⢀⠁⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡱⢀⠌⡐⢀⠂⠌⡠⢁⠂⠄⡁⢂⠐⡀⡇⣿⡱⣍⠲⣁⠂⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⡿ ⡟⡬⢃⠜⠠⠈⠄⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡇
⡔⠡⠂⢌⠠⢈⠐⡀⠂⠌⡐⠠⢁⠂⠄⢻⣯⢳⡍⡖⢄⠃⡈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣧ ⡿⣘⠱⡈⠌⠄⠡⢈⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⠇
⢌⡑⠈⡄⠂⢄⠂⠄⡁⠆⠠⡁⠢⢈⠐⢸⣯⢳⡝⡜⡠⠒⡀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣸⢧⢡⠃⡜⠠⠈⠔⡁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈
⠆⡌⢡⠠⠉⡄⠨⠄⡁⢂⠡⠀⡅⠂⠌⣈⣿⢳⡞⡥⡑⢂⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⢎⠢⡑⡀⠂⡍⠰⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡎
⢣⠘⡀⢆⠡⢂⢁⠂⠔⠠⡁⢡⠀⢃⠐⡀⣿⡳⡞⣥⠃⡌⠠⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⢎⠱⡐⣀⠣⢌⢁⠂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢰⠁
⢣⡑⢌⠂⡅⢢⠈⠔⡈⠔⡠⠁⢌⠐⡐⢀⢻⣵⠻⡴⡩⢄⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣌⠣⡐⢄⡊⠔⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡆
⢣⡘⢄⠣⢌⠰⣈⢂⠱⢈⠔⠡⣈⠐⡈⢄⠈⣯⣟⣱⡑⣂⠂⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣎⠱⣈⠦⡑⠊⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡘
⢣⡘⢄⢊⡄⢣⠐⡌⢄⠣⢈⠥⢀⠒⠠⡈⠄⢻⣜⢧⠳⡄⢃⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣇⠳⣄⢣⠱⡉⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⠂
⠣⡜⡐⢢⠘⡄⢣⠘⡄⢊⠔⡈⠆⡘⢠⠐⡡⠈⣿⣎⠷⡘⠄⢂⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣏⠶⣌⢣⠑⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⡂
⣓⢤⠃⡥⠚⣄⠃⢎⠰⡁⢎⠰⢡⠘⣀⠒⠤⠑⣸⢮⢏⡵⢈⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣏⡞⡌⢆⠡⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡜⠄"""
    )

      
async def entod_cmd(client, message):
    await message.reply(
"""⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠋⠀⠀⠀⠀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀pubg⠀⠀⢀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡀⠀⠀⠀⠀⠀⠀⠀⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣶⣄⣀⣀⣀⣠⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⠋⠉⠀⠀⠉⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⣿⡏⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⡟⠐⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⣿⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⢠⠀⠀⠀⠀⠘⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀⢀⣿⣧⡀⠀⠀⠀⠈⢿⣿⣿⣿⣿⣿⣿⣿⣿⣟
        ⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⣿⣷⣄⠀⠀⠀⠀⠹⣿⣿⣿⡿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⠿⠛⠉⠉⠳⣄⠀⠀⠀⠈⢻⣿⣿⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣆⠀⠀⠀⠀⠀⠀⠀⣾⣏⠀⠀⠀⠀⠀⠙⠦⡀⠀⠀⠀⣻⣿⣿⣿⣿
        ⣿⣿⣿⣿⣿⣿⡀⠀⠀⠂⠀⠀⠠⣿⡈⠀⠀⠀⡀⠀⠀⠀⠙⠆⠠⠔⠃⠀⠀⠉⠀⠀⠀
        ⣿⣿⣿⣿⣿⣿⡇⠀⠀⠀⠀⠀⠀⣿⣇⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⣿⣿⣿⣿⣿⣿⣷⠀⠀⠀⠀⠠⠀⢹⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀ff⠀⠀⠀⠀⠀⠀⠀
        ⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⢸⣿⡄⠀⠀⠀⠀⠀⢸⣿⣿⣷⣶⣶⡄⠀⠀⠀⠀⠀
        ⠋⠉⠉⠉⠉⠉⠉⠁⠀⠀⠀⠀⠀⢸⣿⣇⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣆⡀⠀⠀⡀
        ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡏⠉⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡇
        ⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀⢸⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
        ⣿⣿⣶⣶⣦⣤⣤⣤⣤⣤⣤⣤⣤⣤⣤⣾⣤⣤⣤⣤⣤⣤⣤⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿"""
    )
      
async def fvck_cmd(client, message):
    await message.reply(
"""⢀⡤⠤⣄⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⣾⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⡇⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⢸⡇⠀⠀⢸⡇⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⡾⠋⠻⡇⠀⠀⢸⣧⣀⡀⠀⠀⠀⠀
⠀⠀⢀⣾⠁⠀⠀⡇⠀⠀⢸⠁⠀⢹⣀⠀⠀⠀
⢀⡴⠋⡟⠀⠀⢠⡇⠀⠀⢸⠀⠀⠀⡇⠉⢆⠀
⡎⠀⠀⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⠀⠈⣆
⢷⡀⠀⠁⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸
⠀⠻⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣾
⠀⠀⠈⠻⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⠞⠁
⠀⠀⠀⠀⠈⣷⠀⠀⠀⠀⠀⠀⠀⠀⢰⠋⠀⠀
⠀⠀⠀⠀⠀⣿⠀⠀⠀⠀⠀⠀⠀⠀⡏⠀⠀⠀
⠀⠀⠀⠀⠀⠛⠒⠒⠒⠒⠒⠒⠒⠚⠃"""
    )

async def hah_cmd(client, message):
    await message.reply(
        """⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⡀⠀⠀⠀⠀⠀⠄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⡿⠇⠀⠀⠀⠀⢻⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀HAH...?⠀ ⠀⠀⠀⢀⡇⠀⠀⠀⠀⡸⣞⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠃⠀⠀⠀⢀⣧⢿⣽⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⢴⣿⠆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⠀⠀⠀⠀⣼⣞⡿⣞⡅⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠓⢤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣾⠀⠀⠀⣰⣟⢾⣽⢫⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⣠⢤⣶⡻⣞⣿⣺⢯⣽⣳⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⣄⡀⠀⠀⠀⠀⠙⢦⡀⠀⠀⠀⠀⣀⣠⣤⣿⣽⣻⢾⣽⣷⣾⣽⣻⣞⣷⣳⡄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⣶⣄⡀⠀⠀⠀⣉⣲⣴⢶⣞⡿⣽⣞⡷⣯⢿⡽⣞⣿⠟⠋⠁⠉⠈⠳⣟⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢻⣿⣿⣿⣿⢶⣾⣿⡽⣯⣟⡾⣽⡷⣯⣟⡽⡾⣽⡯⠁⠀⠀⠀⠀⠀⠀⢮⣭⣦⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠉⢞⣿⣿⢯⡿⣿⣯⣟⣷⣯⢿⣳⣟⡷⣽⣼⣻⣽⠀⠀⠀⠀⠀⠀⠀⢀⣼⡯⡗⠋⠤⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢾⣿⣿⣯⣽⣾⣿⣾⣗⡿⣯⡷⣯⣟⡷⣞⣼⣿⣀⠀⠀⠀⠀⢀⣠⡿⣏⡗⠈⠐⠈⠅⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⠛⠏⠉⠉⠽⢟⢿⣿⣿⣿⣿⣷⣻⢾⡽⣞⡷⠄⡹⣶⢿⣻⢿⣻⡽⢯⣼⢦⠶⠁⠈⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣯⠇⠀⠀⠀⠀⠀⠁⣽⣿⣿⣿⣷⣯⣿⣽⣛⡦⠀⠀⢩⣿⣹⢯⣷⢻⣟⠺⢣⡖⣘⠤⠓⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢈⣿⡃⠁⠀⠀⠀⢀⣤⣾⣟⢿⣻⣿⣿⣟⡾⣽⡳⠄⠎⢳⣯⢯⣟⡾⢯⣞⣯⣓⠉⢀⠀⠀⡄⢢⡀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣸⣷⣷⣶⣳⣶⣺⣿⣿⣳⢯⣟⣿⣿⣳⢯⠛⠅⠃⠀⠀⣴⣿⡿⣬⢶⠾⠙⣊⣥⠾⡒⠊⢁⢠⠣⣌⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢺⡽⣾⡽⣯⣟⣿⡿⣯⣿⣿⣾⢿⣿⠳⢏⣈⢠⠀⠀⣰⢿⡿⣽⣉⡶⠌⠋⠉⣀⡀⠁⠀⠀⠀⣘⡐⣂⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣽⣳⣟⣳⣟⣾⣽⣿⣿⣿⣿⣿⣦⣜⡻⡽⠆⠧⣴⡟⣯⢟⡳⣭⠲⠄⠐⠀⠀⠀⠈⠁⠉⠑⢊⡕⢃⠄⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⣾⣿⣯⣿⣾⣿⣿⣿⣿⣿⣿⣿⣿⣾⢧⠀⠹⠾⡵⡞⡽⢢⣃⠐⠀⠀⠄⡐⠀⠀⠀⡘⢦⠘⣌⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠐⠹⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢯⡏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠒⡈⠀⡀⠄⡑⠢⣉⠴⣈⣆
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⠻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⢯⣏⡴⣶⣵⣢⢤⢠⡀⡄⢠⠐⡰⢌⡱⠀⡁⡀⠆⡥⠆⡥⣛⡽⣾
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠔⠉⠀⠀⢽⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣼⣻⢷⣯⡽⣞⣷⣻⡼⣡⢋⡔⠣⠜⡐⢐⠠⡓⣤⣙⣲⣽⣻⢷
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡿⣽⣞⣷⣻⡴⣣⢜⡱⣊⡕⣊⠠⡙⡰⣭⢷⣯⣿⢿"""
    )

async def lopeyu_cmd(client, message):
    noble = random.randint(1, len(NOBLE) - 2)
    reply_text = NOBLE[noble]
    await message.reply(reply_text)


async def hmmm_cmd(client, message):
    return await message.reply(
        "┈┈╱▔▔▔▔▔╲┈┈┈HM┈HM\n┈╱┈┈╱▔╲╲╲▏┈┈┈HMMM\n╱┈┈╱━╱▔▔▔▔▔╲━╮┈┈\n▏┈▕┃▕╱▔╲╱▔╲▕╮┃┈┈\n▏┈▕╰━▏▊▕▕▋▕▕━╯┈┈\n╲┈┈╲╱▔╭╮▔▔┳╲╲┈┈┈\n┈╲┈┈▏╭━━━━╯▕▕┈┈┈\n┈┈╲┈╲▂▂▂▂▂▂╱╱┈┈┈\n┈┈┈┈▏┊┈┈┈┈┊┈┈┈╲\n┈┈┈┈▏┊┈┈┈┈┊▕╲┈┈╲\n┈╱▔╲▏┊┈┈┈┈┊▕╱▔╲▕\n┈▏┈┈┈╰┈┈┈┈╯┈┈┈▕▕\n┈╲┈┈┈╲┈┈┈┈╱┈┈┈╱┈╲\n┈┈╲┈┈▕▔▔▔▔▏┈┈╱╲╲╲▏\n┈╱▔┈┈▕┈┈┈┈▏┈┈▔╲▔▔\n┈╲▂▂▂╱┈┈┈┈╲▂▂▂╱┈ ",
    )


async def kntl_cmd(client, message):
    emoji = client.get_text(message)
    kontol = Quotly.GAMBAR_KONTOL
    if emoji:
        kontol = kontol.replace("⡀", emoji)
    await message.reply(kontol)


async def pns_cmd(client, message):
    emoji = client.get_text(message)
    titid = Quotly.GAMBAR_TITIT
    if emoji:
        titid = titid.replace("😋", emoji)
    await message.reply(titid)


async def heli_cmd(client, message):
    await message.reply(
        "▬▬▬.◙.▬▬▬ \n"
        "═▂▄▄▓▄▄▂ \n"
        "◢◤ █▀▀████▄▄▄▄◢◤ \n"
        "█▄ █ █▄ ███▀▀▀▀▀▀▀╬ \n"
        "◥█████◤ \n"
        "══╩══╩══ \n"
        "╬═╬ \n"
        "╬═╬ \n"
        "╬═╬ \n"
        "╬═╬ \n"
        "╬═╬ \n"
        "╬═╬ \n"
        "╬═╬ Hallo Semuanya :) \n"
        "╬═╬☻/ \n"
        "╬═╬/▌ \n"
        "╬═╬/ \\ \n",
    )


async def tembak_cmd(client, message):
    await message.reply(
        "_/﹋\\_\n"
        " (҂`_´)\n"
        "<,︻╦╤─ ҉\n"
        r"_/﹋\_"
        "\n<b>Mau Jadi Pacarku Gak?!</b>",
    )


async def bundir_cmd(client, message):
    await message.reply(
        "`Dadah Semuanya...`          \n　　　　　|"
        "\n　　　　　| \n"
        "　　　　　| \n"
        "　　　　　| \n"
        "　　　　　| \n"
        "　　　　　| \n"
        "　　　　　| \n"
        "　　　　　| \n"
        "　／￣￣＼| \n"
        "＜ ´･ 　　 |＼ \n"
        "　|　３　 | 丶＼ \n"
        "＜ 、･　　|　　＼ \n"
        "　＼＿＿／∪ _ ∪) \n"
        "　　　　　 Ｕ Ｕ\n",
    )


async def awk_cmd(client, message):
    await message.reply(
        "────██──────▀▀▀██\n"
        "──▄▀█▄▄▄─────▄▀█▄▄▄\n"
        "▄▀──█▄▄──────█─█▄▄\n"
        "─▄▄▄▀──▀▄───▄▄▄▀──▀▄\n"
        "─▀───────▀▀─▀───────▀▀\n`Awkwokwokwok..`",
    )


async def ysaja_cmd(client, message):
    await message.reply(
        "‡‡‡‡‡‡‡‡‡‡‡‡▄▄▄▄\n"
        "‡‡‡‡‡‡‡‡‡‡‡█‡‡‡‡█\n"
        "‡‡‡‡‡‡‡‡‡‡‡█‡‡‡‡█\n"
        "‡‡‡‡‡‡‡‡‡‡█‡‡‡‡‡█\n"
        "‡‡‡‡‡‡‡‡‡█‡‡‡‡‡‡█\n"
        "██████▄▄█‡‡‡‡‡‡████████▄\n"
        "▓▓▓▓▓▓█‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡█\n"
        "▓▓▓▓▓▓█‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡█\n"
        "▓▓▓▓▓▓█‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡█\n"
        "▓▓▓▓▓▓█‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡█\n"
        "▓▓▓▓▓▓█‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡‡█\n"
        "▓▓▓▓▓▓█████‡‡‡‡‡‡‡‡‡‡‡‡██\n"
        "█████‡‡‡‡‡‡‡██████████\n",
    )


async def tank_cmd(client, message):
    await message.reply(
        "█۞███████]▄▄▄▄▄▄▄▄▄▄▃ \n"
        "▂▄▅█████████▅▄▃▂…\n"
        "[███████████████████]\n"
        "◥⊙▲⊙▲⊙▲⊙▲⊙▲⊙▲⊙◤\n",
    )


async def babi_cmd(client, message):
    await message.reply(
        "┈┈┏━╮╭━┓┈╭━━━━╮\n"
        "┈┈┃┏┗┛┓┃╭┫Ngok ┃\n"
        "┈┈╰┓▋▋┏╯╯╰━━━━╯\n"
        "┈╭━┻╮╲┗━━━━╮╭╮┈\n"
        "┈┃▎▎┃╲╲╲╲╲╲┣━╯┈\n"
        "┈╰━┳┻▅╯╲╲╲╲┃┈┈┈\n"
        "┈┈┈╰━┳┓┏┳┓┏╯┈┈┈\n"
        "┈┈┈┈┈┗┻┛┗┻┛┈┈┈┈\n",
    )


async def ange_cmd(client, message):
    e = await message.edit("Ayanggg 😖")
    await asyncio.sleep(2)
    await e.edit("Aku Ange 😫")
    await asyncio.sleep(2)
    await e.edit("Ayuukk Picies Yang 🤤")


async def lipkoll_cmd(client, message):
    e = await message.edit("Ayanggg 😖")
    await asyncio.sleep(2)
    await e.edit("Kangeeen 👉👈")
    await asyncio.sleep(2)
    await e.edit("Pingiinn Slipkool Yaaang 🥺👉👈")


async def nakall_cmd(client, message):
    e = await message.edit("Ayanggg ih🥺")
    await asyncio.sleep(2)
    await e.edit("Nakal Banget Dah Ayang 🥺")
    await asyncio.sleep(2)
    await e.edit("Aku Gak Like Ayang 😠")
    await asyncio.sleep(2)
    await e.edit("Pokoknya Aku Gak Like Ih 😠")


async def peace_cmd(client, message):
    await message.reply(
        "┈┈┈┈PEACE MAN┈┈┈┈\n"
        "┈┈┈┈┈┈╭╮╭╮┈┈┈┈┈┈\n"
        "┈┈┈┈┈┈┃┃┃┃┈┈┈┈┈┈\n"
        "┈┈┈┈┈┈┃┃┃┃┈┈┈┈┈┈\n"
        "┈┈┈┈┈┈┃┗┛┣┳╮┈┈┈┈\n"
        "┈┈┈┈┈╭┻━━┓┃┃┈┈┈┈\n"
        "┈┈┈┈┈┃╲┏━╯┻┫┈┈┈┈\n"
        "┈┈┈┈┈╰╮╯┊┊╭╯┈┈┈┈\n",
    )


async def sponge_cmd(client, message):
    await message.reply(
        "╲┏━┳━━━━━━━━┓╲╲\n"
        "╲┃◯┃╭┻┻╮╭┻┻╮┃╲╲\n"
        "╲┃╮┃┃╭╮┃┃╭╮┃┃╲╲\n"
        "╲┃╯┃┗┻┻┛┗┻┻┻┻╮╲\n"
        "╲┃◯┃╭╮╰╯┏━━━┳╯╲\n"
        "╲┃╭┃╰┏┳┳┳┳┓◯┃╲╲\n"
        "╲┃╰┃◯╰┗┛┗┛╯╭┃╲╲\n",
    )


async def kocokk_cmd(client, message):
    e = await message.edit("KOCOKINNNN SAYANGG🥵")
    await asyncio.sleep(0.2)
    await e.edit("8✊===D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8✊===D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8✊===D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D💦")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8✊===D💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D💦💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8=✊==D💦💦💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8✊===D💦💦💦💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8===✊D💦💦💦💦💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("8==✊=D💦💦💦💦💦💦💦💦💦💦")
    await asyncio.sleep(0.2)
    await e.edit("**CROOTTTT**")
    await asyncio.sleep(0.2)
    await e.edit("**CROOTTTT AAAHHH.....**")
    await asyncio.sleep(0.2)
    await e.edit("AHHH ENAKKKKK SAYANGGGG🥵🥵**")


async def adadino_cmd(client, message):
    typew = await message.edit("`DIN DINNN.....`")
    await asyncio.sleep(1)
    await typew.edit("`DINOOOOSAURUSSSSS!!`")
    await asyncio.sleep(1)
    await typew.edit("`🏃                        🦖`")
    await typew.edit("`🏃                       🦖`")
    await typew.edit("`🏃                      🦖`")
    await typew.edit("`🏃                     🦖`")
    await typew.edit("`🏃   `LARII`          🦖`")
    await typew.edit("`🏃                   🦖`")
    await typew.edit("`🏃                  🦖`")
    await typew.edit("`🏃                 🦖`")
    await typew.edit("`🏃                🦖`")
    await typew.edit("`🏃               🦖`")
    await typew.edit("`🏃              🦖`")
    await typew.edit("`🏃             🦖`")
    await typew.edit("`🏃            🦖`")
    await typew.edit("`🏃           🦖`")
    await typew.edit("`🏃WOARGH!   🦖`")
    await typew.edit("`🏃           🦖`")
    await typew.edit("`🏃            🦖`")
    await typew.edit("`🏃             🦖`")
    await typew.edit("`🏃              🦖`")
    await typew.edit("`🏃               🦖`")
    await typew.edit("`🏃                🦖`")
    await typew.edit("`🏃                 🦖`")
    await typew.edit("`🏃                  🦖`")
    await typew.edit("`🏃                   🦖`")
    await typew.edit("`🏃                    🦖`")
    await typew.edit("`🏃                     🦖`")
    await typew.edit("`🏃  Huh-Huh           🦖`")
    await typew.edit("`🏃                   🦖`")
    await typew.edit("`🏃                  🦖`")
    await typew.edit("`🏃                 🦖`")
    await typew.edit("`🏃                🦖`")
    await typew.edit("`🏃               🦖`")
    await typew.edit("`🏃              🦖`")
    await typew.edit("`🏃             🦖`")
    await typew.edit("`🏃            🦖`")
    await typew.edit("`🏃           🦖`")
    await typew.edit("`🏃          🦖`")
    await typew.edit("`🏃         🦖`")
    await typew.edit("`DIA SEMAKIN MENDEKAT!!!`")
    await asyncio.sleep(1)
    await typew.edit("`🏃       🦖`")
    await typew.edit("`🏃      🦖`")
    await typew.edit("`🏃     🦖`")
    await typew.edit("`🏃    🦖`")
    await typew.edit("`Dahlah Pasrah Aja`")
    await asyncio.sleep(1)
    await typew.edit("`🧎🦖`")
    await asyncio.sleep(2)
    await typew.edit("`-TAMAT-`")


async def anjg_cmd(client, message):
    await message.reply(
        "╥━━━━━━━━╭━━╮━━┳\n"
        "╢╭╮╭━━━━━┫┃▋▋━▅┣\n"
        "╢┃╰┫┈┈┈┈┈┃┃┈┈╰┫┣\n"
        "╢╰━┫┈┈┈┈┈╰╯╰┳━╯┣\n"
        "╢┊┊┃┏┳┳━━┓┏┳┫┊┊┣\n"
        "╨━━┗┛┗┛━━┗┛┗┛━━┻\n",
    )


async def nahh_cmd(client, message):
    typew = await message.reply("`\n(\\_/)`" "`\n(●_●)`" "`\n />💖 *Ini Buat Kamu`")
    await asyncio.sleep(2)
    await typew.edit("`\n(\\_/)`" "`\n(●_●)`" "`\n💖<\\  *Tapi Bo'ong`")


async def tq_cmd(client, message):
    await message.reply(
        "╔══╦╗────╔╗─╔╗╔╗\n"
        "╚╗╔╣╚╦═╦═╣╚╗║╚╝╠═╦╦╗\n"
        "─║║║║║╬║║║╩║╚╗╔╣║║║║\n"
        "─╚╝╚╩╩╩╩╩╩╩╝─╚╝╚═╩═╝\n"
    )


async def rumah_cmd(client, message):
    await message.reply(
        "╱◥◣\n"
        "│∩ │◥███◣ ╱◥███◣\n"
        "╱◥◣ ◥████◣▓∩▓│∩ ║\n"
        "│╱◥█◣║∩∩∩ ║◥█▓ ▓█◣\n"
        "││∩│ ▓ ║∩田│║▓ ▓ ▓∩ ║\n"
        "๑۩๑๑۩๑๑ ۩๑๑۩๑▓๑۩๑๑۩๑"
    )


async def syg_cmd(client, message):
    await message.edit("sayang..")
    await asyncio.sleep(3)
    await message.edit("❤️ I")
    await asyncio.sleep(0.5)
    await message.edit("❤️ I Love")
    await asyncio.sleep(0.5)
    await message.edit("❤️ I Love You")
    await asyncio.sleep(3)
    await message.edit("❤️ I Love You <3")


async def hack_cmd(client, message):
    await message.edit("hack akun aktif...")
    await asyncio.sleep(2)
    await message.edit(" User online: True\nTelegram access: True\nRead Storage: True ")
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 0%\n[░░░░░░░░░░░░░░░░░░░░]\n`Looking for Telegram...`\nETA: 0m, 20s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 11.07%\n[██░░░░░░░░░░░░░░░░░░]\n`Looking for Telegram...`\nETA: 0m, 18s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 20.63%\n[███░░░░░░░░░░░░░░░░░]\n`Found folder C:/Telegram`\nETA: 0m, 16s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 34.42%\n[█████░░░░░░░░░░░░░░░]\n`Found folder C:/Telegram`\nETA: 0m, 14s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 42.17%\n[███████░░░░░░░░░░░░░]\n`Searching for databases`\nETA: 0m, 12s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 55.30%\n[█████████░░░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 10s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 64.86%\n[███████████░░░░░░░░░]\n`Found msgstore.db.crypt12`\nETA: 0m, 08s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 74.02%\n[█████████████░░░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 06s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 86.21%\n[███████████████░░░░░]\n`Trying to Decrypt...`\nETA: 0m, 04s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 93.50%\n[█████████████████░░░]\n`Decryption successful!`\nETA: 0m, 02s"
    )
    await asyncio.sleep(2)
    await message.edit(
        "Hacking... 100%\n[████████████████████]\n`Scanning file...`\nETA: 0m, 00s"
    )
    await asyncio.sleep(2)
    await message.edit("Hacking complete!\nUploading file...")
    await asyncio.sleep(2)
    await message.edit(
        "Targeted Account Hacked...!\n\n ✅ File has been successfully uploaded to my server.\nTelegram Database:\n`./DOWNLOADS/msgstore.db.crypt12`"
    )
