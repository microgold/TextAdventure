#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shadow Circuit: A Night in Austin — Expanded Edition (v1.5)

A neon-noir, urban-fantasy text adventure. You are MARLOWE CROSS, a newly-turned
vampire detective, hunting the glue-obsessed necromancer EZRA VALE across Austin
before dawn.

Run:
  python3 shadow_circuit_full.py

Highlights:
- 12+ locations with multiple paths
- NPCs: Lupita, Reef, Tia Sol, Gasket (the dog), Ezra
- Items & puzzles use nearly every object: coin+string fishing, solvent,
  jar sampling, straw siphon, wire cutters, silvered thread with dog, etc.
- Vault requires 3 sigil tokens (ward/feather/shadow) found via different mechanics
- Three endings (Redemption / Containment / Obliteration)
- Save/Load game, simple map & hint system
- Turns tick down to dawn

Parser (aliases in []):
  LOOK [L], EXAMINE [X] <thing>, INVENTORY [I], STATS, MAP, HINT
  TAKE/GET <item>, DROP <item>
  GO <dir/place> or N,S,E,W,U,D, INSIDE, OUT
  READ <thing>, OPEN/CLOSE <thing>
  USE <item> [ON|WITH] <target>, COMBINE <item> WITH <item>
  LISTEN, SMELL, WAIT [Z]
  TALK/ASK <npc> [ABOUT <topic>]
  SENSE, MESMERIZE <npc>, BITE <target>
  ENTER CODE #### (for keypads)
  TRACE SIGIL (Rain Alley)
  CRAFT COUNTER-INK (if you have garlic+rosemary+hematite)
  SAVE, LOAD, QUIT
"""

# ---- headers, utilities, state, world/items/npcs/hints ---

import sys, json, os, textwrap, random
from collections import defaultdict

def wrap(s, width=94):
    return "\n".join(textwrap.wrap(s, width)) if s else ""

def title(s):
    return f"# {s}"

def norm(s): return s.lower().strip()

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
                           "COIN wedged in a curb crack. A STORM DRAIN whispers under water. A NEWSSTAND creaks.",
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
            "GARLIC":{"name":"garlic clove","loc":"L08","portable":True,
                      "desc":"Pungent protection."},
            "ROSEMARY":{"name":"rosemary sprig","loc":"L08","portable":True,
                        "desc":"Green, resinous scent."},
            "SILVERED_THREAD":{"name":"silvered thread","loc":"L08","portable":True,
                               "desc":"Shimmers—excellent for a delicate pull."},
            "SIGIL_MANUAL":{"name":"sigil manual","loc":"L08","portable":False,
                            "desc":"Illustrated patterns for wards and counters."},
            # L09
            "BLUEPRINT":{"name":"Vale Tower blueprints","loc":"L09","portable":True,
                         "desc":"Ward lattice, dawn-angle line for mirror trick."},
            "LENS_ARRAY_CASE":{"name":"sunglass lens array (in case)","loc":"L09","portable":False,
                               "desc":"Mirrored lenses locked behind glass."},
            "MAGNET_CARD_hidden":{"name":"magnet card (hidden)","loc":"L09_hidden","portable":True,
                                  "desc":"A magnet card—perfect to trip a cheap case lock."},
            "LENS_ARRAY":{"name":"sunglass lens array","loc":"NOWHERE","portable":True,
                          "desc":"Mirrored lenses to redirect dawn."},
            "CASE_KEY":{"name":"case key","loc":"NOWHERE","portable":True,
                        "desc":"A tiny brass key for the archives case."},
            # L10
            "SOLVENT":{"name":"solvent (weak)","loc":"L10","portable":True,"uses":4,
                       "desc":"Resin cleaner—in small doses."},
            "GLOVES":{"name":"industrial gloves","loc":"L10","portable":True,
                      "desc":"Chemical-resistant. Protects hands."},
            "RAG":{"name":"rag","loc":"L10","portable":True,
                   "desc":"Oily but absorbent."},
            # L11
            "BONE":{"name":"bone","loc":"L11","portable":True,
                    "desc":"A delicious bribe for a dog."},
            "WIRE_CUTTER":{"name":"wire cutter","loc":"L11","portable":True,
                           "desc":"Greasy jaws, still sharp."},
            # L12
            "ANTENNA_PANEL":{"name":"antenna panel","loc":"L12","portable":False,
                             "desc":"Tunable panel humming with ward resonance."},
            "BOLT":{"name":"loose bolt","loc":"L12","portable":True,
                    "desc":"A loose bolt rattling near the panel."},
            # Roof
            "NECROFRAME":{"name":"necroframe","loc":"VALE_ROOF","portable":False,
                          "desc":"A lattice of resin and mirrors, humming with grief."},
            # Crafted / special
            "RESIN_SAMPLE":{"name":"resin sample (jar)","loc":"NOWHERE","portable":True,
                            "desc":"Living resin pulses against glass."},
            "WARD_TOKEN":{"name":"ward token (rubbing)","loc":"NOWHERE","portable":True,
                          "desc":"A circle token with jagged rim—bench sigil."},
            "FEATHER_TOKEN":{"name":"feather token (drawn)","loc":"NOWHERE","portable":True,
                             "desc":"A delicate feather sigil token (per manual)."},
            "SHADOW_TOKEN":{"name":"shadow token (imprint)","loc":"NOWHERE","portable":True,
                            "desc":"An imprint from a shadowmark—cool to the touch."},
            "AETHER_RESIN":{"name":"aether resin (refined)","loc":"NOWHERE","portable":True,
                            "desc":"Refined and hungry; binds power when placed with nails."},
            "COUNTER_INK":{"name":"counter-sigil ink","loc":"NOWHERE","portable":True,
                           "desc":"A small vial mixed from garlic, rosemary, hematite."},
        }
        return I

    def _build_npcs(self):
        N = {
            "LUPITA":{"name":"Lupita","loc":"L04",
                      "desc":"Food truck owner with warm eyes and sharper jokes.",
                      "topics":{
                          "auric":"“Gallery's got suits tonight. Feels hinky.”",
                          "glue":"“Guy left amber strings on my napkins. Eww but also… interesting?”",
                          "late-night crowd":"“Tourists and chaos. Keep your wallet close.”",
                      }},
            "REEF":{"name":"Reef","loc":"L06",
                    "desc":"A homeless musician. His chords sound like rain on wire.",
                    "topics":{
                        "sounds":"“Wards hum. Tune your ear and you'll walk through walls.”",
                        "ezra":"“He walks with grief. Storms aren't evil—they're just storms.”",
                        "resin":"“It takes shape from what you feed it. Don't feed it fear.”",
                    }},
            "TIA_SOL":{"name":"Tia Sol","loc":"L08",
                       "desc":"Witch and botanica owner. Incense dust twinkles when she moves.",
                       "topics":{
                           "counter-sigil":"“Intention, then stroke order. Ink helps it bite.”",
                           "hunger":"“Yours howls. Feed it on choices, not throats.”",
                           "consent rules":"“Thresholds ask. Doors answer. It's old law.”",
                           "ezra":"“Grief carved him hollow. Some fill hollows with light. Others with glue.”",
                       }},
            "GASKET":{"name":"Gasket","loc":"L11",
                      "desc":"A good boy. Tail thumps like a drum. Loves bones.",
                      "topics":{}},
            "EZRA_VALE":{"name":"Ezra Vale","loc":"VALE_ROOF",
                         "desc":"Brilliant, broken. Grief-lit eyes hold too much sky.",
                         "topics":{}},
        }
        return N

    def _build_hints(self):
        return {
            "L01":[
                "The sigil on the door can be counter-traced. Try TRACE SIGIL.",
                "If you have the NOTE SCRAP or read the manual, the strokes are easier.",
                "No chalk? TRACE SIGIL still works, but it costs effort (WILL)."
            ],
            "L05":[
                "The keypad wants numbers. POSTER and RADIO both whisper 12-07.",
                "Resin on the locket softens with SOLVENT or with MUG steam + STRAW + JAR."
            ],
            "L07":[
                "The VAULT needs three different sigil tokens.",
                "Try: WARD token from the underbridge bench, FEATHER token from Tia's manual, SHADOW token from Storage.",
                "Collect resin with an EMPTY JAR if you want a sample."
            ],
            "L09":[
                "The lens CASE opens with a MAGNET CARD or a CASE KEY from the vault.",
                "Coin + String at the NEWSSTAND can fish out something."
            ],
            "L11":[
                "The chain gate: WIRE CUTTER works, or tie SILVERED THREAD to a latch and have GASKET pull (give BONE)."
            ],
            "L12":[
                "Fix the ANTENNA PANEL (use BOLT), then TUNE ANTENNA. LISTEN first to hear the tones.",
                "The RADIO can help you lock the right frequency."
            ],
        }

# ---------- core loop, movement, command router ----------

    # ---------- Core Loop & I/O ----------
    def run(self):
        print("Welcome to Shadow Circuit: A Night in Austin — Expanded Edition")
        self.look(announce=True)
        while True:
            if self.s.turn >= self.s.max_turns:
                self.lose("Sunlight runs the alleys like molten glass. You have no shadow left to stand in.")
            try:
                cmd = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodnight.")
                return
            if not cmd:
                continue
            self.handle(cmd)

    # ---------- Turn / Status ----------
    def tick(self, cost=1):
        self.s.turn += cost
        if self.s.hunger >= 4 and random.random() < 0.1:
            print("Your hunger scrapes the back of your throat. Words come out with fangs.")
        self.s.health = max(0, min(3, self.s.health))
        self.s.will = max(0, min(3, self.s.will))
        self.s.hunger = max(0, min(5, self.s.hunger))

    def lose(self, why):
        print("\n" + wrap(why))
        print("\n*** You lose. Dawn takes what it is owed. ***")
        sys.exit(0)

    def stats(self):
        left = self.s.max_turns - self.s.turn
        print(f"Health {self.s.health}/3 · Will {self.s.will}/3 · Hunger {self.s.hunger}/5 · Turns until dawn: {left}")
        inv = ", ".join(self.items[i]["name"] for i in self.s.inv) if self.s.inv else "(empty)"
        print("Inventory:", inv)

    def look(self, announce=False):
        L = self.world[self.s.location]
        if announce:
            print("\n" + title(f"{L['name']} — Turn {self.s.turn+1}"))
        print("\n" + wrap(L["desc"]))
        vis_items = [self.items[i]["name"] for i in self.items if self.items[i]["loc"] == self.s.location and not i.endswith("_hidden")]
        if vis_items:
            print("You notice:", ", ".join(vis_items) + ".")
        feats = L.get("features", [])
        if feats:
            print("Features here:", ", ".join(f.lower().replace("_"," ") for f in feats) + ".")
        npcs = [k for k,v in self.npcs.items() if v["loc"] == self.s.location]
        if npcs:
            print("Someone here:", ", ".join(self.npcs[n]["name"] for n in npcs) + ".")
        exits = []
        for d,t in L["exits"].items():
            if self.exit_unlocked(t):
                exits.append(d.capitalize())
        if exits:
            print("Exits:", ", ".join(exits) + ".")
        print()
        self.stats()

    # ---------- Movement & Gates ----------
    def exit_unlocked(self, loc_id):
        if loc_id.endswith("_locked"):
            if loc_id.startswith("L03"):
                return not self.world["L03"].get("locked", True)
            if loc_id.startswith("L07"):
                return self.s.f["façade_unlocked"]
            if loc_id.startswith("VALE_ROOF"):
                return self.s.f["vale_roof_unlocked"]
            return False
        if loc_id.endswith("_req"):
            return True
        return True

    def real_target(self, loc_id):
        if loc_id.endswith("_locked") or loc_id.endswith("_req"):
            return loc_id.rsplit("_",1)[0]
        return loc_id

    def do_go(self, dirn):
        L = self.world[self.s.location]
        dirn = dirn.lower()
        if dirn in DIRECTIONS:
            dirn = DIRECTIONS[dirn]
        if dirn not in L["exits"]:
            print("You can't go that way.")
            return
        t = L["exits"][dirn]
        if not self.exit_unlocked(t):
            if t.startswith("L03"):
                print("The service door is locked by a chalk sigil. TRACE SIGIL to counter it.")
                return
            if t.startswith("L07"):
                print("The glass door is locked by a keypad.")
                return
            if t.startswith("VALE_ROOF"):
                print("The ward still bars the way south along the rooftops.")
                return
            print("That path is blocked.")
            return
        self.s.location = self.real_target(t)
        self.s.seen.add(self.s.location)
        self.tick()
        self.look(announce=True)

    # ---------- Command Handling ----------
    def handle(self, cmd):
        tokens = cmd.strip().split()
        if not tokens: return
        v = tokens[0].lower()

        if v in DIRECTIONS or v in ["inside","out"]:
            if v in DIRECTIONS: self.do_go(v)
            elif v == "inside": self.do_go("inside")
            elif v == "out": self.do_go("out")
            return

        alias = {"l":"look","x":"examine","i":"inventory","inv":"inventory","z":"wait"}
        v = alias.get(v, v)
        args = tokens[1:]

        if v == "help":
            self.tick(0)
            print(wrap("Commands: LOOK/L, EXAMINE/X <thing>, TAKE/GET <item>, DROP <item>, "
                       "GO <dir> (or N,S,E,W,U,D, INSIDE, OUT), READ <thing>, OPEN/CLOSE <thing>, "
                       "USE <item> [ON/WITH] <target>, COMBINE A WITH B, TALK/ASK <npc> [ABOUT <topic>], "
                       "LISTEN, SMELL, WAIT/Z, SENSE, MESMERIZE <npc>, BITE <target>, ENTER CODE ####, "
                       "TRACE SIGIL, CRAFT COUNTER-INK, MAP, HINT, STATS, SAVE, LOAD, QUIT."))
            return
        if v in ["quit","exit"]:
            print("Goodnight.")
            sys.exit(0)
        if v in ["look"]:
            self.tick(0); self.look(announce=True); return
        if v in ["inventory"]:
            self.tick(0); self.stats(); return
        if v in ["stats"]:
            self.tick(0); self.stats(); return
        if v in ["map"]:
            self.tick(0); self.show_map(); return
        if v in ["hint"]:
            self.tick(0); self.show_hint(); return
        if v in ["wait"]:
            self.tick(); print("You let the night breathe around you."); return
        if v in ["go"]:
            if not args: print("Go where?"); return
            self.do_go(" ".join(args)); return
        if v in ["take","get"]:
            if not args: print("Take what?"); return
            self.do_take(" ".join(args)); return
        if v in ["drop"]:
            if not args: print("Drop what?"); return
            self.do_drop(" ".join(args)); return
        if v in ["examine","x"]:
            if not args: print("Examine what?"); return
            self.do_examine(" ".join(args)); return
        if v in ["read"]:
            if not args: print("Read what?"); return
            self.do_read(" ".join(args)); return
        if v in ["open"]:
            if not args: print("Open what?"); return
            self.do_open(" ".join(args)); return
        if v in ["close"]:
            if not args: print("Close what?"); return
            self.do_close(" ".join(args)); return
        if v in ["use"]:
            if not args: print("Use what?"); return
            left = " ".join(args)
            if " on " in left:
                a,b = left.split(" on ",1)
            elif " with " in left:
                a,b = left.split(" with ",1)
            else:
                a,b = left,None
            self.do_use(a.strip(), b.strip() if b else None); return
        if v in ["combine"]:
            if "with" not in [a.lower() for a in args]:
                print("Combine what WITH what?")
                return
            idx = [a.lower() for a in args].index("with")
            a = " ".join(args[:idx]); b = " ".join(args[idx+1:])
            self.do_combine(a,b); return
        if v in ["listen"]:
            self.do_listen(); return
        if v in ["smell"]:
            self.do_smell(); return
        if v in ["talk","ask"]:
            if not args: print("Talk to whom?"); return
            self.do_talk(args); return
        if v in ["sense"]:
            self.do_sense(); return
        if v in ["mesmerize"]:
            if not args: print("Mesmerize whom?"); return
            self.do_mesmerize(" ".join(args)); return
        if v in ["bite"]:
            self.do_bite(" ".join(args[1:]) if args and args[0].lower()=="to" else " ".join(args)); return
        if v in ["enter"] and len(args)>=2 and args[0].lower()=="code":
            self.do_enter_code(args[1]); return
        if v in ["trace"] and "sigil" in [a.lower() for a in args]:
            self.do_trace_sigil(); return
        if v in ["craft"] and "counter-ink" in [a.lower() for a in args]:
            self.do_craft_counter_ink(); return
        if v in ["save"]:
            self.do_save(); return
        if v in ["load"]:
            self.do_load(); return

        print("That doesn't seem to work. Type HELP for commands.")

    # ---------- Map / Hints ----------
    def show_map(self):
        discovered = [self.world[l]["name"] for l in self.s.seen]
        print("Discovered places:")
        for name in sorted(discovered):
            print(" -", name)

    def show_hint(self):
        loc = self.s.location
        tips = self.hints.get(loc, [])
        if not tips:
            print("Trust your instincts. Or your nose.")
            return
        step = min(2, self.s.turn // 8)
        print("Hint:", tips[step])

# ---------- Item actions ----------

    # ---------- Read / Examine ----------
    def do_read(self, obj):
        key = self.find_item_key(obj)
        if not key:
            print("No readable text there.")
            return
        self.tick()
        if key == "POSTER":
            print(wrap("“Auric Gallery Retrospective — Midnight to Dawn. Entry with code only. Security by Unit 12-07.”"))
            return
        if key == "SIGIL_MANUAL":
            self.s.f["met_tia"] = True
            print(wrap("You study stroke orders and counter-sigils. Feather patterns for focus, ward lines for binding."))
            return
        if key == "GALLERY_MAP":
            print(wrap("Map: Atrium center; Archives east; Storage down; Rooftop via fire escape + wards. A note marks 'Vale Tower'. "))
            return
        if key == "BLUEPRINT":
            print(wrap("Blueprint shows ward nodes on the roof and a 'dawn-angle' line—perfect for a mirror array."))
            return
        if key == "AUDIO_GUIDE":
            print(wrap("“Welcome to the Vale Retrospective… please proceed to the—” static."))
            return
        print("Nothing helpful to read.")

    def do_examine(self, obj):
        npc = self.find_npc(obj)
        if npc:
            self.tick()
            print(wrap(self.npcs[npc]["desc"]))
            return
        key = self.find_item_key(obj)
        self.tick()
        if key:
            print(wrap(self.items[key]["desc"]))
            if key == "BRASS_LOCKET" and self.items["BRASS_LOCKET"].get("stuck", False):
                print("It won't budge—resin holds it fast.")
            if key == "LENS_ARRAY_CASE":
                print("A tiny keyhole winks; a magnet swipe might work too.")
            if key == "RESIN_PUDDLE":
                print("It pulses faintly. Maybe collect a sample in a JAR.")
            return
        feats = self.world[self.s.location].get("features",[])
        o = obj.lower()
        if "sigil" in o and "CHALK_SIGIL" in feats:
            print(wrap("A chalk sigil bars the back room. TRACE SIGIL to counter the pattern.")); return
        if "keypad" in o and "KEYPAD" in feats:
            print(wrap("Slick with rain. Numbers want to be: 12-07.")); return
        if "antenna" in o and "WARD_ANTENNA" in feats:
            print(wrap("Three tones drift. The panel is a bit loose—maybe a BOLT would fix it.")); return
        if "case" in o and "CASE_LOCK" in feats:
            print(wrap("A cheap glass case with a magnetic seam and keyhole.")); return
        if "shadowmark" in o and "SHADOWMARK" in feats:
            print(wrap("The chalk seems to stand off the wall. SENSE might make it imprintable.")); return
        if "storm" in o and "STORM_DRAIN" in feats:
            print(wrap("Water gnashes at the grille. Under it—numbers in rhythm.")); return
        if "newsstand" in o and "NEWSSTAND" in feats:
            print(wrap("A narrow gap behind the stand. Maybe fish something with string+coin.")); return
        print("Nothing special.")

    # ---------- Inventory ----------
    def do_take(self, obj):
        key = self.find_item_key(obj)
        if not key:
            print("You don't see that here.")
            return
        if not self.items[key].get("portable", True):
            print("That's not something you can pocket.")
            return
        if key == "BRASS_LOCKET" and self.items["BRASS_LOCKET"].get("stuck", False):
            print("The resin threads still hold the locket. Needs softening or a trick.")
            return
        if key == "MAGNET_CARD_hidden":
            print("You can't quite reach—maybe fish it out somehow.")
            return
        self.tick()
        if key not in self.s.inv:
            self.s.inv.append(key)
        self.items[key]["loc"] = "PLAYER"
        print(f"You take the {self.items[key]['name']}.")

    def do_drop(self, obj):
        key = self.find_item_key(obj, where="PLAYER")
        if not key:
            print("You don't have that.")
            return
        self.tick()
        self.s.inv.remove(key)
        self.items[key]["loc"] = self.s.location
        print(f"You drop the {self.items[key]['name']}.")

    # ---------- Use / Combine ----------
    def do_use(self, a, b):
        A = self.find_item_key(a, where="PLAYER")
        if not A:
            print("You don't have that.")
            return

        if A == "SOLVENT" and b and any(t in b.lower() for t in ["locket","resin","threads"]):
            if self.s.location != "L05":
                self.tick(); print("No resin-bound locket here."); return
            if self.items["SOLVENT"].get("uses",0) <= 0:
                self.tick(); print("Your solvent bottle is dry."); return
            self.tick()
            self.items["SOLVENT"]["uses"] -= 1
            self.items["BRASS_LOCKET"]["stuck"] = False
            print(wrap("You soak the rag with solvent and press to the threads. They hiss and slacken. "
                       "With a tug, the locket comes free."))
            if "BRASS_LOCKET" not in self.s.inv:
                self.s.inv.append("BRASS_LOCKET")
                self.items["BRASS_LOCKET"]["loc"] = "PLAYER"
                print("You take the brass locket.")
            return

        if A == "EMPTY_JAR" and b and "resin" in b.lower():
            if self.s.location != "L07":
                self.tick(); print("No safe resin to sample here."); return
            if "RESIN_SAMPLE" in self.s.inv:
                self.tick(); print("You already have a sample."); return
            self.tick()
            self.s.inv.append("RESIN_SAMPLE")
            self.items["RESIN_SAMPLE"]["loc"] = "PLAYER"
            self.s.f["resin_sampled"] = True
            print("You coax warm resin into the jar. It taps the glass like a slow heartbeat.")
            return

        if A in ["STRING","TAROT_COIN"] and b:
            B = self.find_item_key(b, where="PLAYER")
            pair = {A, B}
            feats = self.world[self.s.location].get("features",[])
            if "NEWSSTAND" in feats and "STRING" in pair and "TAROT_COIN" in pair:
                self.tick()
                print("You tie the coin to the string and fish behind the newsstand…")
                if self.items["MAGNET_CARD_hidden"]["loc"] == "L09_hidden":
                    self.items["MAGNET_CARD_hidden"]["loc"] = "L04"
                    print("Clack. A magnet card slides free onto the sidewalk.")
                else:
                    print("You scrape gum and a movie stub. Still—nice technique.")
                return

        if A in ["MAGNET_CARD_hidden","CASE_KEY"] and b and any(t in b.lower() for t in ["case","lock","lens","array"]):
            if self.s.location != "L09":
                self.tick(); print("No case here."); return
            self.tick()
            print("You trip the glass seam. *Click.* The case pops open.")
            if self.items["LENS_ARRAY_CASE"]["loc"] == "L09":
                self.items["LENS_ARRAY_CASE"]["loc"] = "NOWHERE"
                self.items["LENS_ARRAY"]["loc"] = "L09"
            return

        if A == "RAG" and (not b or any(t in (b or "").lower() for t in ["hand","hands","fingers"])):
            self.tick()
            self.s.f["sticky_fingers"] = False
            print("You wipe your hands clean. Mostly.")
            return

        if A == "WARD_CHALK":
            self.tick()
            feats = self.world[self.s.location].get("features",[])
            if self.s.location == "L06" and "WARD_SIGIL_BENCH" in feats:
                if "NEWSPAPER" in self.s.inv:
                    print("You chalk and press newspaper for a clean rubbing—the ward token lifts into your palm.")
                else:
                    print("You trace the ward lines and lift a chalky token—rough but serviceable.")
                if not self.s.f["token_ward"]:
                    self.s.f["token_ward"] = True
                    self.s.inv.append("WARD_TOKEN"); self.items["WARD_TOKEN"]["loc"] = "PLAYER"
                return
            if self.s.location == "L08" and "SIGIL_MANUAL" in [k for k in self.items if self.items[k]["loc"]=="L08"]:
                print("With the manual's pattern, you draw a feather sigil, lift it as a token.")
                if not self.s.f["token_feather"]:
                    self.s.f["token_feather"] = True
                    self.s.inv.append("FEATHER_TOKEN"); self.items["FEATHER_TOKEN"]["loc"] = "PLAYER"
                return
            if self.s.location == "L07" and self.world["L07"]["features"]:
                print("Chalking over the vault does nothing without proper tokens.")
                return
            print("You sketch idle sigils in the air. Pretty; ineffective.")
            return

        if A == "SILVERED_THREAD" and self.s.location == "L11":
            self.tick()
            print("You tie the silvered thread to the inner latch through the gate bars. Now if only someone could pull…")
            self.s.f["loyal_dog"] = True
            return

        if A == "WIRE_CUTTER" and self.s.location == "L11":
            self.tick()
            print("You snip the chain with a grunt. The gate swings loose.")
            return

        if A == "BOLT" and self.s.location == "L12":
            self.tick()
            self.s.f["antenna_fixed"] = True
            print("You twist the bolt into place. The panel sits firm, hum sharpening to a stable chord.")
            return

        if A == "SILVER_NAILS" and b and "resin" in b.lower():
            if "AETHER_RESIN" in self.s.inv:
                self.tick()
                print("You coat the nails with refined resin—the air around them tastes like winter metal.")
                return
            self.tick(); print("You don't have refined resin yet."); return

        if A == "LENS_ARRAY" and b and "blueprint" in b.lower():
            if "BLUEPRINT" in self.s.inv:
                self.tick()
                print("You plan the mirror angles along the dawn line. It will cut the ritual like glass.")
                return
            self.tick(); print("You need the tower blueprints to plan angles."); return

        if A == "POLICE_RADIO" and self.s.location == "L12":
            self.tick()
            if not self.s.f["antenna_fixed"]:
                print("The radio hisses; the panel rattles too much to hold a clear frequency. Maybe secure it first?")
            else:
                print("You sweep channels until the hum locks—remember the cadence. TUNE ANTENNA could seal it.")
            return

        self.tick()
        print("Nothing obvious happens.")

    def do_combine(self, a, b):
        A = self.find_item_key(a, where="PLAYER")
        B = self.find_item_key(b, where="PLAYER")
        if not A or not B:
            print("You don't hold both parts.")
            return
        self.tick()
        combo = {A,B}
        if combo == {"TAROT_COIN","STRING"}:
            print("Tie them first with USE COIN WITH STRING (at the newsstand) to fish properly.")
            return
        print("You fidget with your gear. Maybe try USE A ON B against something in the world.")

    # ---------- Special actions ----------
    def do_listen(self):
        self.tick()
        feats = self.world[self.s.location].get("features",[])
        if "STORM_DRAIN" in feats:
            print("Under water and grate: tap…tap… 1-2… 0-7. Sounds like a code.")
            return
        if "WARD_ANTENNA" in feats:
            if not self.s.f["antenna_fixed"]:
                print("Three tones drift, but the panel rattles out of tune.")
            else:
                print("Three tones: low, mid, high. They slide, then align for a breath—like they want to lock.")
            return
        if self.s.location == "L07":
            print("The atrium whispers: …frame…bind…Ezra…")
            return
        print("Rain, engines, and your heartbeat in your ears.")

    def do_smell(self):
        self.tick()
        if self.s.location in ["L05","L07"]:
            print("Acrid resin, hot electronics, and wet stone.")
        else:
            print("Austin smells like wet asphalt, coffee, and night.")

    def do_talk(self, args):
        if args[0].lower() == "to":
            args = args[1:]
        if "about" in [a.lower() for a in args]:
            idx = [a.lower() for a in args].index("about")
            who = " ".join(args[:idx]); topic = " ".join(args[idx+1:]).lower()
        else:
            who = " ".join(args); topic = None
        npc = self.find_npc(who)
        if not npc:
            print("No one by that name here.")
            return
        self.tick()
        if npc == "LUPITA":
            self.s.f["met_lupita"] = True
            if topic:
                key = "auric" if "auric" in topic else ("glue" if "glue" in topic or "resin" in topic else None)
                if key and key in self.npcs[npc]["topics"]:
                    print(wrap(self.npcs[npc]["topics"][key])); return
            print("“You look like you need carbs and secrets. Ask me about 'auric' or the 'glue' guy.”")
            return
        if npc == "REEF":
            self.s.f["met_reef"] = True
            if topic:
                for k,msg in self.npcs[npc]["topics"].items():
                    if k in topic:
                        print(wrap(msg)); break
                else:
                    print("Reef hums, eyes half-closed.")
            else:
                print("“Share warmth, share words. Ask about 'sounds', 'ezra', or 'resin'.”")
            if "MUG" in self.s.inv:
                print("He eyes your mug. “Trade? I could use that warmth.” (GIVE MUG TO REEF)")
            return
        if npc == "TIA_SOL":
            self.s.f["met_tia"] = True
            if topic:
                for k,msg in self.npcs[npc]["topics"].items():
                    if k in topic:
                        print(wrap(msg)); break
                else:
                    print("She arches a brow. “Be precise.”")
            else:
                print("“The night is thin; choose your strokes wisely. Ask about 'counter-sigil', 'hunger', 'consent rules', or 'ezra'.”")
            if "BRASS_LOCKET" in self.s.inv and self.s.f["tia_trust"] < 1:
                self.s.f["tia_trust"] = 1
                print("She sees the locket, gentles. “Keep that close. Here—chalk and a feather pattern.”")
                if "WARD_CHALK" not in self.s.inv and self.items["WARD_CHALK"]["loc"] != "PLAYER":
                    self.s.inv.append("WARD_CHALK"); self.items["WARD_CHALK"]["loc"] = "PLAYER"
            return
        if npc == "GASKET":
            print("Gasket pants happily, tail going like a metronome for joy.")
            if "BONE" in self.s.inv:
                print("He eyes your BONE with reverence. (GIVE BONE TO GASKET)")
            return
        if npc == "EZRA_VALE":
            if not self.s.f["vale_roof_unlocked"]:
                print("He barely notices you—wards roar too loud.")
                return
            if "AETHER_RESIN" in self.s.inv and "SILVER_NAILS" in self.s.inv:
                print(wrap("You lay resin and drive silver nails into ward marks. The frame stalls; the city exhales."))
                self.end("B"); return
            if "LENS_ARRAY" in self.s.inv and "BLUEPRINT" in self.s.inv:
                print(wrap("You angle mirrors along the dawn line. Light knifes the frame—sigils scream and go dark."))
                self.end("C"); return
            if "BRASS_LOCKET" in self.s.inv and "COUNTER_INK" in self.s.inv and self.s.f["empathy"] >= 1:
                print(wrap("You raise the locket, trace the counter-sigil in ink. Ezra's breath breaks; grief finds a softer path."))
                self.end("A"); return
            print("“Leave me my work,” he says, voice a winter river. “Or make it quick.”")
            return

    def do_mesmerize(self, who):
        npc = self.find_npc(who)
        if not npc:
            print("No target to catch your gaze.")
            return
        if self.s.will <= 0:
            self.tick(); print("Your will is ash; your gaze slides off like rain."); return
        self.tick()
        self.s.will -= 1
        print(f"You catch {self.npcs[npc]['name']}'s eyes. Time narrows. Breath syncs.")
        if self.s.hunger >= 4:
            print("Hunger frays the trance. Control wobbles.")
        else:
            print("For a heartbeat, they are yours to lead. But to what end?")

    def do_bite(self, target):
        self.tick()
        self.s.hunger = max(0, self.s.hunger - 1)
        self.s.will = min(3, self.s.will + 1)
        self.s.f["bite_count"] += 1
        self.s.f["empathy"] = max(0, self.s.f["empathy"] - 1)
        print("Copper and lightning. Strength steadies; a light inside you gutters.")

    def do_enter_code(self, digits):
        if self.s.location != "L05":
            print("There's no keypad here.")
            return
        self.tick()
        if digits == "1207" or digits == "12-07":
            self.s.f["façade_unlocked"] = True
            print("Beep. Beep. Beep. Beep. *Click.* The gallery door unlatches.")
        else:
            print("The keypad rejects it with a damp little chirp.")

    def do_trace_sigil(self):
        if self.s.location != "L01":
            print("No sigil here to trace.")
            return
        if not self.world["L03"]["locked"]:
            print("You've already dispelled the door sigil.")
            return
        self.tick()
        cost = 1 if ("NOTE_SCRAP" in self.s.inv or self.s.f["met_tia"]) else 2
        if self.s.will < cost:
            print("You start the strokes but your focus slips. (Need more WILL.)")
            return
        self.s.will -= cost
        self.world["L03"]["locked"] = False
        print("You trace the counter-strokes. The sigil exhales and fades. The back room unlocks.")

    def do_craft_counter_ink(self):
        need = {"GARLIC","ROSEMARY","HEMATITE"}
        if not need.issubset(set(self.s.inv)):
            print("You need GARLIC, ROSEMARY, and HEMATITE to craft the ink.")
            return
        if "COUNTER_INK" in self.s.inv:
            print("You already have counter-sigil ink.")
            return
        self.tick()
        self.s.inv.append("COUNTER_INK"); self.items["COUNTER_INK"]["loc"] = "PLAYER"
        print("You grind herbs and stone—steeped in your breath. The ink smells like thunder before rain.")
        self.s.f["empathy"] += 1

    # ---------- Open/Close ----------
    def do_open(self, obj):
        key = self.find_item_key(obj) or self.find_item_key(obj, where="PLAYER")
        if not key:
            print("Open what?")
            return
        self.tick()
        if key == "BRASS_LOCKET":
            if self.items["BRASS_LOCKET"].get("stuck",False):
                print("Resin holds it too tight.")
                return
            if not self.items["BRASS_LOCKET"].get("open",False):
                self.items["BRASS_LOCKET"]["open"] = True
                print(wrap("You open the locket: a miniature portrait—Ezra Vale and a gentle-faced man. "
                           "Along the rim, a tiny silver sigil that could fit a vault socket."))
                return
            print("It's already open.")
            return
        if key == "LENS_ARRAY_CASE":
            print("The case won't open by hand—needs a key or magnet swipe.")
            return
        print("It doesn't open.")

    def do_close(self, obj):
        key = self.find_item_key(obj) or self.find_item_key(obj, where="PLAYER")
        if key == "BRASS_LOCKET":
            self.tick()
            self.items["BRASS_LOCKET"]["open"] = False
            print("You close the locket. It still thrums faintly.")
            return
        self.tick(); print("No need to close that.")

# ---Part 4/4 — sense/vault/antenna/give, helpers, endings, main()---

    # ---------- Sense / Vault / Antenna / Give ----------
    def do_sense(self):
        self.tick()
        if self.s.location == "L10" and not self.s.f["token_shadow"]:
            print("The shadowmark lifts in your sight. You press the rag—an imprint comes away, cold.")
            self.s.f["token_shadow"] = True
            self.s.inv.append("SHADOW_TOKEN"); self.items["SHADOW_TOKEN"]["loc"] = "PLAYER"
            self.s.f["shadowmark_seen"] = True
            return
        if self.s.location == "L06" and not self.s.f["token_ward"]:
            print("Ward-lines under the bench breathe cold. Chalk would capture it as a token.")
            return
        print("The night sharpens—edges and echoes, the bones beneath the city.")

    def insert_token(self, which):
        if self.s.location != "L07":
            print("There is nowhere to socket that here.")
            return
        if which not in self.s.inv:
            print("You don't have that token.")
            return
        self.tick()
        self.s.f["sockets_inserted"] += 1
        self.s.inv.remove(which); self.items[which]["loc"] = "NOWHERE"
        print(f"You press the {self.items[which]['name']} into a socket. It hums in place.")
        if self.s.f["sockets_inserted"] >= 3 and not self.s.f["vault_open"]:
            self.s.f["vault_open"] = True
            print("The vault sighs open. Inside: refined AETHER RESIN…and a tiny CASE KEY.")
            if "AETHER_RESIN" not in self.s.inv:
                self.s.inv.append("AETHER_RESIN"); self.items["AETHER_RESIN"]["loc"] = "PLAYER"
            if "CASE_KEY" not in self.s.inv:
                self.s.inv.append("CASE_KEY"); self.items["CASE_KEY"]["loc"] = "PLAYER"

    def tune_antenna(self):
        if self.s.location != "L12":
            print("No antenna to tune here.")
            return
        if not self.s.f["antenna_fixed"]:
            print("The panel rattles too loose to hold a frequency. Secure it first.")
            return
        self.tick()
        self.s.f["antenna_tuned"] = True
        self.s.f["vale_roof_unlocked"] = True
        print("You nudge the three tones until they lock—like teeth of a key finding its ward. The path south slackens.")

    # ---------- Save / Load ----------
    def do_save(self, path="shadow_circuit_save.json"):
        data = {"state":self.s.__dict__,
                "items":self.items,
                "world":self.world}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        self.tick(0)
        print(f"Saved game to {path}")

    def do_load(self, path="shadow_circuit_save.json"):
        if not os.path.exists(path):
            print("No save found.")
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.s.__dict__ = data["state"]
        self.items = data["items"]
        self.world = data["world"]
        self.tick(0)
        print("Loaded save.")
        self.look(announce=True)

    # ---------- Give (barter & dog) ----------
    def do_give(self, what, to_whom):
        it = self.find_item_key(what, where="PLAYER")
        if not it:
            print("You don't have that.")
            return
        npc = self.find_npc(to_whom)
        if not npc:
            print("They're not here.")
            return
        self.tick()
        if npc == "REEF" and it == "MUG":
            if "HEMATITE" not in self.s.inv:
                self.s.inv.append("HEMATITE"); self.items["HEMATITE"]["loc"] = "PLAYER"
                print("You hand him the warmth. He presses a hematite stone into your palm. “Ground yourself.”")
            else:
                print("He nods gratefully, warms his hands. “Bless you.”")
            self.s.inv.remove("MUG"); self.items["MUG"]["loc"] = self.s.location
            return
        if npc == "GASKET" and it == "BONE":
            self.s.inv.remove("BONE"); self.items["BONE"]["loc"] = self.s.location
            if self.s.f["loyal_dog"]:
                print("Gasket slips through the gate with the thread and yanks—*click*. The latch releases.")
            else:
                print("Gasket crunches the bone, tail a metronome of joy.")
            return
        print("They accept it with a nod, but nothing obvious changes.")

    # ---------- Helpers ----------
    def find_item_key(self, name, where=None):
        if not name: return None
        name = norm(name)
        if where == "PLAYER" or where is None:
            for k in self.s.inv:
                if name in self.items[k]["name"].lower() or name == k.lower():
                    return k
        if where == "PLAYER":
            return None
        for k,v in self.items.items():
            if v["loc"] == self.s.location:
                if name in v["name"].lower() or name == k.lower():
                    return k
        return None

    def find_npc(self, name):
        if not name: return None
        name = norm(name)
        for k,v in self.npcs.items():
            if v["loc"] == self.s.location:
                if name in v["name"].lower() or name == k.lower():
                    return k
        return None

    # ---------- Endings ----------
    def end(self, which):
        self.s.f["ending"] = which
        print()
        if which == "A":
            print("*** Ending A — Redemption ***")
            print(wrap("Ezra shudders. The Necroframe's pulse dims. You bind, not break. The city exhales—and keeps its wounded son."))
        elif which == "B":
            print("*** Ending B — Containment ***")
            print(wrap("The resin locks cold around the ritual; silver nails pin it to silence. Not mercy—but no more harm."))
        elif which == "C":
            print("*** Ending C — Obliteration ***")
            print(wrap("Dawn becomes a blade. Glass screams; resin chars. The ritual dies with a final, hollow breath."))
        else:
            print("*** Ending — Unknown ***")
        print("\nThanks for playing ‘Shadow Circuit: A Night in Austin’.")
        sys.exit(0)

# ---------- Command glue for GIVE / TOKEN INSERT / TUNE ----------
def main():
    g = Game()
    print("Type HELP for commands. Extra verbs: ENTER CODE ####, TRACE SIGIL, CRAFT COUNTER-INK, "
          "TUNE ANTENNA, INSERT TOKEN <WARD/FEATHER/SHADOW>, GIVE <item> TO <npc>")
    while True:
        if g.s.turn >= g.s.max_turns:
            g.lose("Sunrise licks the rooftops. Your story ends in ash and apology.")
        try:
            cmd = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodnight.")
            return
        if not cmd:
            continue
        low = cmd.lower()
        if low.startswith("give "):
            if " to " in low:
                lhs, rhs = low[5:].split(" to ",1)
                g.do_give(lhs.strip(), rhs.strip()); continue
        if low.startswith("insert token"):
            t = low.replace("insert token","",1).strip()
            if not t:
                print("Insert which token? (WARD / FEATHER / SHADOW)"); continue
            keymap = {"ward":"WARD_TOKEN","feather":"FEATHER_TOKEN","shadow":"SHADOW_TOKEN"}
            k = keymap.get(t.split()[0])
            if not k:
                print("Unknown token. Try WARD, FEATHER, or SHADOW."); continue
            g.insert_token(k); continue
        if low.startswith("tune antenna"):
            g.tune_antenna(); continue
        g.handle(cmd)

if __name__ == "__main__":
    main()
