import random
from typing import Tuple, List, Set, TypeVar

ranks = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "X", "J", "Q", "K"]
suits = ["C", "H", "S", "D"]

Card = Tuple[str, str]  # (rank, suit)
T = TypeVar('T')


def gen_card_list() -> List[Card]:
    cards = []
    for rank in ranks:
        for suit in suits:
            cards.append((rank, suit))
    return cards


# noinspection PyShadowingBuiltins
def shuffle(list: List[T]) -> List[T]:
    for i in range(len(list)):
        j = random.randrange(i, len(list))
        if i != j:
            list[i], list[j] = list[j], list[i]
    return list


def read_order(filepath: str) -> Set[Tuple[Card, int]]:
    with open(filepath, "r") as file:
        data = [card.split(",") for card in file.read().split(";")]
        ret = set(((rank, suit), int(pos)) for rank, suit, pos in data)
        check = set(card for card, _ in ret)
        assert len(check) == len(ret), f"Card order specifier (in file {filepath}) had duplicate cards..."
        return ret


def compute_shuffled_deck(card_spec: Set[Tuple[Card, int]], *, verbose: bool = False) -> List[Card]:
    deck = set(gen_card_list())
    known_cards = set(card for card, _ in card_spec)
    assert len(known_cards) == len(card_spec), "Card order specification had duplicate cards"
    deck = shuffle(list(deck.difference(known_cards)))

    if verbose:
        print(deck)

    card_spec_ordered = list(card_spec)
    card_spec_ordered.sort(key=lambda spec: spec[1])
    for card, pos in card_spec_ordered:
        if verbose:
            print(f"Card {card} into pos {pos}")
        deck.insert(pos, card)

    return deck


def generate_arbitrary_specification(filepath: str, num_cards_to_spec: int) -> None:
    with open(filepath, "w") as file:
        deck = shuffle(gen_card_list())[:num_cards_to_spec]
        positions = shuffle([p for p in range(52)])[:num_cards_to_spec]
        file.write(';'.join(f"{card[0]},{card[1]},{pos}" for card, pos in zip(deck, positions)))


if __name__ == "__main__":
    # for i in [5, 10, 15, 20, 40, 52]:
    #     generate_arbitrary_specification(f"./card_specs/card_spec{i}.txt", i)
    order = read_order("./card_specs/card_spec5.txt")
    shuffled = compute_shuffled_deck(order, verbose=True)
    print(shuffled)
