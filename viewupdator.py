"""
1. 主页（三个页面，small, big, large）
2. 规则页面（1个页面）
3. 所有历史游戏界面（列表形式，每轮游戏一行，只包含具体页面的页头信息）（三个页面，small, big, large)
4. 每轮游戏具体页面（每轮游戏一个页面，small, big, large 显示在同一个页面
5. 当前游戏下注页面（未结算的）
"""

import db
import model
import json
import util
import os
import threading
import log

is_release = True


if is_release:
    html_root = "../geekcashgame.github.io/"
else:
    html_root = "/Users/Fred/Documents/html/"


def get_index_json_file():
    return "{}{}.json".format(html_root, "index")


def get_bets_json_file(_bet_level, _bet_round):
    dir = ""
    if _bet_level == 1:
        dir = "small/"
    if _bet_level == 2:
        dir = "big/"
    if _bet_level == 3:
        dir = "rare/"

    return "{}{}{}.json".format(html_root, dir,_bet_round)


def get_history_json_file(_bet_level):
    if _bet_level == 1:
        return "{}{}.json".format(html_root, "small_history")
    if _bet_level == 2:
        return "{}{}.json".format(html_root, "big_history")
    if _bet_level == 3:
        return "{}{}.json".format(html_root, "rare_history")

class BetAddress(object):
    def __init__(self, _bet_level, _number):
        self.number = _number
        self.address = model.get_bet_address(_bet_level, self.number)
        self.total_bet_count = db.get_total_unsettle_bet_count(_bet_level, self.number) #db.get_total_bet_count(_bet_level, self.number)
        self.total_bet_amount = db.get_total_unsettle_bet_amount(_bet_level, self.number) #db.get_total_bet_amount(_bet_level, self.number)
        self.total_win_count = db.get_bet_number_total_win_count(_bet_level, self.number)

    def get_json_obj(self):
        return {
            "number": self.number,
            "address": self.address,
            "total_bet_count": self.total_bet_count,
            "total_bet_amount": self.total_bet_amount,
            "total_win_count": self.total_win_count,
        }


class CurrBetInfo(object):
    def __init__(self, _bet_level):
        self.round = db.get_curr_unsettle_game_round(_bet_level)
        self.bet_count = db.get_curr_unsettle_count(_bet_level)
        self.bet_amount = db.get_curr_unsettle_amount(_bet_level)

    def get_json_obj(self):
        return {
            "round": self.round,
            "bet_count": self.bet_count,
            "bet_amount": util.get_precision(self.bet_amount, 2),
        }


class SettledBetInfo(object):
    def __init__(self, _bet_level):
        self.round = db.get_last_game_round_number(_bet_level)
        self.bet_count = 0
        self.bet_amount = 0
        self.winner_count = 0
        self.loser_count = 0
        self.total_reward = 0
        self.bet_number = -1

        if self.round > 0:
            bet_round_data = db.get_bet_round_data(_bet_level, self.round)
            if bet_round_data is not None:
                self.bet_count = bet_round_data.bet_count
                self.bet_amount = bet_round_data.total_bet_amount
                self.winner_count = bet_round_data.winner_count
                self.loser_count = bet_round_data.loser_count
                self.total_reward = bet_round_data.total_reward
                self.bet_number = bet_round_data.bet_number

    def get_json_obj(self):
        return {
            "round": self.round,
            "bet_count": self.bet_count,
            "bet_amount": self.bet_amount,
            "winner_count": self.winner_count,
            "loser_count": self.loser_count,
            "total_reward": self.total_reward,
            "bet_number": self.bet_number,
        }


class UnSettleBet(object):
    def __init__(self,
                 _join_txid,
                 _join_block,
                 _bet_round,
                 _bet_level,
                 _bet_number,
                 _bet_amount,
                 _player_address,
                 _join_time):
        self.short_txid = _join_txid[:10] + "..."
        self.txid = _join_txid
        self.join_block = _join_block
        self.short_txid_link_to = ""
        self.bet_round = _bet_round
        self.bet_level = _bet_level
        self.bet_number = _bet_number
        self.bet_amount = util.get_precision(_bet_amount,2)
        self.player_address = _player_address
        self.join_time = _join_time

    def get_json_obj(self):
        return {
            "short_txid": self.short_txid,
            "txid": self.txid,
            "join_block": self.join_block,
            "short_txid_link_to": self.short_txid_link_to,
            "bet_round": self.bet_round,
            "bet_level": self.bet_level,
            "bet_number": self.bet_number,
            "bet_amount": self.bet_amount,
            "player_address": self.player_address,
            "join_time": self.join_time,
        }


class SettledBet(object):
    def __init__(self,
                 _join_txid,
                 _join_block,
                 _settled_block,
                 _bet_round,
                 _bet_level,
                 _bet_number,
                 _bet_amount,
                 _bet_reward,
                 _bet_state,
                 _player_address,
                 _join_time,
                 _payment_txid):
        self.txid = _join_txid
        self.short_txid = _join_txid[:10] + "..."
        self.join_block = _join_block
        self.settled_block = _settled_block
        self.short_txid_link_to = ""
        self.bet_round = _bet_round
        self.bet_level = _bet_level
        self.bet_number = _bet_number
        self.bet_amount = util.get_precision(_bet_amount,2)
        self.bet_reward = util.get_precision(_bet_reward,2)
        self.bet_state = _bet_state
        self.player_address = _player_address
        self.join_time = _join_time
        self.payment_txid = _payment_txid
        if self.payment_txid == "":
            self.short_payment_txid = "-"
        else:
            self.short_payment_txid = self.payment_txid[:10] + "..."

        if self.bet_state == 1:
            self.bet_reward += self.bet_amount
        else:
            self.bet_reward = -self.bet_amount

    def get_json_obj(self):
        return {
            "txid":self.txid,
            "short_txid": self.short_txid,
            "join_block": self.join_block,
            "settled_block": self.settled_block,
            "short_txid_link_to": self.short_txid_link_to,
            "bet_round": self.bet_round,
            "bet_level": self.bet_level,
            "bet_number": self.bet_number,
            "bet_amount": self.bet_amount,
            "bet_reward": self.bet_reward,
            "player_address": self.player_address,
            "join_time": self.join_time,
            "payment_txid": self.payment_txid,
            "short_payment_txid":self.short_payment_txid,
        }


class BetLevel(object):
    def __init__(self, _bet_level):
        self.addresses = []
        self.min_bet_amount = model.get_min_bet_amount(_bet_level)
        self.curr_bet_info = CurrBetInfo(_bet_level)
        self.prev_bet_info = SettledBetInfo(_bet_level)
        self.recently_winners = []
        self.init_addresses(_bet_level)
        self.init_recently_winners(_bet_level)

    def get_json_obj(self):
        return {
            "addresses": self.addresses,
            "min_bet_amount": self.min_bet_amount,
            "curr_bet_info": self.curr_bet_info.get_json_obj(),
            "prev_bet_info": self.prev_bet_info.get_json_obj(),
            "recently_winners": self.recently_winners,
        }

    def init_addresses(self, _bet_level):
        for x in range(10):
            self.addresses.append(BetAddress(_bet_level, x).get_json_obj())

    def init_recently_winners(self, _bet_level):
        bet_list = db.get_recently_winner_list(_bet_level, 7)
        for bet in bet_list:
            settledbet = SettledBet(
                bet.join_txid,
                bet.join_block_height,
                bet.settlement_block_height,
                bet.game_round,
                bet.bet_level,
                bet.bet_number,
                util.get_precision(bet.bet_amount,2),
                util.get_precision(bet.reward_amount,2),
                bet.bet_state,
                bet.payment_address,
                bet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                bet.reward_txid,
            )
            self.recently_winners.append(settledbet.get_json_obj())


class PageIndex(object):
    def __init__(self):
        self.small_bets = BetLevel(1).get_json_obj()
        self.big_bets = BetLevel(2).get_json_obj()
        self.large_bets = BetLevel(3).get_json_obj()
        self.recently_unsettle_bets = []
        self.recently_settled_bets = []
        self.init_recently_settled_bets()
        self.init_recently_unsettle_bets()

    def get_json_obj(self):
        return {
            "small_bets": self.small_bets,
            "big_bets": self.big_bets,
            "large_bets": self.large_bets,
            "recently_unsettle_bets": self.recently_unsettle_bets,
            "recently_settled_bets": self.recently_settled_bets,
        }

    def init_recently_unsettle_bets(self):
        bet_list = db.get_recently_unsettle_bet_list()
        for bet in bet_list:
            unsettlebet = UnSettleBet(
                bet.join_txid,
                bet.join_block_height,
                bet.game_round,
                bet.bet_level,
                bet.bet_number,
                util.get_precision(bet.bet_amount,2),
                bet.payment_address,
                bet.join_block_timestamp,
                #bet.created_at.strftime("%Y-%m-%d %H:%M:%S")
            )
            self.recently_unsettle_bets.append(unsettlebet.get_json_obj())

    def init_recently_settled_bets(self):
        bet_list = db.get_recently_settled_bet_list(100)
        for bet in bet_list:
            settledbet = SettledBet(
                bet.join_txid,
                bet.join_block_height,
                bet.settlement_block_height,
                bet.game_round,
                bet.bet_level,
                bet.bet_number,
                util.get_precision(bet.bet_amount,2),
                util.get_precision(bet.reward_amount,2),
                bet.bet_state,
                bet.payment_address,
                bet.join_block_timestamp,
                #bet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                bet.reward_txid,
            )
            self.recently_settled_bets.append(settledbet.get_json_obj())


class GameRound(object):
    def __init__(self, _db_bet_round):
        self.round = _db_bet_round.bet_round
        self.number = _db_bet_round.bet_number
        self.level = _db_bet_round.bet_level
        self.bet_count = _db_bet_round.bet_count
        self.bet_amount = util.get_precision(_db_bet_round.total_bet_amount,2)
        self.winner_count = _db_bet_round.winner_count
        self.loser_count = _db_bet_round.loser_count
        self.reward = util.get_precision(_db_bet_round.total_reward,2)
        self.start_bet_block = _db_bet_round.start_block
        self.end_bet_block = _db_bet_round.settled_block - 1
        self.reward_block = _db_bet_round.settled_block
        self.nonce = _db_bet_round.block_nonce

    def get_json_obj(self):
        return {
            "round":self.round,
            "number":self.number,
            "level":self.level,
            "bet_count":self.bet_count,
            "bet_amount":self.bet_amount,
            "winner_count":self.winner_count,
            "loser_count":self.loser_count,
            "reward":self.reward,
            "start_bet_block":self.start_bet_block,
            "end_bet_block":self.end_bet_block,
            "reward_block":self.reward_block,
            "nonce":self.nonce
        }


class PageHistory(object):
    def __init__(self, _bet_level):
        self.round_list = []
        self.init_game_round_list(_bet_level)


    def init_game_round_list(self, _bet_level):
        db_round_list = db.get_bet_round_list(_bet_level)
        if db_round_list is not None:
            for db_round in db_round_list:
                self.round_list.append(GameRound(db_round).get_json_obj())

    def get_json_obj(self):
        return self.round_list


class PageRoundBets(object):
    def __init__(self, _bet_level, _bet_round):
        self.round = _bet_round
        self.bet_count = 0
        self.bet_amount = 0
        self.winner_count = 0
        self.loser_count = 0
        self.total_reward = 0
        self.bet_number = -1

        if self.round > 0:
            bet_round_data = db.get_bet_round_data(_bet_level, self.round)
            if bet_round_data is not None:
                self.bet_count = bet_round_data.bet_count
                self.bet_amount = bet_round_data.total_bet_amount
                self.winner_count = bet_round_data.winner_count
                self.loser_count = bet_round_data.loser_count
                self.total_reward = bet_round_data.total_reward
                self.bet_number = bet_round_data.bet_number

        self.settled_bet_list = []

        self.init_round_bets(_bet_level, _bet_round)


    def get_json_obj(self):
        return {
            "round":self.round,
            "bet_count":self.bet_count,
            "bet_amount":self.bet_amount,
            "winner_count":self.winner_count,
            "loser_count":self.loser_count,
            "reward":self.total_reward,
            "number":self.bet_number,
            "bet_list":self.settled_bet_list,
        }


    def init_round_bets(self, _bet_level, _bet_round):
        bet_list = db.get_settled_bet_list(_bet_level, _bet_round)
        for bet in bet_list:
            settledbet = SettledBet(
                bet.join_txid,
                bet.join_block_height,
                bet.settlement_block_height,
                bet.game_round,
                bet.bet_level,
                bet.bet_number,
                util.get_precision(bet.bet_amount,2),
                util.get_precision(bet.reward_amount,2),
                bet.bet_state,
                bet.payment_address,
                # bet.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                bet.join_block_timestamp,
                bet.reward_txid,
            )
            self.settled_bet_list.append(settledbet.get_json_obj())





def generate_index_data_json():
    page_index = PageIndex().get_json_obj()
    json_str = json.dumps(page_index)
    with open(get_index_json_file(), "w", encoding="utf-8") as f:
        f.write(json_str)


def generate_history_data_json():
    small_history = PageHistory(1).get_json_obj()
    small_history_json_str = json.dumps(small_history)
    big_history = PageHistory(2).get_json_obj()
    big_history_json_str = json.dumps(big_history)
    rare_history = PageHistory(3).get_json_obj()
    rare_history_json_str = json.dumps(rare_history)
    with open(get_history_json_file(1), "w",encoding="utf-8") as f:
        f.write(small_history_json_str)

    with open(get_history_json_file(2), "w",encoding="utf-8") as f:
        f.write(big_history_json_str)

    with open(get_history_json_file(3), "w",encoding="utf-8") as f:
        f.write(rare_history_json_str)


def generate_bets_data_json(_bet_level, _bet_round):
    data = PageRoundBets(_bet_level, _bet_round).get_json_obj()
    data_json = json.dumps(data)
    with open(get_bets_json_file(_bet_level, _bet_round), "w", encoding="utf-8") as f:
        f.write(data_json)


def publish_thread():
    os.chdir(html_root)
    result = os.popen("git add .").read()
    log.Info("Add Result: ", result)
    result = os.popen('git commit -m "Update"').read()
    log.Info("Commit Result: ", result)
    result = os.popen("git push origin master").read()
    log.Info("Commit Result: ", result)


def update_view(_small_settled_round_list, _big_settled_round_list, _large_settled_round_list):
    generate_index_data_json()
    generate_history_data_json()

    for round in _small_settled_round_list:
        generate_bets_data_json(1, round)

    for round in _big_settled_round_list:
        generate_bets_data_json(2, round)

    for round in _large_settled_round_list:
        generate_bets_data_json(3, round)

    t = threading.Thread(target=publish_thread)
    t.setDaemon(True)
    t.start()






#log.init_logger()
#model.init_addresses()
#db.init_db()
#generate_index_data_json()
#generate_bets_data_json(1, 1)
#generate_history_data_json()
#regenerate_all()
#generate_index_page()
