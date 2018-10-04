import rpcapi as api
import time
import db
import util
import datetime
import viewupdator
import model


# bet_address_dict = {}  # account - address
# bet_address_number_dict = {}  # address - bet number

prev_block_height = -1
dev_reward_percentage = 0.05


def get_bet_address(_number, _bet_level):
    if _bet_level == 1:
        account_name = "{}{}".format(model.small_bet_account_name_prefix, _number)
        return model.small_bet_address_dict.get(account_name, None)
    if _bet_level == 2:
        account_name = "{}{}".format(model.big_bet_account_name_prefix, _number)
        return model.big_bet_address_dict.get(account_name, None)
    if _bet_level == 3:
        account_name = "{}{}".format(model.large_bet_account_name_prefix, _number)
        return model.large_bet_address_dict.get(account_name, None)




def step1_try_save_bet_list(_curr_block_height, _bet_level):
    bet_list = []

    if _bet_level == 1:
        bet_address_dict = model.small_bet_address_dict
        bet_address_number_dict = model.small_address_number_dict
    elif _bet_level == 2:
        bet_address_dict = model.big_bet_address_dict
        bet_address_number_dict = model.big_address_number_dict
    elif _bet_level == 3:
        bet_address_dict = model.large_bet_address_dict
        bet_address_number_dict = model.large_address_number_dict
    else:
        print("Error!, Wrong Diff Level: {}".format(_bet_level))
        return

    curr_game_round = db.get_curr_unsettle_game_round(_bet_level)

    for account_name in bet_address_dict:
        bet_address = bet_address_dict[account_name]
        unspent_list = api.get_unspent_list_by_address(bet_address)
        if len(unspent_list) > 0:
            for unspent in unspent_list:
                bet_data = {}

                bet_number = bet_address_number_dict.get(bet_address, None)
                if bet_number is None:
                    print("Fatal Error, get bet number error! {}".format(bet_address))
                    return

                unspent_txid = unspent["txid"]
                join_block_height, join_block_hash, join_block_timestamp = \
                    api.get_block_height_hash_timestamp_by_txid(unspent["txid"])

                if join_block_height == -1 or join_block_hash == -1 or join_block_timestamp == -1:
                    continue

                input_address_list = api.get_input_addresses(unspent_txid)
                if len(input_address_list) == 0:
                    print("Fatal Error, get input address faild! {}".format(unspent_txid))
                    return

                bet_data["join_txid"] = unspent_txid
                bet_data["join_block_height"] = join_block_height
                bet_data["join_block_hash"] = join_block_hash
                bet_data["join_block_timestamp"] = join_block_timestamp
                bet_data["bet_number"] = bet_number
                bet_data["bet_address"] = unspent["address"]
                bet_data["bet_amount"] = util.get_precision(float(unspent["amount"]), 8)
                bet_data["payment_address"] = input_address_list[0]
                bet_data["bet_level"] = _bet_level
                bet_data["bet_round"] = curr_game_round
                bet_data["created_at"] = util.timestamp2utctime(join_block_timestamp)

                bet_list.append(bet_data)
    db.save_new_bet_list(bet_list, _bet_level)


def step2_try_settle_bets(_curr_block_height, _bet_level):
    unsettle_bet_list = db.get_unsettle_bet_list(_bet_level)
    settled_game_round_list = []
    if unsettle_bet_list is None or len(unsettle_bet_list) == 0:
        return settled_game_round_list

    min_bet_amount = model.get_min_bet_amount(_bet_level)

    min_block_height = -1
    max_block_height = -1
    bet_dict = {}

    for bet in unsettle_bet_list:
        print("###############: ", bet.join_txid, bet.join_block_hash, bet.bet_number)
        if min_block_height < 0 or bet.join_block_height < min_block_height:
            min_block_height = bet.join_block_height

        if max_block_height < 0 or bet.join_block_height > max_block_height:
            max_block_height = bet.join_block_height

        bet_dict[bet.join_txid] = bet

    if _curr_block_height == min_block_height:
        return settled_game_round_list

    for block in range(min_block_height, _curr_block_height + 1):
        check_block = block + 1
        if check_block > _curr_block_height:
            break
        block_hash, block_nonce, block_timestamp = api.get_block_hash_nonce_timestamp_by_height(check_block)
        nonce_last_number = int(str(block_nonce)[-1])
        selected_bet_list = []
        has_loser = False
        has_winer = False
        print("Check Block: ", block, "Nonce: ", block_nonce)
        for txid in bet_dict:
            dbbet = bet_dict[txid]
            if dbbet.join_block_height < check_block:
                selected_bet_list.append(dbbet)
                if dbbet.bet_amount < min_bet_amount:
                    has_loser = True
                else:
                    if dbbet.bet_number == nonce_last_number:
                        has_winer = True
                    else:
                        has_loser = True

        print("Has winer: ", has_winer, "Has Loaser: ", has_loser)

        if has_winer and has_loser:
            winer_list = []
            loser_list = []
            total_loser_amount = 0.0
            total_winer_amount = 0.0
            for dbbet in selected_bet_list:
                if dbbet.bet_number == nonce_last_number:
                    winer_list.append(dbbet)
                    total_winer_amount += dbbet.bet_amount
                    dbbet.bet_state = 1
                else:
                    loser_list.append(dbbet)
                    total_loser_amount += dbbet.bet_amount
                    dbbet.bet_state = 0

                dbbet.settlement_block_height = check_block
                dbbet.settlement_block_hash = block_hash
                dbbet.settlement_block_nonce = block_nonce

                del bet_dict[dbbet.join_txid]

            print("Winer Count: ", len(winer_list), "Loser Count: ", len(loser_list))
            print("Total winer amount: ", total_winer_amount, "Total loser amount: ", total_loser_amount)
            total_reward = total_loser_amount * (1 - dev_reward_percentage)
            total_reward = util.get_precision(total_reward, 8)
            dev_reward = total_loser_amount - total_reward
            print("Total winer reward: ", total_reward, "dev reward: ", dev_reward)

            pay_input_txid_list = []
            to_dict = {}
            # pay to winers
            for dbbet in winer_list:
                reward_percentage = dbbet.bet_amount / total_winer_amount
                reward_percentage = util.get_precision(reward_percentage, 3)
                reward_amount = total_reward * reward_percentage
                reward_amount = util.get_precision(reward_amount, 8)
                dbbet.reward_amount = reward_amount
                pay_amount = reward_amount + dbbet.bet_amount
                pay_amount = util.get_precision(pay_amount, 8)
                to_dict[dbbet.payment_address] = pay_amount
                pay_input_txid_list.append(dbbet.join_txid)
                print("Txid: ", dbbet.join_txid, "bet amount: ", dbbet.bet_amount, "reward %: ", reward_percentage,
                      "reward: ", reward_amount, "payment: ", pay_amount)

            for dbbet in loser_list:
                pay_input_txid_list.append(dbbet.join_txid)

            pay_reward_txid = api.send_to_many_from_input_txid_list(pay_input_txid_list, to_dict, model.dev_reward_address)

            if pay_reward_txid == -1:
                print("Error! Payment Faild!")

            settled_bet_list = []
            for dbbet in winer_list:
                dbbet.payment_state = 1
                dbbet.reward_txid = pay_reward_txid
                dbbet.update_at = datetime.datetime.now()
                settled_bet_list.append(dbbet)
                print("Winer: ", dbbet.join_txid, "Join Height: ", dbbet.join_block_height, "address: ",
                      dbbet.payment_address, "bet number: ", dbbet.bet_number)

            for dbbet in loser_list:
                dbbet.update_at = datetime.datetime.now()
                settled_bet_list.append(dbbet)
                print("Loser: ", dbbet.join_txid, "Join Height: ", dbbet.join_block_height, "address: ",
                      dbbet.payment_address, "bet number: ", dbbet.bet_number, "Bet Amount: ", dbbet.bet_amount)

            # last_game_round = db.get_last_game_round_number(_bet_level)
            curr_game_round = db.get_curr_unsettle_game_round(_bet_level)
            settled_game_round_list.append(curr_game_round)

            min_join_block = -1
            max_join_block = -1
            for dbbet in settled_bet_list:
                dbbet.game_round = curr_game_round
                if min_join_block < 0 or dbbet.join_block_height < min_join_block:
                    min_join_block = dbbet.join_block_height
                if max_join_block < 0 or dbbet.join_block_height > max_join_block:
                    max_join_block = dbbet.join_block_height

            db.save_settlement_bet_list(settled_bet_list)
            db.save_settled_header_data(
                curr_game_round,
                nonce_last_number,
                _bet_level,
                len(settled_bet_list),
                len(winer_list),
                len(loser_list),
                total_winer_amount + total_loser_amount,
                total_loser_amount,
                dev_reward,
                min_join_block,
                check_block,
                block_nonce,
            )
    return settled_game_round_list


def on_block_height_changed(_curr_block_height):
    print("On Block Height Changed: ", _curr_block_height)
    step1_try_save_bet_list(_curr_block_height, 1)
    small_settled_game_round_list = step2_try_settle_bets(_curr_block_height, 1)

    step1_try_save_bet_list(_curr_block_height, 2)
    big_settled_game_round_list = step2_try_settle_bets(_curr_block_height, 2)

    step1_try_save_bet_list(_curr_block_height, 3)
    large_settled_game_round_list = step2_try_settle_bets(_curr_block_height, 3)

    viewupdator.update_view(small_settled_game_round_list, big_settled_game_round_list, large_settled_game_round_list)


def game_loop():
    global prev_block_height
    while True:
        # try:
        curr_block_height = api.get_current_block_height()
        print("Current Block Height: {} {}".format(curr_block_height, int(time.time())))
        if curr_block_height != prev_block_height:
            prev_block_height = curr_block_height
            on_block_height_changed(curr_block_height)
        time.sleep(1)


model.init_addresses()
db.init_db()
game_loop()

