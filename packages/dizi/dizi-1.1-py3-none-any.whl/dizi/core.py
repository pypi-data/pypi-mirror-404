from .constants import *
import os
from time import sleep
def gradient(start, end, string):
    r1, g1, b1 = start
    r2, g2, b2 = end
    length = max(len(string) - 1, 1)
    result = ""
    for i, char in enumerate(string):
        r = int(r1 + (r2 - r1) * i / length)
        g = int(g1 + (g2 - g1) * i / length)
        b = int(b1 + (b2 - b1) * i / length)
        result += f"\033[38;2;{r};{g};{b}m{char}"
    return result + "\033[0m"

def renderBanner(name='', version='', server='', website='', note=''):
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")

    logo = f"""{gradient((255,0,180),(255, 100, 0),"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")}\n{ORANGE}{name} {WHITE}-{ORANGE} Ver {version} \n{BLUE}auth{WHITE}: {GREEN}Dang Dizi {WHITE}| {BLUE}server{WHITE}: {GREEN}{server}\n{BLUE}website{WHITE}: {YELLOW}{website}\n{gradient((255, 100, 0),(255,0,180),"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")}\n{WHITE}note{YELLOW}: {GRAY}{note}\n"""
    print (logo)

def success(message):
    print (f"{WHITE}[{GREEN}✓{WHITE}]{GREEN} / {WHITE}[{GREEN}{message}{WHITE}]")

def warning(message):
    print (f"{WHITE}[{YELLOW}!{WHITE}]{YELLOW} / {WHITE}[{YELLOW}{message}{WHITE}]")

def error(message):
    print (f"{WHITE}[{RED}×{WHITE}]{RED} / {WHITE}[{RED}{message}{WHITE}]")

def info(message):
    print (f"{WHITE}[{BLUE}i{WHITE}]{BLUE} / {WHITE}[{BLUE}{message}{WHITE}]") 

def loadTime(time):
    tick = ["|", "/", "-", "\\"]
    num = 0
    for i in range(int(time), 0, -1):
        print (f"{WHITE}[{ORANGE}{tick[num]}{WHITE}] {ORANGE}Please wait {WHITE}/ {PINK}{i} {WHITE}/ {ORANGE}seconds!    ", end="\r", flush=True)
        sleep(1)
        num = num + 1
        if num >= len(tick):
            num = 0
    print ("                                 ", end="\r", flush=True)