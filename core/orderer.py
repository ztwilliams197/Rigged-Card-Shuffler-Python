from abc import ABC, abstractmethod
from typing import List, Any, Dict
from identify_card import Card


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
                _impl = _BlackJackGenerator()
            else:
                assert False, f"Unrecognized game: {value}"

    @staticmethod
    def generate_order() -> Dict[Card, int]:
        # noinspection PyProtectedMember
        return OrderGenerator._impl._generate_order()

    @abstractmethod
    def _generate_order(self) -> Dict[Card, int]:
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

    def _generate_order(self) -> Dict[Card, int]:
        pass
