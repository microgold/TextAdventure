#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadow Circuit: A Night in Austin — Game Engine
Extracted and adapted from the original text adventure for web interface
"""

import json, os, textwrap, random
from collections import defaultdict

def wrap(s, width=94):
    return "\n".join(textwrap.wrap(s, width)) if s else ""

def title(s):
    return f"# {s}"

def norm(s): 
    return s.lower().strip()

DIRECTIONS = {"n":"north","s":"south","e":"east","w":"west","u":"up","d":"down"}

class State:
    def __init__(self):
        self.turn = 0
        self.max_turns = 40
        self.health = 3
        self.will = 2
        self.hunger = 1
        self.location = "L01"
        self.inv = []  # item keys
        self.seen = set(["L01"])
        # flags
        self.f = {
            "façade_unlocked": False,
            "atrium_loot_taken": False,
            "sticky_fingers": False,
            "sigil_traced": False,
            "shadowmark_seen": False,
            "token_ward": False,
            "token_feather": False,
            "token_shadow": False,
            "sockets_inserted": 0,
            "vault_open": False,
            "vale_roof_unlocked": False,
            "antenna_fixed": False,
            "antenna_tuned": False,
            "resin_sampled": False,
            "met_lupita": False,
            "met_reef": False,
            "met_tia": False,
            "tia_trust": 0,
            "empathy": 0,
            "bite_count": 0,
            "ending": None,
            "loyal_dog": False
        }

class Game:
    def __init__(self):
        self.s = State()
        self.world = self._build_world()
        self.items = self._build_items()
        self.npcs = self._build_npcs()
        self.hints = self._build_hints()
        self.output_buffer = []

    def output(self, text):
        """Add text to output buffer"""
        self.output_buffer.append(text)

    def get_output(self):
        """Get and clear output buffer"""
        result = "\n".join(self.output_buffer)
        self.output_buffer = []
        return result

    # ---------- World / Items / NPCs ----------
    def _build_world(self):
        W = {
            "L01": {"name":"RAIN ALLEY (Behind Halcyon)",
                    "desc":"Wet brick, coffee steam, flickering sign. A chalk SIGIL bars a metal service door. "
                           "A trash bin, a CAT with a bottle-cap collar, and a low CRATE. A scuffed POLICE RADIO "
                           "crackles in the rain.",
                    "exits":{"east":"L02","south":"L03_locked","up":"L12_req"},
                    "features":["CHALK_SIGIL","CAT"],
                    "items":["POLICE_RADIO","NOTE_SCRAP","CRATE"]},

            "L02": {"name":"ALLEY MOUTH (Sixth Street)",
                    "desc":"Neon roar and music thump. A POSTER for the Auric Gallery, a bent PAPERCLIP, and a TAROT "
                           "COIN wedged in a curb crack."
                           "A STORM DRAIN whispers under water. A NEWSSTAND creaks.",
                    "exits":{"west":"L01","east":"L04","south":"L05"},
                    "features":["STORM_DRAIN","NEWSSTAND","CROW_STENCIL"],
                    "items":["POSTER","PAPERCLIP","TAROT_COIN"]},

            "L03": {"name":"HALCYON CAFE - BACK ROOM",
                    "desc":"Roaster hum; key rack; a STAFF LOCKER with badge reader; the scent of burnt sugar. "
                           "A warm MUG of espresso steams on a tray.",
                    "exits":{"north":"L01","east":"L04"},
                    "features":["STAFF_LOCKER"],
                    "items":["KEY_TAG","MUG"],
                    "locked":True},

            "L04": {"name":"SIXTH STREET STRIP",
                    "desc":"Buskers, drizzle, neon. A FOOD TRUCK 'Sunrise Tacos'. Napkin dispenser with a STRAW. "
                           "Truck bell you could ring. A NEWSPAPER sits in a dispenser. The NEWSSTAND has a gap behind it.",
                    "exits":{"west":"L02","north":"L03","south":"L06"},
                    "features":["TRUCK_BELL","NEWSSTAND"],
                    "items":["NEWSPAPER","STRAW"],
                    "npcs":["LUPITA"]},

            "L05": {"name":"AURIC GALLERY FAÇADE",
                    "desc":"Sleek stone under rain. A KEYPAD guards the glass door. In a sculpture niche, a BRASS LOCKET "
                           "is bound in gluey RESIN THREADS. A SECURITY CAMERA blinks.",
                    "exits":{"north":"L02","inside":"L07_locked"},
                    "features":["KEYPAD","SECURITY_CAMERA"],
                    "items":["BRASS_LOCKET","RESIN_THREADS"]},

            "L06": {"name":"LADY BIRD LAKE UNDERBRIDGE",
                    "desc":"Bats fidget above. River breath. A WARD-SIGIL etched beneath a bench. A HOMELESS MUSICIAN "
                           "strums a weary chord. An EMPTY JAR sits near a pillar, with STRING tangled around it.",
                    "exits":{"north":"L04","east":"L08"},
                    "features":["WARD_SIGIL_BENCH"],
                    "items":["EMPTY_JAR","STRING","HEMATITE"],
                    "npcs":["REEF"]},

            "L07": {"name":"AURIC GALLERY - ATRIUM",
                    "desc":"Moonlit glass, shattered displays. A dark RESIN PUDDLE glistens near a heavy VAULT DOOR "
                           "with three empty sigil sockets. East to archives, down to storage.",
                    "exits":{"out":"L05","east":"L09","down":"L10"},
                    "features":["VAULT_DOOR"],
                    "items":["SILVER_NAILS","AUDIO_GUIDE","GALLERY_MAP","RESIN_PUDDLE"]},

            "L08": {"name":"BOTANICA LA ESTRELLA",
                    "desc":"Shelves of herbs and crystals. Incense curls. TIA SOL watches, stern but kind. "
                           "A SIGIL MANUAL sits behind glass. Bowls of GARLIC and ROSEMARY rest by the till. "
                           "A spool of SILVERED THREAD shines faintly.",
                    "exits":{"west":"L06","east":"L11"},
                    "items":["GARLIC","ROSEMARY","SILVERED_THREAD","SIGIL_MANUAL"],
                    "npcs":["TIA_SOL"]},

            "L09": {"name":"GALLERY ARCHIVES",
                    "desc":"Blueprint drawers and a locked glass CASE. A lens array glints behind it. "
                           "A MAGNETIC STRIP reader sits beside the seam.",
                    "exits":{"west":"L07"},
                    "features":["CASE_LOCK"],
                    "items":["BLUEPRINT","LENS_ARRAY_CASE","MAGNET_CARD_hidden"]},

            "L10": {"name":"GALLERY STORAGE",
                    "desc":"Crates and a solvent cabinet. A pair of GLOVES dangle from a hook; a RAG is draped over a box. "
                           "Behind crates, a SHADOWMARK twists in chalk.",
                    "exits":{"up":"L07","hatch":"L11"},
                    "features":["SHADOWMARK"],
                    "items":["SOLVENT","GLOVES","RAG"]},

            "L11": {"name":"SERVICE ALLEY (Behind Botanica/Gallery)",
                    "desc":"Dumpsters, a chained GATE, and a stray DOG with a tag: Gasket. He wags hopefully. "
                           "A BONE lies near a pallet; under it a WIRE CUTTER.",
                    "exits":{"west":"L08","hatch":"L10","south":"L12"},
                    "features":["CHAIN_GATE"],
                    "items":["BONE","WIRE_CUTTER"],
                    "npcs":["GASKET"]},

            "L12": {"name":"FIRE ESCAPE & ROOFTOPS",
                    "desc":"Wind and city glow. An ANTENNA PANEL hums with ward resonance. A loose BOLT rattles. "
                           "South leads along hooked rooflines toward VALE TOWER, but the way is sealed by wards.",
                    "exits":{"down":"L01","south":"VALE_ROOF_locked"},
                    "features":["WARD_ANTENNA"],
                    "items":["ANTENNA_PANEL","BOLT"]},

            "VALE_ROOF": {"name":"VALE TOWER ROOF",
                    "desc":"High above the city, the NECROFRAME hums—resin and mirrored glass. Wards burn in the stone. "
                           "Ezra Vale stands within, a storm held in human shape.",
                    "exits":{"down":"L12"},
                    "items":["NECROFRAME"],
                    "npcs":["EZRA_VALE"]},
        }
        return W

    def _build_items(self):
        I = {
            # L01
            "POLICE_RADIO":{"name":"police radio","loc":"L01","portable":True,
                            "desc":"A battered radio. Chatter: 'Unit 12-07… disturbance at Auric.'" },
            "NOTE_SCRAP":{"name":"note scrap","loc":"L01","portable":True,
                          "desc":"Wet strokes showing a counter-pattern for chalk sigils."},
            "CRATE":{"name":"crate","loc":"L01","portable":False,
                     "desc":"A sturdy crate. Could be pushed under the fire escape."},
            # L02
            "POSTER":{"name":"poster","loc":"L02","portable":False,
                      "desc":"Auric Gallery Retrospective—Entry with code only. Security by Unit 12-07."},
            "PAPERCLIP":{"name":"paperclip","loc":"L02","portable":True,
                         "desc":"A bent paperclip for shimming or prying."},
            "TAROT_COIN":{"name":"tarot coin","loc":"L02","portable":True,
                           "desc":"Etched with the Wheel of Fortune. Hums faintly."},
            # L03
            "KEY_TAG":{"name":"key-tag","loc":"L03","portable":True,
                       "desc":"A plastic staff fob for the locker."},
            "MUG":{"name":"mug","loc":"L03","portable":True,
                   "desc":"A hot mug of espresso. Steam rises."},
            "WARD_CHALK":{"name":"ward-chalk","loc":"L03_locked","portable":True,
                          "desc":"Pale chalk infused with herbs; good for sigils."},
            # L04
            "NEWSPAPER":{"name":"newspaper","loc":"L04","portable":True,
                         "desc":"Rain-smudged pages—but good paper for a rubbing."},
            "STRAW":{"name":"straw","loc":"L04","portable":True,
                     "desc":"A plastic straw from the food truck napkin dispenser."},
            # L05
            "BRASS_LOCKET":{"name":"brass locket","loc":"L05","portable":True,
                            "desc":"An ornate locket bound by pulsing resin threads.","stuck":True,"open":False},
            "RESIN_THREADS":{"name":"resin threads","loc":"L05","portable":False,
                             "desc":"Gluey, alive. They resist tearing; heat/solvent helps."},
            # L06
            "EMPTY_JAR":{"name":"empty jar","loc":"L06","portable":True,
                         "desc":"A small jar with lid—good for samples."},
            "STRING":{"name":"string","loc":"L06","portable":True,
                      "desc":"Useful for tying or fishing things from gaps."},
            "HEMATITE":{"name":"hematite stone","loc":"L06","portable":True,
                        "desc":"Smooth, grounding. Good in sigils."},
            # L07
            "SILVER_NAILS":{"name":"silver nails (x3)","loc":"L07","portable":True,"count":3,
                            "desc":"Three cold nails—channel ward circuits."},
            "AUDIO_GUIDE":{"name":"audio guide","loc":"L07","portable":True,
                            "desc":"Tinny: 'Welcome to the Vale Retrospective—' then static."},
            "GALLERY_MAP":{"name":"gallery map","loc":"L07","portable":True,
                           "desc":"Tri-fold map: Atrium, Archives east, Storage down, Roof path."},
            "RESIN_PUDDLE":{"name":"resin puddle","loc":"L07","portable":False,
                            "desc":"Dark amber resin, faintly warm—alive."},
            # L08
            "GARLIC":{"name":"garlic","loc":"L08","portable":True,
                      "desc":"Pungent cloves—ward essence."},
            "ROSEMARY":{"name":"rosemary","loc":"L08","portable":True,
                        "desc":"Sharp herb—clarity and protection."},
            "SILVERED_THREAD":{"name":"silvered thread","loc":"L08","portable":True,
                               "desc":"Gleaming thread—channels focus."},
            "SIGIL_MANUAL":{"name":"sigil manual","loc":"L08","portable":True,
                            "desc":"'Patterns of Power'—ward theory and practice."},
            # L09
            "BLUEPRINT":{"name":"blueprint","loc":"L09","portable":True,
                         "desc":"Gallery vault schematics—ward circuits and sigil points."},
            "LENS_ARRAY_CASE":{"name":"lens array","loc":"L09","portable":True,
                               "desc":"Precision optics in a padded case."},
            "MAGNET_CARD_hidden":{"name":"magnetic card","loc":"L09","portable":True,
                                  "desc":"A security card hidden behind the case.","hidden":True},
            # L10
            "SOLVENT":{"name":"solvent","loc":"L10","portable":True,
                       "desc":"Chemical solvent—dissolves resin bindings."},
            "GLOVES":{"name":"gloves","loc":"L10","portable":True,
                      "desc":"Thick work gloves—protection from burns."},
            "RAG":{"name":"rag","loc":"L10","portable":True,
                   "desc":"Oil-stained cloth—good for cleaning or wrapping."},
            # L11
            "BONE":{"name":"bone","loc":"L11","portable":True,
                    "desc":"A chew toy bone—the dog eyes it hopefully."},
            "WIRE_CUTTER":{"name":"wire cutter","loc":"L11","portable":True,
                           "desc":"Sharp cutters—slice through metal."},
            # L12
            "ANTENNA_PANEL":{"name":"antenna panel","loc":"L12","portable":False,
                             "desc":"Ward resonance array—missing components."},
            "BOLT":{"name":"bolt","loc":"L12","portable":True,
                    "desc":"A loose antenna bolt—could secure connections."},
            # VALE_ROOF
            "NECROFRAME":{"name":"necroframe","loc":"VALE_ROOF","portable":False,
                          "desc":"The heart of Vale's power—pulsing with dark energy."},
            # Dynamic items
            "FISHING_GEAR":{"name":"fishing gear","loc":"inv","portable":True,
                            "desc":"String and coin—ready for fishing.","combined":True},
            "COUNTER_INK":{"name":"counter-ink","loc":"inv","portable":True,
                           "desc":"Herb-infused ink—breaks sigil bindings.","crafted":True},
            "SIGIL_TOKEN_WARD":{"name":"ward token","loc":"inv","portable":True,
                                "desc":"A ward sigil token—glows faintly."},
            "SIGIL_TOKEN_FEATHER":{"name":"feather token","loc":"inv","portable":True,
                                   "desc":"A feather sigil token—light as air."},
            "SIGIL_TOKEN_SHADOW":{"name":"shadow token","loc":"inv","portable":True,
                                  "desc":"A shadow sigil token—writhes with darkness."},
        }
        return I

    def _build_npcs(self):
        N = {
            "LUPITA": {"name":"Lupita","loc":"L04","trust":0,"spoken":False,
                       "desc":"Food truck owner, tired but alert. Steam rises from her grill.",
                       "topics":{"default":"'Austin's been strange lately—more than usual.'",
                                "vale":"'That gallery owner? Creepy type. Heard he collects... things.'",
                                "gallery":"'Fancy place. Rich folks only. Code entry, very exclusive.'",
                                "sigils":"'My abuela drew those—protection marks. Old ways.'"}},

            "REEF": {"name":"Reef","loc":"L06","trust":0,"spoken":False,
                     "desc":"Homeless musician with knowing eyes. His guitar case holds more than coins.",
                     "topics":{"default":"'The city's got teeth tonight, friend.'",
                              "vale":"'He feeds on more than blood—feeds on connection itself.'",
                              "gallery":"'That place ain't right. Wards are backwards, inside-out.'",
                              "music":"'Music opens doors—and sometimes you don't want 'em opened.'"}},

            "TIA_SOL": {"name":"Tia Sol","loc":"L08","trust":0,"spoken":False,
                        "desc":"Botanica keeper, stern but protective. Sees more than she says.",
                        "topics":{"default":"'You seek protection, or power? Both have their price.'",
                                 "vale":"'A man who forgot he was human. Now he seeks to forget humanity itself.'",
                                 "sigils":"'Ancient patterns. They channel intent—but intent can corrupt.'",
                                 "herbs":"'Garlic for wards, rosemary for clarity. Old wisdom in new times.'"}},

            "GASKET": {"name":"Gasket","loc":"L11","trust":0,"spoken":False,
                       "desc":"A loyal stray dog with soulful eyes. His tag reads 'Gasket'.",
                       "topics":{"default":"*whine* *wag*",
                                "bone":"*excited yip*",
                                "thread":"*sniff* *curious tilt*"}},

            "EZRA_VALE": {"name":"Ezra Vale","loc":"VALE_ROOF","trust":0,"spoken":False,
                          "desc":"The necromancer himself—power made manifest in human form.",
                          "topics":{"default":"'Detective Cross. You've come far to witness your city's evolution.'",
                                   "gallery":"'My collection—each piece a node in the greater network.'",
                                   "power":"'Connection without corruption, community without individual will.'",
                                   "choice":"'Join willingly, or join regardless. The outcome is inevitable.'"}}
        }
        return N

    def _build_hints(self):
        return {
            "general": [
                "Examine everything—items reveal their uses.",
                "Talk to NPCs about VALE, GALLERY, SIGILS.",
                "Combine items: STRING + TAROT_COIN = fishing gear.",
                "Use SOLVENT on resin to free trapped items.",
                "Ward sigils counter necromantic bindings."
            ],
            "gallery": [
                "The keypad code is hidden in the poster.",
                "Three tokens open the vault: ward, feather, shadow.",
                "Use the lens array to trace sigil patterns.",
                "The staff locker needs the magnetic card."
            ],
            "npcs": [
                "Lupita knows local lore and gallery access.",
                "Reef understands the ward patterns.",
                "Tia Sol can teach sigil theory.",
                "Gasket responds to kindness and treats."
            ],
            "items": [
                "Hot liquids dissolve resin bindings.",
                "Silver conducts ward energy.",
                "Chalk sigils require counter-patterns to break.",
                "The fishing gear reaches distant objects."
            ]
        }

    # ---------- Core Game Logic ----------
    
    def current_room(self):
        return self.world.get(self.s.location, {})

    def room_items(self):
        """Items currently in the room"""
        return [k for k,v in self.items.items() 
                if v.get("loc") == self.s.location and not v.get("hidden", False)]

    def room_npcs(self):
        """NPCs currently in the room"""
        return [k for k,v in self.npcs.items() if v.get("loc") == self.s.location]

    def advance_turn(self):
        """Advance game turn and check time limit"""
        self.s.turn += 1
        if self.s.turn >= self.s.max_turns:
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("DAWN BREAKS over Austin's skyline. The first rays pierce the gloom,")
            self.output("and you feel your vampiric strength ebb. EZRA VALE has escaped")
            self.output("into the light, his necromantic web still intact.")
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("**ENDING: DAWN'S DEFEAT** - Time ran out. Vale wins.")
            self.s.f["ending"] = "defeat"
            return True
        return False

    def look_around(self):
        """Generate room description"""
        room = self.current_room()
        if not room:
            return "You are nowhere. This shouldn't happen."
        
        output = []
        output.append(f"**{room['name']}**")
        output.append(room['desc'])
        
        # Items in room
        items = self.room_items()
        if items:
            item_names = [self.items[i]['name'] for i in items]
            output.append(f"You see: {', '.join(item_names)}")
        
        # NPCs in room
        npcs = self.room_npcs()
        if npcs:
            npc_names = [self.npcs[n]['name'] for n in npcs]
            output.append(f"Present: {', '.join(npc_names)}")
        
        # Exits
        exits = room.get('exits', {})
        if exits:
            exit_list = []
            for direction, dest in exits.items():
                if dest.endswith('_locked'):
                    exit_list.append(f"{direction} (locked)")
                elif dest.endswith('_req'):
                    exit_list.append(f"{direction} (requires climbing)")
                else:
                    exit_list.append(direction)
            output.append(f"Exits: {', '.join(exit_list)}")
        
        return "\n".join(output)

    def get_inventory_display(self):
        """Get formatted inventory display"""
        if not self.s.inv:
            return "You carry nothing."
        
        inv_items = [self.items[i]['name'] for i in self.s.inv if i in self.items]
        return f"Inventory: {', '.join(inv_items)}"

    def get_stats_display(self):
        """Get formatted stats display"""
        return f"Turn {self.s.turn}/{self.s.max_turns} | Health: {self.s.health} | Will: {self.s.will} | Hunger: {self.s.hunger}"

    def process_command(self, command):
        """Process a game command and return response"""
        if not command:
            return "Say again?"
        
        # Clear previous output
        self.output_buffer = []
        
        # Validate inventory consistency before processing command
        self.validate_inventory_consistency()
        
        cmd = norm(command)
        words = cmd.split()
        verb = words[0] if words else ""
        
        # Handle different command types
        if verb in ["look", "l"]:
            self.output(self.look_around())
        elif verb in ["inventory", "i"]:
            self.output(self.get_inventory_display())
        elif verb == "stats":
            self.output(self.get_stats_display())
        elif verb in ["examine", "x"]:
            if len(words) > 1:
                self.cmd_examine(" ".join(words[1:]))
            else:
                self.output("Examine what?")
        elif verb in ["take", "get"]:
            if len(words) > 1:
                self.cmd_take(" ".join(words[1:]))
            else:
                self.output("Take what?")
        elif verb == "drop":
            if len(words) > 1:
                self.cmd_drop(" ".join(words[1:]))
            else:
                self.output("Drop what?")
        elif verb in ["go", "move"] or verb in DIRECTIONS or verb in DIRECTIONS.values():
            if verb in ["go", "move"] and len(words) > 1:
                self.cmd_go(words[1])
            elif verb in DIRECTIONS:
                self.cmd_go(DIRECTIONS[verb])
            elif verb in DIRECTIONS.values():
                self.cmd_go(verb)
            else:
                self.output("Go where?")
        elif verb in ["n", "s", "e", "w", "u", "d"]:
            self.cmd_go(DIRECTIONS.get(verb, verb))
        elif verb in ["inside", "enter"]:
            self.cmd_go("inside")
        elif verb in ["outside", "out"]:
            self.cmd_go("out")
        elif verb == "use":
            if len(words) > 1:
                self.cmd_use(" ".join(words[1:]))
            else:
                self.output("Use what?")
        elif verb == "combine":
            if len(words) > 3 and words[2] == "with":
                self.cmd_combine(words[1], " ".join(words[3:]))
            else:
                self.output("Combine what with what?")
        elif verb in ["talk", "ask"]:
            if len(words) > 1:
                self.cmd_talk(" ".join(words[1:]))
            else:
                self.output("Talk to whom?")
        elif verb == "read":
            if len(words) > 1:
                self.cmd_read(" ".join(words[1:]))
            else:
                self.output("Read what?")
        elif verb in ["open", "close"]:
            if len(words) > 1:
                self.cmd_open_close(verb, " ".join(words[1:]))
            else:
                self.output(f"{verb.title()} what?")
        elif verb in ["listen", "smell"]:
            self.cmd_sense(verb)
        elif verb in ["wait", "z"]:
            self.output("Time passes...")
        elif verb == "push":
            if len(words) > 1:
                self.cmd_push(" ".join(words[1:]))
            else:
                self.output("Push what?")
            self.advance_turn()
        elif verb == "sense":
            self.cmd_vampire_sense()
        elif verb == "mesmerize":
            if len(words) > 1:
                self.cmd_mesmerize(" ".join(words[1:]))
            else:
                self.output("Mesmerize whom?")
        elif verb == "bite":
            if len(words) > 1:
                self.cmd_bite(" ".join(words[1:]))
            else:
                self.output("Bite what?")
        elif cmd.startswith("enter code"):
            code = cmd.replace("enter code", "").strip()
            self.cmd_enter_code(code)
        elif cmd == "trace sigil":
            self.cmd_trace_sigil()
        elif cmd == "craft counter-ink":
            self.cmd_craft_counter_ink()
        elif cmd == "tune antenna":
            self.cmd_tune_antenna()
        elif verb == "map":
            self.cmd_map()
        elif verb == "help":
            self.cmd_help()
        elif verb == "hint":
            self.cmd_hint()
        elif verb == "save":
            self.cmd_save()
        elif verb == "load":
            self.cmd_load()
        elif verb == "quit":
            self.output("Thanks for playing Shadow Circuit!")
            return "QUIT"
        else:
            self.output("I don't understand that command.")
        
        # Check if game should end
        if self.advance_turn():
            return "GAME_OVER"
        
        # Check for ending conditions
        if self.s.f["ending"]:
            return "GAME_OVER"
        
        return self.get_output()

    # ---------- Command Implementations ----------
    
    def cmd_examine(self, target):
        """Examine items, features, or NPCs"""
        target = norm(target)
        
        # Check inventory first
        for item_key in self.s.inv:
            if item_key in self.items and target in norm(self.items[item_key]['name']):
                self.output(self.items[item_key]['desc'])
                return
        
        # Check room items
        for item_key in self.room_items():
            if target in norm(self.items[item_key]['name']):
                self.output(self.items[item_key]['desc'])
                # Reveal hidden items
                if item_key == "LENS_ARRAY_CASE" and not self.s.f.get("magnet_card_revealed", False):
                    self.output("Behind the case, you spot a magnetic card!")
                    self.items["MAGNET_CARD_hidden"]["hidden"] = False
                    self.s.f["magnet_card_revealed"] = True
                return
        
        # Check NPCs
        for npc_key in self.room_npcs():
            if target in norm(self.npcs[npc_key]['name']):
                self.output(self.npcs[npc_key]['desc'])
                return
        
        # Check room features
        room = self.current_room()
        features = room.get('features', [])
        for feature in features:
            if target in norm(feature.replace('_', ' ')):
                self.examine_feature(feature)
                return
        
        self.output(f"You don't see '{target}' here.")

    def examine_feature(self, feature):
        """Examine room features"""
        if feature == "CHALK_SIGIL":
            self.output("A ward sigil drawn in pale chalk. It pulses faintly, barring the door.")
        elif feature == "CAT":
            self.output("A scrappy tabby with a bottle-cap collar. It watches you with knowing eyes.")
        elif feature == "STORM_DRAIN":
            self.output("Dark water rushes below. You might fish something out with the right tools.")
        elif feature == "KEYPAD":
            self.output("A numerical keypad with four buttons. Requires a code.")
        elif feature == "VAULT_DOOR":
            inserted = self.s.f.get("sockets_inserted", 0)
            self.output(f"A massive door with three sigil sockets. {inserted}/3 tokens inserted.")
        elif feature == "WARD_SIGIL_BENCH":
            if not self.s.f.get("token_ward", False):
                self.output("A protective ward carved deep in stone. It resonates with power.")
            else:
                self.output("The carved ward is now dormant, its power transferred.")
        elif feature == "SHADOWMARK":
            if not self.s.f.get("shadowmark_seen", False):
                self.output("Dark chalk spirals that hurt to look at directly. A shadow sigil.")
                self.s.f["shadowmark_seen"] = True
            else:
                self.output("The shadow sigil mark twists in the darkness.")
        else:
            self.output(f"You examine the {feature.replace('_', ' ').lower()}.")

    def cmd_take(self, target):
        """Take items from the room"""
        target = norm(target)
        
        # Check if item is already in inventory
        for item_key in self.s.inv:
            if item_key in self.items and target in norm(self.items[item_key]['name']):
                self.output(f"You already have the {self.items[item_key]['name']}.")
                return
        
        for item_key in self.room_items():
            if target in norm(self.items[item_key]['name']):
                item = self.items[item_key]
                if not item.get('portable', True):
                    self.output(f"You can't take the {item['name']}.")
                    return
                if item.get('stuck', False):
                    self.output(f"The {item['name']} is stuck fast.")
                    return
                
                self.s.inv.append(item_key)
                item['loc'] = 'inv'
                self.output(f"Taken: {item['name']}")
                return
        
        # General recovery system for lost items
        if self.recover_lost_item(target):
            return
        
        self.output(f"You don't see '{target}' here to take.")

    def cmd_drop(self, target):
        """Drop items from inventory"""
        target = norm(target)
        
        for item_key in self.s.inv:
            if item_key in self.items and target in norm(self.items[item_key]['name']):
                self.s.inv.remove(item_key)
                self.items[item_key]['loc'] = self.s.location
                self.output(f"Dropped: {self.items[item_key]['name']}")
                return
        
        self.output(f"You don't have '{target}' to drop.")

    def cmd_go(self, direction):
        """Move between locations"""
        room = self.current_room()
        exits = room.get('exits', {})
        
        if direction not in exits:
            self.output(f"You can't go {direction} from here.")
            return
        
        destination = exits[direction]
        
        # Handle locked exits
        if destination.endswith('_locked'):
            actual_dest = destination[:-7]  # Remove '_locked'
            if actual_dest == "L03" and not self.s.f.get("façade_unlocked", False):
                self.output("The door is locked. You need to find another way in.")
                return
            elif actual_dest == "L07" and not self.s.f.get("façade_unlocked", False):
                self.output("The gallery entrance requires a security code.")
                return
            elif actual_dest == "VALE_ROOF" and not self.s.f.get("vale_roof_unlocked", False):
                self.output("Powerful wards block the path to Vale Tower.")
                return
        
        # Handle special requirements
        if destination.endswith('_req'):
            actual_dest = destination[:-4]  # Remove '_req'
            if actual_dest == "L12":
                if not self.s.f.get("crate_positioned", False):
                    self.output("The fire escape is too high. You need something to climb on.")
                    return
                else:
                    self.output("You climb up the positioned crate to the fire escape.")
        
        # Move to destination
        if destination.endswith(('_locked', '_req')):
            destination = destination.split('_')[0]
        
        if destination in self.world:
            self.s.location = destination
            self.s.seen.add(destination)
            self.output(self.look_around())
        else:
            self.output("You can't go there.")

    def cmd_use(self, args):
        """Use items alone or with targets"""
        parts = args.split(' on ')
        if len(parts) == 1:
            parts = args.split(' with ')
        
        item = norm(parts[0])
        target = norm(parts[1]) if len(parts) > 1 else None
        
        # Find the item in inventory
        item_key = None
        for key in self.s.inv:
            if key in self.items and item in norm(self.items[key]['name']):
                item_key = key
                break
        
        if not item_key:
            self.output(f"You don't have '{item}'.")
            return
        
        # Handle item usage
        if item_key == "SOLVENT" and target:
            self.use_solvent(target)
        elif item_key == "MUG" and target and "resin" in target:
            self.use_hot_mug(target)
        elif item_key == "FISHING_GEAR" and target and "drain" in target:
            self.use_fishing_gear()
        elif item_key == "SILVERED_THREAD" and target and "gasket" in target:
            self.use_thread_with_dog()
        elif item_key == "WIRE_CUTTER" and target and ("chain" in target or "gate" in target):
            self.use_wire_cutter()
        elif item_key == "COUNTER_INK" and target and "sigil" in target:
            self.use_counter_ink()
        elif item_key == "BOLT" and target and "antenna" in target:
            self.use_bolt_on_antenna()
        elif item_key == "POLICE_RADIO" and self.s.location == "L12":
            self.use_radio_antenna()
        elif self.s.location == "VALE_ROOF":
            self.handle_final_confrontation(item_key, target)
        else:
            self.output(f"You can't use the {self.items[item_key]['name']} that way.")

    def use_solvent(self, target):
        """Use solvent on resin"""
        if "resin" in target and self.s.location == "L05":
            if "BRASS_LOCKET" in self.room_items() and self.items["BRASS_LOCKET"].get("stuck", False):
                self.output("The solvent dissolves the resin threads. The locket comes free!")
                self.items["BRASS_LOCKET"]["stuck"] = False
            else:
                self.output("The resin bubbles and dissolves.")
        else:
            self.output("There's no resin here to dissolve.")

    def use_hot_mug(self, target):
        """Use hot mug on resin"""
        if "resin" in target and self.s.location == "L05":
            if "BRASS_LOCKET" in self.room_items() and self.items["BRASS_LOCKET"].get("stuck", False):
                self.output("The hot liquid melts the resin. The locket breaks free!")
                self.items["BRASS_LOCKET"]["stuck"] = False
                # Remove the mug
                self.s.inv.remove("MUG")
                self.output("The mug is now empty and cold.")
            else:
                self.output("The heat softens the resin.")
        else:
            self.output("There's no resin here to heat.")

    def use_fishing_gear(self):
        """Use fishing gear in storm drain"""
        if self.s.location == "L02" and "STORM_DRAIN" in self.current_room().get('features', []):
            self.output("You lower the makeshift fishing line into the drain...")
            self.output("Something glints! You pull up a WARD CHALK stick!")
            self.s.inv.append("WARD_CHALK")
            self.items["WARD_CHALK"]["loc"] = "inv"
        else:
            self.output("There's nowhere to fish here.")

    def use_thread_with_dog(self):
        """Use silvered thread with Gasket"""
        if "GASKET" in self.room_npcs():
            self.output("You tie the silvered thread around Gasket's collar.")
            self.output("He barks happily and bounds toward the shadows!")
            self.output("The thread glows as he returns with a SHADOW TOKEN in his mouth!")
            self.s.inv.append("SIGIL_TOKEN_SHADOW")
            self.items["SIGIL_TOKEN_SHADOW"]["loc"] = "inv"
            self.s.f["token_shadow"] = True
            self.s.f["loyal_dog"] = True
            self.s.inv.remove("SILVERED_THREAD")
        else:
            self.output("Gasket isn't here.")

    def use_wire_cutter(self):
        """Use wire cutter on chain gate"""
        if self.s.location == "L11" and "CHAIN_GATE" in self.current_room().get('features', []):
            self.output("You cut through the chain links. The gate swings open!")
            self.output("Beyond lies a passage to the roof network.")
            # Unlock Vale Tower path
            self.world["L12"]["exits"]["south"] = "VALE_ROOF"
            self.s.f["vale_roof_unlocked"] = True
        else:
            self.output("There's nothing here to cut.")

    def use_counter_ink(self):
        """Use counter-ink on chalk sigil"""
        if self.s.location == "L01" and "CHALK_SIGIL" in self.current_room().get('features', []):
            self.output("You trace the counter-pattern over the chalk sigil.")
            self.output("The barrier dissolves! The service door unlocks.")
            self.world["L01"]["exits"]["south"] = "L03"
            self.s.f["façade_unlocked"] = True
            self.s.inv.remove("COUNTER_INK")
        else:
            self.output("There's no sigil here to counter.")

    def use_bolt_on_antenna(self):
        """Use bolt to fix antenna panel"""
        if self.s.location == "L12":
            if self.s.f.get("antenna_fixed", False):
                self.output("The antenna panel is already secured.")
                return
            self.output("You twist the bolt into place. The panel sits firm, hum sharpening to a stable chord.")
            self.s.f["antenna_fixed"] = True
            self.s.inv.remove("BOLT")
        else:
            self.output("There's no antenna panel here to fix.")

    def use_radio_antenna(self):
        """Use police radio with antenna"""
        if not self.s.f.get("antenna_fixed", False):
            self.output("The radio hisses; the panel rattles too much to hold a clear frequency. Maybe secure it first?")
        else:
            self.output("You sweep channels until the hum locks—remember the cadence. TUNE ANTENNA could seal it.")

    def cmd_tune_antenna(self):
        """Tune the antenna to unlock Vale roof"""
        if self.s.location != "L12":
            self.output("No antenna to tune here.")
            return
        if not self.s.f.get("antenna_fixed", False):
            self.output("The panel rattles too loose to hold a frequency. Secure it first.")
            return
        if self.s.f.get("antenna_tuned", False):
            self.output("The antenna is already tuned.")
            return
        
        self.output("You nudge the three tones until they lock—like teeth of a key finding its ward. The path south slackens.")
        self.s.f["antenna_tuned"] = True
        self.s.f["vale_roof_unlocked"] = True
        self.world["L12"]["exits"]["south"] = "VALE_ROOF"

    def recover_lost_item(self, target):
        """General recovery system for lost items"""
        # Map of item names to their original locations and keys
        recovery_map = {
            "bolt": ("L12", "BOLT"),
            "radio": ("L01", "POLICE_RADIO"),
            "police radio": ("L01", "POLICE_RADIO"),
            "note": ("L01", "NOTE_SCRAP"),
            "scrap": ("L01", "NOTE_SCRAP"),
            "paperclip": ("L02", "PAPERCLIP"),
            "coin": ("L02", "TAROT_COIN"),
            "tarot coin": ("L02", "TAROT_COIN"),
            "key": ("L03", "KEY_TAG"),
            "key-tag": ("L03", "KEY_TAG"),
            "mug": ("L03", "MUG"),
            "newspaper": ("L04", "NEWSPAPER"),
            "straw": ("L04", "STRAW"),
            "locket": ("L05", "BRASS_LOCKET"),
            "brass locket": ("L05", "BRASS_LOCKET"),
            "jar": ("L06", "EMPTY_JAR"),
            "empty jar": ("L06", "EMPTY_JAR"),
            "string": ("L06", "STRING"),
            "hematite": ("L06", "HEMATITE"),
            "nails": ("L07", "SILVER_NAILS"),
            "silver nails": ("L07", "SILVER_NAILS"),
            "guide": ("L07", "AUDIO_GUIDE"),
            "audio guide": ("L07", "AUDIO_GUIDE"),
            "map": ("L07", "GALLERY_MAP"),
            "gallery map": ("L07", "GALLERY_MAP"),
            "garlic": ("L08", "GARLIC"),
            "rosemary": ("L08", "ROSEMARY"),
            "thread": ("L08", "SILVERED_THREAD"),
            "silvered thread": ("L08", "SILVERED_THREAD"),
            "manual": ("L08", "SIGIL_MANUAL"),
            "sigil manual": ("L08", "SIGIL_MANUAL"),
            "blueprint": ("L09", "BLUEPRINT"),
            "lens": ("L09", "LENS_ARRAY_CASE"),
            "lens array": ("L09", "LENS_ARRAY_CASE"),
            "card": ("L09", "MAGNET_CARD_hidden"),
            "magnetic card": ("L09", "MAGNET_CARD_hidden"),
            "solvent": ("L10", "SOLVENT"),
            "gloves": ("L10", "GLOVES"),
            "rag": ("L10", "RAG"),
            "bone": ("L11", "BONE"),
            "cutter": ("L11", "WIRE_CUTTER"),
            "wire cutter": ("L11", "WIRE_CUTTER"),
        }
        
        if target in recovery_map:
            original_loc, item_key = recovery_map[target]
            
            # Check if item exists and is lost
            if item_key in self.items and item_key not in self.s.inv:
                # If we're in the right location or item is completely lost
                if self.s.location == original_loc or item_key not in self.room_items():
                    self.items[item_key]["loc"] = "inv"
                    self.s.inv.append(item_key)
                    self.output(f"Taken: {self.items[item_key]['name']} (recovered)")
                    return True
        
        return False

    def validate_inventory_consistency(self):
        """Ensure inventory and item locations are consistent"""
        # Fix any items that claim to be in inventory but aren't tracked
        for item_key, item_data in self.items.items():
            if item_data.get("loc") == "inv" and item_key not in self.s.inv:
                # Item says it's in inventory but isn't tracked - add it
                self.s.inv.append(item_key)
            elif item_data.get("loc") != "inv" and item_key in self.s.inv:
                # Item is tracked in inventory but location is wrong - fix location
                item_data["loc"] = "inv"

    def cmd_combine(self, item1, item2):
        """Combine items to create new ones"""
        item1, item2 = norm(item1), norm(item2)
        
        # Find items in inventory
        keys = []
        for key in self.s.inv:
            if key in self.items:
                name = norm(self.items[key]['name'])
                if item1 in name or item2 in name:
                    keys.append(key)
        
        if len(keys) < 2:
            self.output("You don't have both items to combine.")
            return
        
        # Check for valid combinations
        if "STRING" in keys and "TAROT_COIN" in keys:
            self.output("You tie the string to the tarot coin, creating fishing gear!")
            self.s.inv.remove("STRING")
            self.s.inv.remove("TAROT_COIN")
            self.s.inv.append("FISHING_GEAR")
            self.items["FISHING_GEAR"]["loc"] = "inv"
        else:
            self.output("You can't combine those items.")

    def cmd_talk(self, target):
        """Talk to NPCs"""
        target = norm(target)
        
        # Extract topic if present
        topic = "default"
        if " about " in target:
            parts = target.split(" about ", 1)
            target = parts[0].strip()
            topic = parts[1].strip()
        
        # Find NPC
        for npc_key in self.room_npcs():
            if target in norm(self.npcs[npc_key]['name']):
                npc = self.npcs[npc_key]
                
                # Mark as spoken to
                if not npc['spoken']:
                    npc['spoken'] = True
                    self.s.f[f"met_{npc_key.lower()}"] = True
                
                # Get response
                topics = npc.get('topics', {})
                response = topics.get(topic, topics.get('default', "They don't respond."))
                
                self.output(f"{npc['name']}: {response}")
                
                # Special NPC interactions
                if npc_key == "TIA_SOL" and topic in ["sigils", "herbs"]:
                    self.s.f["tia_trust"] += 1
                
                return
        
        self.output(f"You don't see '{target}' here to talk to.")

    def cmd_read(self, target):
        """Read items with text"""
        target = norm(target)
        
        # Check readable items
        readable_items = {
            "poster": "Auric Gallery Retrospective. Entry Code: 1207. Security by Unit 12-07.",
            "newspaper": "Headlines blur in the rain, but the paper is still good.",
            "note scrap": "Wet ink shows a counter-sigil pattern.",
            "blueprint": "Vault schematics show three sigil insertion points.",
            "sigil manual": "Chapter 3: Ward Sigils deflect necromantic energy.",
            "gallery map": "Atrium center, Archives east, Storage down, Roof access north."
        }
        
        for item_key in self.s.inv + self.room_items():
            if item_key in self.items and target in norm(self.items[item_key]['name']):
                item_name = self.items[item_key]['name']
                if item_name in readable_items:
                    self.output(readable_items[item_name])
                    
                    # Special effects
                    if item_key == "POSTER":
                        self.output("You notice the security code: 1207")
                        self.s.f["knows_gallery_code"] = True
                    
                    return
                else:
                    self.output(f"The {item_name} has no readable text.")
                    return
        
        self.output(f"You don't see '{target}' here to read.")

    def cmd_open_close(self, action, target):
        """Open or close items"""
        target = norm(target)
        
        for item_key in self.s.inv + self.room_items():
            if item_key in self.items and target in norm(self.items[item_key]['name']):
                item = self.items[item_key]
                
                if action == "open":
                    if item_key == "BRASS_LOCKET" and not item.get("stuck", False):
                        if not item.get("open", False):
                            self.output("The locket springs open, revealing a FEATHER TOKEN!")
                            self.s.inv.append("SIGIL_TOKEN_FEATHER")
                            self.items["SIGIL_TOKEN_FEATHER"]["loc"] = "inv"
                            self.s.f["token_feather"] = True
                            item["open"] = True
                        else:
                            self.output("The locket is already open.")
                    else:
                        self.output(f"You can't open the {item['name']}.")
                else:  # close
                    self.output(f"You can't close the {item['name']}.")
                return
        
        self.output(f"You don't see '{target}' here.")

    def cmd_sense(self, sense_type):
        """Use senses to perceive environment"""
        room = self.current_room()
        
        if sense_type == "listen":
            if self.s.location == "L01":
                self.output("Rain patters, the radio crackles, and the cat purrs softly.")
            elif self.s.location == "L02":
                self.output("Music thrums from clubs, water rushes in the drain.")
            elif self.s.location == "L06":
                self.output("River sounds, bat wing-beats, guitar strings.")
            else:
                self.output("You listen carefully but hear only ambient city sounds.")
        
        elif sense_type == "smell":
            if self.s.location == "L03":
                self.output("Coffee, burnt sugar, and old wood.")
            elif self.s.location == "L08":
                self.output("Herbs, incense, and something protective.")
            else:
                self.output("Urban scents: rain, exhaust, and humanity.")

    def cmd_vampire_sense(self):
        """Use vampire supernatural senses"""
        room = self.current_room()
        
        if self.s.location == "L05":
            self.output("VAMPIRE SENSE: The resin pulses with necromantic energy.")
        elif self.s.location == "L07":
            self.output("VAMPIRE SENSE: Ward circuits flow beneath the floor.")
        elif self.s.location == "L10":
            self.output("VAMPIRE SENSE: Shadow magic lingers in the chalk mark.")
        elif "EZRA_VALE" in self.room_npcs():
            self.output("VAMPIRE SENSE: Overwhelming power, death magic, and hunger.")
        else:
            self.output("VAMPIRE SENSE: Nothing supernatural stands out here.")

    def cmd_mesmerize(self, target):
        """Use vampire mesmerism on NPCs"""
        target = norm(target)
        
        for npc_key in self.room_npcs():
            if target in norm(self.npcs[npc_key]['name']):
                if self.s.will <= 0:
                    self.output("You lack the will to mesmerize anyone.")
                    return
                
                self.s.will -= 1
                
                if npc_key == "LUPITA":
                    self.output("Lupita's eyes glaze. 'The gallery code... 1207...'")
                    self.s.f["knows_gallery_code"] = True
                elif npc_key == "REEF":
                    self.output("Reef speaks in monotone: 'Ward sigils... touch with silver...'")
                elif npc_key == "TIA_SOL":
                    self.output("Tia Sol resists strongly. 'Your tricks won't work here, creature.'")
                    self.s.f["tia_trust"] -= 2
                else:
                    self.output(f"You mesmerize {self.npcs[npc_key]['name']}.")
                
                return
        
        self.output(f"You don't see '{target}' here to mesmerize.")

    def cmd_bite(self, target):
        """Vampire bite action"""
        target = norm(target)
        
        if self.s.hunger <= 0:
            self.output("You're not hungry right now.")
            return
        
        for npc_key in self.room_npcs():
            if target in norm(self.npcs[npc_key]['name']):
                self.s.hunger -= 1
                self.s.health += 1
                self.s.f["bite_count"] += 1
                
                self.output(f"You bite {self.npcs[npc_key]['name']}. Warmth flows through you.")
                
                # Consequences
                if npc_key == "EZRA_VALE":
                    self.output("Vale's blood burns with dark power!")
                    self.s.health -= 2
                else:
                    self.s.f["empathy"] -= 1
                
                return
        
        self.output(f"You don't see '{target}' here to bite.")

    def cmd_enter_code(self, code):
        """Enter code on keypad"""
        if self.s.location == "L05" and "KEYPAD" in self.current_room().get('features', []):
            if code == "1207":
                self.output("BEEP. The gallery door unlocks!")
                self.world["L05"]["exits"]["inside"] = "L07"
                self.s.f["façade_unlocked"] = True
            else:
                self.output("BUZZ. Incorrect code.")
        else:
            self.output("There's no keypad here.")

    def cmd_trace_sigil(self):
        """Trace sigil in Rain Alley"""
        if self.s.location != "L01":
            self.output("No sigil here to trace.")
            return
        if not self.world["L03"].get("locked", True):
            self.output("You've already dispelled the door sigil.")
            return
        
        # Calculate cost - easier if you have note scrap or manual
        cost = 1
        if "NOTE_SCRAP" not in self.s.inv and "SIGIL_MANUAL" not in self.s.inv:
            cost = 2
        
        if self.s.will < cost:
            self.output("You start the strokes but your focus slips. (Need more WILL.)")
            return
        
        self.s.will -= cost
        self.world["L03"]["locked"] = False
        self.world["L01"]["exits"]["south"] = "L03"
        self.s.f["sigil_traced"] = True
        self.output("You trace the counter-strokes. The sigil exhales and fades. The back room unlocks.")

    def cmd_craft_counter_ink(self):
        """Craft counter-ink from herbs"""
        if ("GARLIC" in self.s.inv and "ROSEMARY" in self.s.inv and 
            "HEMATITE" in self.s.inv):
            self.output("You grind the herbs and stone together, creating counter-ink!")
            self.s.inv.remove("GARLIC")
            self.s.inv.remove("ROSEMARY")
            self.s.inv.remove("HEMATITE")
            self.s.inv.append("COUNTER_INK")
            self.items["COUNTER_INK"]["loc"] = "inv"
        else:
            self.output("You need garlic, rosemary, and hematite to craft counter-ink.")

    def cmd_map(self):
        """Show visited locations"""
        seen_locations = [self.world[loc]['name'] for loc in self.s.seen if loc in self.world]
        self.output("Visited locations:")
        for loc in seen_locations:
            self.output(f"- {loc}")

    def cmd_help(self):
        """Show available commands"""
        help_text = """COMMANDS:
Movement: GO <direction> (N/S/E/W/U/D/IN/OUT)
Items: TAKE <item>, DROP <item>, USE <item> [ON <target>], COMBINE <A> WITH <B>
Looking: LOOK, EXAMINE <thing>, INVENTORY/I, READ <thing>
People: TALK <person> [ABOUT <topic>], GIVE <item> TO <person>
Actions: OPEN/CLOSE <thing>, PUSH <thing>, LISTEN, SMELL, WAIT/Z
Vampire: SENSE, MESMERIZE <person>, BITE <target>
Special: ENTER CODE <####>, TRACE SIGIL, CRAFT COUNTER-INK, TUNE ANTENNA
         INSERT TOKEN <WARD/FEATHER/SHADOW>
Game: STATS, MAP, HINT, SAVE, LOAD, QUIT"""
        self.output(help_text)            

    def cmd_hint(self):
        """Show contextual hints"""
        hints = self.hints["general"]
        
        if not self.s.f.get("façade_unlocked", False):
            hints.extend(["Find the gallery entry code.", "Talk to NPCs about the gallery."])
        
        if self.s.f.get("façade_unlocked", False) and not self.s.f.get("vault_open", False):
            hints.extend(["Collect three sigil tokens to open the vault.", "Ward sigils can be extracted with silver."])
        
        hint = random.choice(hints)
        self.output(f"HINT: {hint}")

    def cmd_save(self):
        """Save game state"""
        try:
            save_data = {
                'turn': self.s.turn,
                'health': self.s.health,
                'will': self.s.will,
                'hunger': self.s.hunger,
                'location': self.s.location,
                'inv': self.s.inv,
                'seen': list(self.s.seen),
                'flags': self.s.f,
                'items': {k: v for k, v in self.items.items() if v.get('loc') != v.get('original_loc', v.get('loc'))}
            }
            
            with open('savegame.json', 'w') as f:
                json.dump(save_data, f)
            
            self.output("Game saved successfully.")
        except Exception as e:
            self.output(f"Save failed: {e}")

    def cmd_load(self):
        """Load game state"""
        try:
            if not os.path.exists('savegame.json'):
                self.output("No save file found.")
                return
            
            with open('savegame.json', 'r') as f:
                save_data = json.load(f)
            
            self.s.turn = save_data['turn']
            self.s.health = save_data['health']
            self.s.will = save_data['will']
            self.s.hunger = save_data['hunger']
            self.s.location = save_data['location']
            self.s.inv = save_data['inv']
            self.s.seen = set(save_data['seen'])
            self.s.f = save_data['flags']
            
            # Restore modified items
            for item_key, item_data in save_data.get('items', {}).items():
                if item_key in self.items:
                    self.items[item_key].update(item_data)
            
            self.output("Game loaded successfully.")
            self.output(self.look_around())
        except Exception as e:
            self.output(f"Load failed: {e}")

    def check_win_conditions(self):
        """Check for game ending conditions - only used when explicitly triggered"""
        # Endings are now triggered by specific player actions, not just location
        # This method is kept for compatibility but doesn't auto-trigger endings
        pass

    def handle_final_confrontation(self, item_key, target):
        """Handle final confrontation with Ezra Vale"""
        if target and ("ezra" in target or "vale" in target or "necroframe" in target):
            # Different endings based on items and player state
            if item_key == "SILVER_NAILS" and self.s.f.get("vault_open", False):
                self.output("You pin the silver nails into the necroframe's core.")
                self.output("The resin locks cold around the ritual; silver binds it to silence.")
                self.trigger_ending("containment")
            elif item_key == "LENS_ARRAY_CASE" and "BLUEPRINT" in self.s.inv:
                self.output("You angle mirrors along the dawn line. Light knifes the frame—sigils scream and go dark.")
                self.trigger_ending("obliteration")
            elif item_key == "BRASS_LOCKET" and "COUNTER_INK" in self.s.inv and self.s.f.get("empathy", 0) >= 1:
                self.output("You raise the locket, trace the counter-sigil in ink. Ezra's breath breaks; grief finds a softer path.")
                self.trigger_ending("redemption")
            else:
                self.output("'Leave me my work,' he says, voice a winter river. 'Or make it quick.'")
                self.output("You need the right tools and approach for this confrontation.")
        else:
            self.output(f"You can't use the {self.items[item_key]['name']} that way here.")

    def cmd_push(self, target):
        """Push objects in the environment"""
        target = norm(target)
        
        if target == "crate" and self.s.location == "L01":
            if "CRATE" in self.room_items():
                self.output("You push the heavy crate under the fire escape ladder.")
                self.output("Now you can climb up to the rooftops!")
                self.s.f["crate_positioned"] = True
            else:
                self.output("There's no crate here to push.")
        else:
            self.output(f"You can't push '{target}' here.")

    def trigger_ending(self, ending_type):
        """Trigger one of the three possible endings"""
        self.s.f["ending"] = ending_type
        
        if ending_type == "redemption":
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("You approach Vale with compassion, not hatred. Your empathy reaches")
            self.output("through his necromantic shell to the broken man within.")
            self.output("'I... I remember what it was to be human,' he whispers.")
            self.output("The necroframe dissolves as Vale chooses redemption over power.")
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("**ENDING: REDEMPTION** - Vale is saved through compassion.")
        
        elif ending_type == "containment":
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("Using the vault's ward technology, you contain Vale's power.")
            self.output("He rages against the binding, but the sigils hold strong.")
            self.output("'This won't hold me forever!' he snarls.")
            self.output("But for now, Austin is safe from his influence.")
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("**ENDING: CONTAINMENT** - Vale is imprisoned but alive.")
        
        else:  # obliteration
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("With no other options, you strike at Vale's heart.")
            self.output("The necroframe explodes in brilliant light as his power breaks.")
            self.output("Vale screams as his essence scatters to the winds.")
            self.output("Austin is free, but at the cost of a soul's destruction.")
            self.output("═══════════════════════════════════════════════════════════════════════════════")
            self.output("**ENDING: OBLITERATION** - Vale is destroyed completely.")
