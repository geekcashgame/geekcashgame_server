import rpcapi as api

dev_reward_account = "dev_reward"
small_bet_account_name_prefix = "small_bet_"
big_bet_account_name_prefix = "big_bet_"
large_bet_account_name_prefix = "large_bet_"
small_bet_address_dict = {}
small_address_number_dict = {}
small_number_address_dict = {}
big_bet_address_dict = {}
big_address_number_dict = {}
big_number_address_dict = {}
large_bet_address_dict = {}
large_address_number_dict = {}
large_number_address_dict = {}

dev_reward_address = "GTDC6VoAALQtEra9n5tNu41PogPTojkqg2"

bet_level_min_amount_dict = {
    1: 1000,
    2: 10000,
    3: 100000,
}


def init_addresses():
    #global dev_reward_address
    global small_bet_address_dict, small_address_number_dict, small_number_address_dict
    global big_bet_address_dict, big_address_number_dict, big_number_address_dict
    global large_bet_address_dict, large_address_number_dict, large_number_address_dict
    #dev_reward_address = api.get_or_create_address(dev_reward_account)
    # init small addresses
    for x in range(10):
        account_name = "{}{}".format(small_bet_account_name_prefix, x)
        address = api.get_or_create_address(account_name)
        small_bet_address_dict[account_name] = address
        small_address_number_dict[address] = x
        small_number_address_dict[x] = address

    # init big addresses
    for x in range(10):
        account_name = "{}{}".format(big_bet_account_name_prefix, x)
        address = api.get_or_create_address(account_name)
        big_bet_address_dict[account_name] = address
        big_address_number_dict[address] = x
        big_number_address_dict[x] = address

    # init large addresses
    for x in range(10):
        account_name = "{}{}".format(large_bet_account_name_prefix, x)
        address = api.get_or_create_address(account_name)
        large_bet_address_dict[account_name] = address
        large_address_number_dict[address] = x
        large_number_address_dict[x] = address



def get_small_bet_address_by_number(_number):
    account_name = "{}{}".format(small_bet_account_name_prefix, _number)
    return small_bet_address_dict.get(account_name, None)


def get_big_bet_address_by_number(_number):
    account_name = "{}{}".format(big_bet_account_name_prefix, _number)
    return big_bet_address_dict.get(account_name, None)


def get_large_bet_address_by_number(_number):
    account_name = "{}{}".format(large_bet_account_name_prefix, _number)
    return large_bet_address_dict.get(account_name, None)


def get_min_bet_amount(_bet_level):
    return bet_level_min_amount_dict.get(_bet_level, 1000)


def get_bet_address(_bet_level, _bet_number):
    if _bet_level == 1:
        return get_small_bet_address_by_number(_bet_number)
    elif _bet_level == 2:
        return get_big_bet_address_by_number(_bet_number)
    elif _bet_level == 3:
        return get_large_bet_address_by_number(_bet_number)
    return None