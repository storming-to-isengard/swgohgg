import requests
from lxml import html

class CharacterInfo:

    def __init__(self, name, level, gear_level, star_level):

        self.name = name
        self.level = level
        self.gear_level = gear_level
        self.star_level = star_level

class PlayerInfo:

    def __init__(self, name):

        self.name = name
        self.characters = {}

    def add_character(self, character_info):

        self.characters[character_info.name] = character_info

def process_character_element(character_html_element):

    # first determine if the character is unlocked or not
    parent_element_class = character_html_element.xpath("../@class")[0]
    if "collection-char-missing" in parent_element_class:
        return None

    # character is unlocked, get the name, level, and gear level
    name = character_html_element.xpath("./a/text()")[0]
    name = name.encode('utf-8')
    level = character_html_element.xpath("..//div[@class='char-portrait-full-level']/text()")[0]
    gear_level = character_html_element.xpath("..//div[@class='char-portrait-full-gear-level']/text()")[0]
    star_level = "1"

    # the star level is a little harder to get - we have to try one by one
    # probably a better way to do this, but it's quick and dirty for now
    star_level_element = character_html_element.xpath("..//div[@class='star star7']")
    if len(star_level_element) == 0:
        star_level_element = character_html_element.xpath("..//div[@class='star star6']")
        if len(star_level_element) == 0:
            star_level_element = character_html_element.xpath("..//div[@class='star star5']")
            if len(star_level_element) == 0:
                star_level_element = character_html_element.xpath("..//div[@class='star star4']")
                if len(star_level_element) == 0:
                    star_level_element = character_html_element.xpath("..//div[@class='star star3']")
                    if len(star_level_element) == 0:
                        star_level_element = character_html_element.xpath("..//div[@class='star star2']")
                        if len(star_level_element) != 0:
                            star_level == "2"
                    else:
                        star_level = "3"
                else:
                    star_level = "4"
            else:
                star_level = "5"
        else:
            star_level = "6"
    else:
        star_level = "7"

    return CharacterInfo(name, level, gear_level, star_level)

if __name__ == '__main__':

    session = requests.session()
    
    # get the list of all characters in the game
    result = session.get("http://swgoh.gg/", headers = dict(referer = "http://swgoh.gg/"))
    tree = html.fromstring(result.content)
    character_names = tree.xpath("//li[@class='media list-group-item p-0 character']//h5/text()")
    character_factions = tree.xpath("//li[@class='media list-group-item p-0 character']//small/text()")
    character_infos = dict(zip(character_names, character_factions))

    # get the list of members who have public profiles in the guild
    result = session.get("http://swgoh.gg/g/13864/storming-to-isengard/", headers = dict(referer = "http://swgoh.gg/g/13864/storming-to-isengard/"))
    tree = html.fromstring(result.content)
    player_names = tree.xpath("//table[@class='table table-condensed table-striped']//tr//strong/text()")
    player_links = tree.xpath("//table[@class='table table-condensed table-striped']//tr//a/@href")
    players_in_guild = dict(zip(player_names, player_links))
    
    # get each player's collection state
    base_link = "http://swgoh.gg/"
    players = []
    for player_name, player_link in players_in_guild.items():
        player_collection_link = base_link + player_link + "collection/"
        result = session.get(player_collection_link, headers = dict(referer = player_collection_link))
        tree = html.fromstring(result.content)

        # create the player instance and loop over all possible characters to get the information
        # specific to this player
        player = PlayerInfo(player_name)

        character_elements = tree.xpath("//div[@class='col-xs-6 col-sm-3 col-md-3 col-lg-2']//div[@class='collection-char-name']")
        for character_element in character_elements:

            character_info = process_character_element(character_element)
            if(character_info is not None):
                
                # add the character to the player's collection
                player.add_character(character_info)

        players.append(player)

    # character information processed for each player, now write it out
    # we write out characters as rows, players as columns, and information in the intersecting cell
    f = open('character_data.csv', 'w')

    f.write("Characters,")
    for player in players:
        f.write(player.name.encode('utf-8') + ",")

    f.write("\n")

    for character in character_names:

        encoded = character.encode('utf-8')
        f.write(encoded + ",")

        for player in players:
            if encoded in player.characters.keys():
                f.write(player.characters[encoded].level + " " + player.characters[encoded].star_level + " " + player.characters[encoded].gear_level + ",")
            else:
                f.write("Locked,")

        f.write("\n")

    f.write("\n\n\n\n")

    # faction table
    f.write("Character,Factions,\n")
    for character_name, character_factions in character_infos.items():
        encoded = character_name.encode('utf-8')
        f.write(encoded + ",")

        # split the factions
        encoded_character_factions = character_factions.encode('utf-8')
        factions = encoded_character_factions.split('\xb7')
        for faction in factions:
            faction = faction.strip('\xc2')
            faction = faction.strip(' ')
            f.write(faction.encode('utf-8') + " ")
        
        f.write("\n")

    f.write("\n")

    f.close()