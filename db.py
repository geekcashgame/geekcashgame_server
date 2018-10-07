from peewee import *
import datetime
import os
import random
import log

db_root = "./db/"
db_bet_name = "bets.db"
db_settled_name = "settled.db"

db = SqliteDatabase(db_root + db_bet_name)
db_settled = SqliteDatabase(db_root + db_settled_name)


class DBBetRound(Model):
    bet_round = IntegerField()
    bet_number = IntegerField()
    bet_level = IntegerField()
    bet_count = IntegerField()
    winner_count = IntegerField()
    loser_count = IntegerField()
    total_bet_amount = IntegerField()
    total_reward = IntegerField()
    dev_reward = IntegerField()
    start_block = IntegerField()
    settled_block = IntegerField()
    block_nonce = IntegerField()
    update_at = DateTimeField(default=datetime.datetime.now())
    created_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        database = db_settled


class DBBet(Model):
    join_txid = CharField(unique=True)
    join_block_height = IntegerField()
    join_block_hash = CharField()
    join_block_timestamp = IntegerField()
    bet_number = IntegerField()
    bet_address = CharField()
    bet_amount = FloatField()
    payment_address = CharField()

    bet_state = IntegerField(default=-1)  # -1 not closing, 0 lose, 1 win
    settlement_block_height = IntegerField(default=-1)
    settlement_block_hash = CharField(default="")
    settlement_block_nonce = IntegerField(default=-1)

    payment_state = IntegerField(default=-1)  # -1 no need pay, 0 unpay, 1 paid
    reward_amount = FloatField(default=0.0)
    reward_txid = CharField(default="")

    bet_level = IntegerField(default=1, index=True)  # 1 = small, 2 = big, 3 = large
    game_round = IntegerField(default=0, index=True)

    update_at = DateTimeField(default=datetime.datetime.now())
    created_at = DateTimeField(default=datetime.datetime.now())

    class Meta:
        database = db


def _generate_test_bet_data():
    for x in range(10):
        DBBet.create(
            join_txid="{}adedfdf45s4fds".format(x),
            join_block_height=random.randint(10000,99999),
            join_block_hash="{}545a4sd5f4a5sd4f5s5df4a5s4df".format(x),
            join_block_timestamp=random.randint(10000000, 99999999),
            bet_number=random.randint(0, 9),
            bet_address="{}fdjwoerunnvasdfasdf".format(x),
            bet_amount=random.randint(1000, 100000),
            payment_address="{}fdjwonsdfasdfnvasdfasdf".format(x),
            bet_level=random.randint(1, 3)
        )


def get_unsettle_bet_list(_bet_level):
    unsettle_bet_list = DBBet.select().where((DBBet.bet_state == -1) & (DBBet.bet_level == _bet_level))
    return unsettle_bet_list


def get_bet_list_by_round(_game_round):
    bet_list = DBBet.select().where(DBBet.game_round == _game_round)
    return bet_list


def save_new_bet_list(_bet_list, _bet_level):
    if _bet_list is None or len(_bet_list) == 0:
        return

    with db.atomic():
        for bet in _bet_list:
            try:
                dbbet = DBBet.get(DBBet.join_txid == bet["join_txid"])
            except DoesNotExist:
                dbbet = None

            if dbbet is None:
                log.Info("New bet: {} {}".format(bet["join_txid"], bet["bet_amount"]))
                DBBet.create(
                    join_txid=bet["join_txid"],
                    join_block_height=bet["join_block_height"],
                    join_block_hash=bet["join_block_hash"],
                    join_block_timestamp=bet["join_block_timestamp"],
                    bet_number=bet["bet_number"],
                    bet_address=bet["bet_address"],
                    bet_amount=bet["bet_amount"],
                    payment_address=bet["payment_address"],
                    bet_level=bet["bet_level"],
                    game_round=bet["bet_round"],
                    created_at=bet["created_at"],
                )


def save_settlement_bet_list(_dbbet_list):
    if _dbbet_list is None or len(_dbbet_list) == 0:
        return

    with db.atomic():
        now = datetime.datetime.now()
        for dbbet in _dbbet_list:
            dbbet.update_at = now
            dbbet.save()


def get_last_game_round_number(_bet_level):
    # result = DBBet.select(fn.Max(DBBet.game_round)).where(DBBet.bet_level == _bet_level).scalar()
    #if result is None:
    #    return 0
    #return result
    result = DBBetRound.select(fn.Max(DBBetRound.bet_round)).where(DBBetRound.bet_level == _bet_level).scalar()
    if result is None:
        return -1
    return result


def get_curr_unsettle_game_round(_bet_level):
    '''
    result = DBBet.select(fn.Max(DBBet.game_round)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_state == -1)
    ).scalar()
    if result is None:
        result = 1
    return result
    '''

    result = DBBetRound.select(fn.Max(DBBetRound.bet_round)).where(
        (DBBetRound.bet_level == _bet_level)
    ).scalar()
    if result is None:
        return 1
    return result + 1


def get_total_bet_count(_bet_level, _bet_number):
    count = DBBet.select(fn.Count(DBBet.join_txid)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_number == _bet_number)).scalar()
    return count

def get_total_unsettle_bet_count(_bet_level, _bet_number):
    count = DBBet.select(fn.Count(DBBet.join_txid)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_number == _bet_number) & (DBBet.bet_state == -1)
    ).scalar()
    return count


def get_total_bet_amount(_bet_level, _bet_number):
    sum_amount = DBBet.select(fn.SUM(DBBet.bet_amount)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_number == _bet_number)).scalar()
    if sum_amount is None:
        return 0
    else:
        return sum_amount

def get_total_unsettle_bet_amount(_bet_level, _bet_number):
    sum_amount = DBBet.select(fn.SUM(DBBet.bet_amount)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_number == _bet_number) & (DBBet.bet_state == -1)
    ).scalar()

    if sum_amount is None:
        return 0
    else:
        return sum_amount


def get_bet_number_total_win_count(_bet_level, _bet_number):
    count = DBBetRound.select(fn.Count(DBBetRound.bet_round)).where(
        (DBBetRound.bet_level == _bet_level) & (DBBetRound.bet_number == _bet_number)).scalar()
    return count


def get_curr_unsettle_count(_bet_level):
    count = DBBet.select(fn.Count(DBBet.join_txid)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_state == -1)
    ).scalar()
    return count


def get_curr_unsettle_amount(_bet_level):
    amount = DBBet.select(fn.SUM(DBBet.bet_amount)).where(
        (DBBet.bet_level == _bet_level) & (DBBet.bet_state == -1)
    ).scalar()
    if amount is None:
        return 0
    return amount


def get_bet_round_data(_bet_level, _bet_round):
    bet_rounds = DBBetRound.select().where(
        (DBBetRound.bet_round == _bet_round) & (DBBetRound.bet_level == _bet_level))
    if len(bet_rounds) > 0:
        return bet_rounds[0]
    return None


def get_bet_round_list(_bet_level):
    bet_rounds = DBBetRound.select().where(
        DBBetRound.bet_level == _bet_level
    )
    return bet_rounds


def save_settled_header_data(_bet_round, _bet_number, _bet_level, _bet_count, _winner_count,
                             _loser_count, _total_bet_amount, _total_reward,
                             _dev_reward, _start_block, _settled_block, _block_nonce):
    DBBetRound.create(
        bet_round=_bet_round,
        bet_number=_bet_number,
        bet_level=_bet_level,
        bet_count=_bet_count,
        winner_count=_winner_count,
        loser_count=_loser_count,
        total_bet_amount=_total_bet_amount,
        total_reward=_total_reward,
        dev_reward=_dev_reward,
        start_block=_start_block,
        settled_block=_settled_block,
        block_nonce=_block_nonce,
    )


def get_all_settled_header_data():
    return DBBetRound.select()


def get_settled_header_list(_bet_level):
    header_list = DBBetRound.select().where(DBBetRound.bet_level == _bet_level)
    return header_list


def get_settled_bet_list(_bet_level, _bet_round):
    settled_bet_list = DBBet.select().where(
        (DBBet.bet_level == _bet_level) & (DBBet.game_round == _bet_round)
    )
    return settled_bet_list


def get_recently_unsettle_bet_list():
    result = DBBet.select().where(DBBet.bet_state == -1).order_by(DBBet.created_at.desc())
    return result


def get_recently_settled_bet_list(_limit):
    result = DBBet.select().where(DBBet.bet_state != -1).order_by(DBBet.update_at.desc()).limit(_limit)
    return result


def get_recently_winner_list(_bet_level, _limit):
    result = DBBet.select().where((DBBet.bet_state == 1) & (DBBet.bet_level == _bet_level)).order_by(DBBet.created_at.desc()).limit(_limit)
    return result


def init_db():
    if not os.path.exists(db_root):
        log.Info("To Create database dir!")
        os.mkdir(db_root)
    db.connect()
    db.create_tables([DBBet])

    db_settled.connect()
    db_settled.create_tables([DBBetRound])


def close_db():
    db.close()
