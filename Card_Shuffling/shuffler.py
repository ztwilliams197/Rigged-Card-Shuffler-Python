import os
import random
import sys

ranks = ["A","2","3","4","5","6","7","8","9","X","J","Q","K"]
suits = ["C","H","S","D"]

def gen_card_list():
    cards = []
    for rank in ranks:
        for suit in suits:
            cards.append((rank,suit))
    
    return cards

def shuffle_cards(cards):
    for i in range(len(cards)):
        j = random.randint(0,i)
        if i != j:
            temp = cards[i]
            cards[i] = cards[j]
            cards[j] = temp
    return cards

def read_order(filepath):
    with open(filepath,"r") as file:
        data = file.read()
        data = data.split(";")
        data = [card.split(",") for card in data]
        return  data

def shuffle_deck(cards):
    deck = gen_card_list()
    known_cards = [(card[0],card[1]) for card in cards]
    #print(known_cards)
    for card in known_cards:
        if card in deck:
            deck.remove(card)
    deck = shuffle_cards(deck)
    for card in cards:
    #    print(card)
        deck.insert(int(card[2]),(card[0],card[1]))
    return deck

def write_to_file(file, cards):
    written = []
    for i in range(52):
        if ((cards[i][0],cards[i][1]) in written):
            print("This should never happen")
        file.write(cards[i][0]+","+cards[i][1]+","+str(i))
        written.append((cards[i][0],cards[i][1]))
        if i != 52 - 1:
            file.write(";")

def main():
    '''
        main()
        params:
            input file str
            output file
    '''
    
    if (len(sys.argv) != 3):
        print("incorrect argument number\nFormat: python fixture_generator.py filenename num_spec_cards")
        return
    
    in_file = sys.argv[1]
    out_file = sys.argv[2]
    
    with open(os.path.join(out_file),"w") as output:
        write_to_file(output,shuffle_deck(read_order(in_file)))

if __name__ == "__main__":
    main()