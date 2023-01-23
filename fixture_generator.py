import sys
import os
import random

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

def write_fixture(file, cards, num_cards):
    used = []
    for i in range(num_cards):
        rand = random.randint(0,len(cards)-1)
        while(rand in used):
            rand = random.randint(0,len(cards)-1)
        file.write(cards[rand][0]+","+cards[rand][1]+","+str(rand))
        if i != num_cards - 1:
            file.write(";")

def main():
    '''
        main()
        params:
            Filename str
            number of specified cards
    '''
    
    if (len(sys.argv) != 3):
        print("incorrect argument number\nFormat: python fixture_generator.py filenename num_spec_cards")
        return
    
    filename = sys.argv[1]
    num_spec_cards = int(sys.argv[2])
    
    with open(os.path.join("Data",filename),"w") as file:
        write_fixture(file,shuffle_cards(gen_card_list()),num_spec_cards)
    

if __name__ == "__main__":
    main()