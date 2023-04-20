from abc import ABC, abstractmethod
from typing import List, Any, Dict, TypeVar
import random

from identify_card import Card

_ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K"]
_suits = ["C", "H", "S", "D"]

_T = TypeVar('_T')


def _gen_card_list() -> List[Card]:
    cards = []
    for rank in _ranks:
        for suit in _suits:
            cards.append((rank, suit))
    return cards


# noinspection PyShadowingBuiltins
def _shuffle(list: List[_T]) -> List[_T]:
    for i in range(len(list)):
        j = random.randrange(i, len(list))
        if i != j:
            list[i], list[j] = list[j], list[i]
    return list


def _compute_shuffled_deck(card_spec: Dict[Card, int], *, verbose: bool = False) -> Dict[Card, int]:
    deck = set(_gen_card_list())
    known_cards = set(card_spec)
    deck = _shuffle(list(deck.difference(known_cards)))

    if verbose:
        print(deck)

    card_spec_ordered = list((card, pos) for card, pos in card_spec.items())
    card_spec_ordered.sort(key=lambda spec: spec[1])
    for card, pos in card_spec_ordered:
        if verbose:
            print(f"Placed card {card} into pos {pos}")
        deck.insert(pos, card)

    return {card: pos for pos, card in enumerate(deck)}


class OrderGenerator(ABC):
    _impl: Any = None

    @staticmethod
    def reconfigure(key: str, value: str) -> None:
        if key != "game":
            # noinspection PyProtectedMember
            OrderGenerator._impl._reconfigure(key, value)
        else:
            # switch/case for different game handlers
            if value == 'blackjack':
                OrderGenerator._impl = _BlackJackGenerator()
            elif value == 'none' or value == 'random' or value == 'shuffle':
                OrderGenerator._impl = _RandomShuffleGenerator()
            else:
                assert False, f"Unrecognized game: {value}"

    @staticmethod
    def generate_order() -> Dict[Card, int]:
        # noinspection PyProtectedMember
        return _compute_shuffled_deck(OrderGenerator._impl._generate_order())

    @abstractmethod
    def _generate_fixed_points(self) -> Dict[Card, int]:
        pass

    @abstractmethod
    def _reconfigure(self, key: str, value: str) -> None:
        pass


class _BlackJackGenerator(OrderGenerator):
    num_players: int
    winners: List[bool]
    dealer_wins: bool

    def __init__(self):
        self.num_players = 0
        self.winners = []
        self.dealer_wins = False

    def _reconfigure(self, key: str, value: str) -> None:
        if key == 'num_players':
            num_players = int(value)
            if num_players < self.num_players:
                self.winners = self.winners[:num_players]
            elif num_players > self.num_players:
                self.winners += [False] * (num_players - self.num_players)
            self.num_players = num_players
        elif key == 'winner':
            if value == 'dealer':
                self.dealer_wins = True
                self.winners = [False] * self.num_players
            elif value == 'table':
                self.dealer_wins = False
                self.winners = [True] * self.num_players
            else:
                # value = 'player #'
                assert value[:7] == "player ", "Invalid winner config message format"
                player = int(value[7:])
                assert 0 <= player < self.num_players, "Invalid player number for winner config"
                self.dealer_wins = False
                self.winners[player] = True
        else:
            assert False, f"Unrecognized config key {key}"

    def _generate_fixed_points(self) -> Dict[Card, int]:
        pass


class _RandomShuffleGenerator(OrderGenerator):
    fixed_points: Dict[Card, int]

    def __init__(self):
        self.fixed_points = {}

    def _reconfigure(self, key: str, value: str) -> None:
        # (R,S)
        rank, suit = key.split(',')
        card = rank[1:], suit[:-1]
        self.fixed_points[card] = int(value)
        # TODO error checking

    def _generate_fixed_points(self) -> Dict[Card, int]:
        return self.fixed_points


OrderGenerator._impl = _RandomShuffleGenerator()
