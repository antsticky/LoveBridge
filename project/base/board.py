from enum import Enum
from os import stat

from project.base.card import Card, CardSuit, CardValue
from project.base.deck import Deck, SUIT_LIST, CARD_VALUE_LIST
from project.base.bid import BidsClass, Bid, BidSuit
from project.base.people import TablePlayers
from project.base.seats import SeatDirections


class PhaseClass(Enum):
    NEW = "NEW"
    BID = "BID"
    PLAY = "PLAY"
    END = "END"
    ABORTED = "ABORTED"


class Board:
    def __init__(self, board_nb, dealer):
        self.board_nb = board_nb  # board number
        self.dealer = SeatDirections[dealer]  # the player who starts
        self.phase = PhaseClass.NEW  # identificate the phase of the game NEW/BID/PLAY/END or ABORTED
        # TODO: feed this for bidding and playing
        self.active_player = SeatDirections[dealer]

        self.players = None  # players must be seat first
        self.deck = None  # must be deal first

        self.bids = BidsClass(dealer=self.dealer, callbacks={"board_contract": self.set_contract, "set_phase": self.set_phase, "increase_active_player": self.increase_active_player})
        self._contract = None  # bid first
        self.dds = None  # bid first

        self.tricks = None  # dict of {"N": [3, 4, 5], "E", "..."} where value gives then
        self.plays = []

        #TODO: isvul ["NONVUL", "VUL"] set by board number
        
        self.claim = None

    @property
    def contract(self):
        if self._contract is None:
            raise ValueError("Do bidding first")

        return self._contract

    @contract.setter
    def contract(self, contr):
        self.set_contract(contr)

    def set_contract(self, value):
        self._contract = value

    def set_phase(self, key):
        self.phase = PhaseClass(key)

    def increase_active_player(self, seat):
        if seat.value == 4:
            self.active_player = SeatDirections(1)
        else:
            self.active_player = SeatDirections(seat.value + 1)

    @staticmethod
    def get_active_player_by_trick(tricks, trump):
        lead_suit = tricks[0][1].suit
        key_suits = [lead_suit] if trump == BidSuit.from_str("NT") else [lead_suit, trump]
        my_trump = trump if trump != BidSuit.from_str("NT") else None

        player_won = tricks[0][0]
        card_won = tricks[0][1]
        
        for player, card in tricks:
            if card.suit in key_suits:
                if card_won.suit == card.suit:
                    if card_won.value < card.value:
                        card_won = card
                        player_won = player
                elif (my_trump is not None) and card.suit == trump:
                    card_won = card
                    player_won = player



        return player_won

    def deal(self):
        if self.phase == PhaseClass.NEW:
            self.deck = Deck.shuffle()
            self.set_phase("BID")
        else:
            print("Deal was alredy made, please use redeal")

    def load_deck(self, file_name, line_idx=0):
        self.deck = Deck.load(file_name=file_name, line_idx=line_idx)
        self.phase = PhaseClass.BID
        # TODO make reset actions when go back in phase function(cur_phase, new_phase)

    def redeal(self):
        # TODO: Implement this
        raise NotImplementedError("NOT implemented")

    def seating(self, N, S, E, W):
        self.players = TablePlayers(N=N, S=S, E=E, W=W)

    def bid(self, bid, seat):
        if self.active_player != SeatDirections[seat]:
            print("It is not your turn")
        elif self.phase == PhaseClass.BID:
            self.bids.bidding(Bid(bid), SeatDirections[seat])
        elif self.phase == PhaseClass.NEW:
            print("Deal first")
        else:
            print("Bidding was already made")

    def play(self, card, seat):
        if self.active_player != SeatDirections[seat]:
            print("It is not your turn")
        elif self.phase == PhaseClass.PLAY:
            player = SeatDirections[seat]
            suit = CardSuit(list(filter(lambda x: x[0].upper() == card[0].upper(), SUIT_LIST))[0])
            value = list(filter(lambda x: x.display_name.upper() == card[1:].upper(), CARD_VALUE_LIST))[0]
            played_card = Card(suit, value)

            player_hand = getattr(self.deck, player.name)
            player_suit_cards = player_hand[suit]

            if played_card not in player_suit_cards:
                print(f"Player {seat} does not holds the given card ({card})")
                return -1
            elif list(filter(lambda x: x == played_card, player_suit_cards))[0].played:
                print(f"The card {card} is already played")
                return -1

            list(filter(lambda x: x == played_card, player_suit_cards))[0].played = True
            self.plays.append((player, played_card))
            
            if len(self.plays) % 4 != 0:
                self.increase_active_player(player)
            else:
                tricks = self.plays[-4:]
                self.active_player = self.get_active_player_by_trick(tricks, self.contract.bid.suit)

            print(f"{player.name} {played_card.suit.short_name}{played_card.value.display_name} {self.active_player.name}")

        else:
            # TODO: be more concrete
            print("Not bidding phase...")