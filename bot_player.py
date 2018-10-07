import model
import random
import rpcapi as api
import model
import log

player_address_dict = {}

def init_player_address():
    for x in range(10):
        account_name = "Player_{}".format(x)
        address = api.get_or_create_address(account_name)
        player_address_dict[account_name] = address
        print(account_name, address)


def get_player_address(_number):
    return player_address_dict.get("Player_{}".format(_number), None)


def get_player_balance(_number):
    address = get_player_address(_number)
    balance = api.get_address_balance(address)
    print(balance)
    return balance


def show_all_player_balance():
    for account in player_address_dict:
        address = player_address_dict[account]
        balance = api.get_address_balance(address)
        print(account, address, balance)


def choose_bet_level():
    return random.randint(1,3)


def choose_bet_amount(_min_bet_amount, _player_address):
    balance = api.get_address_balance(_player_address)
    if balance < 1:
        return -1

    if balance >= _min_bet_amount:
        return _min_bet_amount

    return balance


def take_small_bet(_player_number, _number, _amount):
    log.Info("Start Take Samll Bet ----------------")
    bet_address = model.get_small_bet_address_by_number(_number)
    player_address = get_player_address(_player_number)
    api.send(player_address, bet_address, _amount)
    log.Info("Small Bet Player_{} -> Number {}  Amount: {}".format(_player_number, _number, _amount))
    log.Info("End Take Samll Bet ----------------")


def take_big_bet(_player_number, _number, _amount):
    log.Info("Start Take Big Bet ----------------")
    bet_address = model.get_big_bet_address_by_number(_number)
    player_address = get_player_address(_player_number)
    api.send(player_address, bet_address, _amount)
    log.Info("Big Bet Player_{} -> Number {}  Amount: {}".format(_player_number, _number, _amount))
    log.Info("End Take Big Bet ----------------")


def take_rare_bet(_player_number, _number, _amount):
    log.Info("Start Take Rare Bet ----------------")
    bet_address = model.get_large_bet_address_by_number(_number)
    player_address = get_player_address(_player_number)
    api.send(player_address, bet_address, _amount)
    log.Info("Rare Bet Player_{} -> Number {}  Amount: {}".format(_player_number, _number, _amount))
    log.Info("End Take Rare Bet ----------------")


def send_balance_from_bank():
    send_dict = {}
    for account in player_address_dict:
        address = player_address_dict[account]
        send_dict[address] = 2300

    bank_address = api.get_or_create_address("bank")
    print(send_dict)
    api.send_to_many(bank_address, send_dict)


model.init_addresses()
init_player_address()

bank_balance = api.get_account_balance("bank")
print("Bank Balance: ", bank_balance)
print("Bank Address: ", api.get_or_create_address("bank"))

show_all_player_balance()

#send_balance_from_bank()

#take_small_bet(2, 2, 29)

#take_big_bet(7, 3, 51)
#take_big_bet(8, 3, 31)

#take_rare_bet(1,1,100)