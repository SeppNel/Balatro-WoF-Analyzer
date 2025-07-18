from bot import Bot, Actions
import time
import types
import subprocess
import os
import signal

#STATS
WOF_USES = 0
WOF_HITS = 0
RUNS = 0

#CONTROL
RUN_FINISHED = False
BLINDS_PLAYED = 0
SHOP_ACTIONS = 0


def play_flushes(G):
    suit_count = {
        "Hearts": 0,
        "Diamonds": 0,
        "Clubs": 0,
        "Spades": 0,
    }
    for card in G["hand"]:
        suit_count[card["suit"]] += 1

    most_common_suit = max(suit_count, key=suit_count.get)
    most_common_suit_count = suit_count[most_common_suit]
    if most_common_suit_count >= 5:
        flush_cards = []
        for card in G["hand"]:
            if card["suit"] == most_common_suit:
                flush_cards.append(card)
        flush_cards.sort(key=lambda x: x["value"], reverse=True)
        return [Actions.PLAY_HAND, [G["hand"].index(card) + 1 for card in flush_cards[:5]],]

    # We don't have a flush, so we discard up to 5 cards that are not of the most common suit
    discards = []
    for card in G["hand"]:
        if card["suit"] != most_common_suit:
            discards.append(card)
    discards.sort(key=lambda x: x["value"], reverse=True)
    discards = discards[:5]
    if len(discards) > 0:
        if G["current_round"]["discards_left"] > 0:
            action = Actions.DISCARD_HAND
        else:
            action = Actions.PLAY_HAND
        return [action, [G["hand"].index(card) + 1 for card in discards]]

    print("Somehow don't have a flush, but also don't have any cards to discard. Playing the first card")
    return [Actions.PLAY_HAND, [1]]


def skip_or_select_blind(self, G):
    global RUN_FINISHED, BLINDS_PLAYED, SHOP_ACTIONS, RUNS, WOF_USES, WOF_HITS

    if RUN_FINISHED and G["round"] == 0:
        RUNS += 1
        print("--------------------")
        print(f"|     Run {RUNS}        |")
        print("--------------------")
        print(f"WOF Uses = {WOF_USES}")
        print(f"WOF Hits = {WOF_HITS}")
        if WOF_USES > 0:
            print(f"WOF Chance = {WOF_HITS / WOF_USES * 100}%")

        RUN_FINISHED = False
        BLINDS_PLAYED = 0
        SHOP_ACTIONS = 0
    
    BLINDS_PLAYED += 1
    return [Actions.SELECT_BLIND]


def select_cards_from_hand(self, G):
    global RUN_FINISHED
    # G["hand"] is a list of cards in the hand

    # Cards have:
    # a label e.g. base_card
    # a name e.g. 3 of Hearts
    # a suit e.g. Hearts
    # a value e.g. 3
    # a card_key e.g. H_3

    # Example of playing the first card in the hand
    # return [Actions.PLAY_HAND, [1]]

    # Example of discarding the first card in the hand
    # return [Actions.DISCARD_HAND, [1]]

    if RUN_FINISHED:
        return [Actions.PLAY_HAND, [6]]

    return play_flushes(G)


def select_shop_action(self, G):
    global WOF_HITS, RUN_FINISHED, WOF_USES, SHOP_ACTIONS

    action = Actions.END_SHOP
    params = []
    if SHOP_ACTIONS == 0:
        wof_found = False
        for card in G["shop"]["cards"]:
            if card["label"] == "The Wheel of Fortune":
                wof_found = True

        if wof_found:
            action = Actions.BUY_BOOSTER
            params = [1]
        else:
            SHOP_ACTIONS = 100 # If no WoF just skip everything
            RUN_FINISHED = True

    elif SHOP_ACTIONS == 1:
        wof_found = False
        wof_index = None
        i = 1
        for card in G["shop"]["cards"]:
            if card["label"] == "The Wheel of Fortune":
                wof_index = i
                wof_found = True
                i += 1
        
        if wof_found and len(G["jokers"]) > 0:
            WOF_USES += 1
            action = Actions.BUY_CARD
            params = [wof_index]

    elif SHOP_ACTIONS == 2:
        # Checking for WoF hit
        for joker in G["jokers"]:
            if "edition" in joker:
                WOF_HITS += 1
        RUN_FINISHED = True
    
    SHOP_ACTIONS += 1
    return [action, params]


def select_booster_action(self, G):
    i = 1
    for joker in G["shop"]["pertu"]:
        if "edition" not in joker:
            return [Actions.SELECT_BOOSTER_CARD, [i]]
        i += 1
    return [Actions.SKIP_BOOSTER_PACK, []]


def sell_jokers(self, G):
    return [Actions.SELL_JOKER, []]


def rearrange_jokers(self, G):
    return [Actions.REARRANGE_JOKERS, []]


def use_or_sell_consumables(self, G):
    return [Actions.USE_CONSUMABLE, []]


def rearrange_consumables(self, G):
    return [Actions.REARRANGE_CONSUMABLES, []]


def rearrange_hand(self, G):
    return [Actions.REARRANGE_HAND, []]

def start_balatro_instance2(self):
    bottles_cli = "flatpak run --command=bottles-cli com.usebottles.bottles"
    start_command = bottles_cli + " run -b Babot -p Balatro"
    self.balatro_instance = subprocess.Popen(
        [start_command, str(self.bot_port)], shell=True
    )

def stop_balatro_instance2(self):
    if self.balatro_instance:
        self.balatro_instance.kill()


def start_balatro_instance(self):
    bottles_cli = "flatpak run --command=bottles-cli com.usebottles.bottles"
    start_command = bottles_cli + " run -b Babot -p Balatro"
    self.balatro_instance = subprocess.Popen(
        [start_command, str(self.bot_port)],
        shell=True,
        preexec_fn=os.setsid  # Start in new process group
    )
    time.sleep(10)

def stop_balatro_instance(self):
    if self.balatro_instance:
        try:
            os.killpg(os.getpgid(self.balatro_instance.pid), signal.SIGTERM)
            print(f"Killed process group {os.getpgid(self.balatro_instance.pid)}")
            time.sleep(2)
        except ProcessLookupError:
            print("Process already exited.")
        self.balatro_instance = None

def restart(self):
    self.stop_balatro_instance()
    self.start_balatro_instance()
    
    RUN_FINISHED = False
    BLINDS_PLAYED = 0
    SHOP_ACTIONS = 0
    mybot.running = True


if __name__ == "__main__":
    mybot = Bot(deck="Plasma Deck", stake=1)
    mybot.running = True
    mybot.restartOnError = True

    mybot.skip_or_select_blind = skip_or_select_blind
    mybot.select_cards_from_hand = select_cards_from_hand
    mybot.select_shop_action = select_shop_action
    mybot.select_booster_action = select_booster_action
    mybot.sell_jokers = sell_jokers
    mybot.rearrange_jokers = rearrange_jokers
    mybot.use_or_sell_consumables = use_or_sell_consumables
    mybot.rearrange_consumables = rearrange_consumables
    mybot.rearrange_hand = rearrange_hand

    mybot.restart = types.MethodType(restart, mybot)
    mybot.start_balatro_instance = types.MethodType(start_balatro_instance, mybot)
    mybot.stop_balatro_instance = types.MethodType(stop_balatro_instance, mybot)

    mybot.start_balatro_instance()
    mybot.run()
