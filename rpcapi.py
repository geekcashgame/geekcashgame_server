from bitcoinrpc.authproxy import AuthServiceProxy
import util

rpc_user = "NiPEL9gATxuo"
rpc_password = "2h4GvkQnWCqXmAnYBaucRe8Ik5d5g7TB"
url = "http://{}:{}@127.0.0.1:6888".format(rpc_user, rpc_password)
# rpc_user and rpc_password are set in the bitcoin.conf file
rpc = AuthServiceProxy(url, timeout=3)


def get_address_by_account_name(_account_name):
    address_list = rpc.getaddressesbyaccount(_account_name)
    if len(address_list) == 0:
        return None
    else:
        return address_list[0]


def create_new_address(_account_name):
    address = rpc.getaccountaddress(_account_name)
    return address


def get_or_create_address(_account_name):
    address = get_address_by_account_name(_account_name)
    if address is None:
        address = create_new_address(_account_name)
    return address


# Send all balance from unspent list to one address, The test result is: unspent_list max 500,
def send_to_address_from_unspent_list(unspent_list, to_address):
    if unspent_list is None or len(unspent_list) == 0:
        print("No unspent list!")
        return -1

    if to_address is None:
        print("No to address!")
        return -1

    input_list = []
    total_balance = 0.0
    for unspent in unspent_list:
        txid = unspent['txid']
        vout = unspent['vout']
        amount = unspent['amount']
        total_balance += util.get_precision(amount, 8)
        input_list.append({"txid": txid, "vout": vout})

    fee = ((len(unspent_list) * 180 + 1 * 34 + 10 + 40) / 1024) * 0.000015
    fee = util.get_precision(fee, 8)
    total_send = total_balance - fee
    total_send = util.get_precision(total_send, 8)
    send_dict = dict()
    send_dict[to_address] = total_send

    if total_send <= 0.0:
        print("No enough money, send faild!")
        return -1

    transaction_hash = rpc.createrawtransaction(input_list, send_dict)
    signed_hex = rpc.signrawtransaction(transaction_hash)['hex']
    out_txid = rpc.sendrawtransaction(signed_hex)

    print("Balance: {}, send: {}, fee: {}, out_txid: {}".format(total_balance, total_send, fee, out_txid))
    return out_txid


def send_all_unspent_list_to_address(_to_address):
    unspent_list = rpc.listunspent()
    if unspent_list is not None and len(unspent_list) > 0:
        return send_to_address_from_unspent_list(unspent_list, _to_address)
    return None


# send money from unspent to many address, and change to one address
def send_to_many_from_unspent_list(unspent_list, to_dict, change_address):
    if unspent_list is None or len(unspent_list) == 0:
        print("No unspent list!")
        return -1

    if to_dict is None or len(to_dict) == 0:
        print("No to dict!")
        return -1

    input_list = list()
    total_balance = 0.0
    for unspent in unspent_list:
        txid = unspent['txid']
        vout = unspent['vout']
        amount = unspent['amount']
        total_balance += util.get_precision(amount, 8)
        input_list.append({"txid": txid, "vout": vout})

    total_send = 0.0
    for key in to_dict:
        send_amount = to_dict[key]
        total_send += send_amount

    fee = ((len(unspent_list) * 180 + (len(to_dict) + 1) * 34 + 10 + 40) / 1024) * 0.000015
    fee = util.get_precision(fee, 8)
    change_amount = total_balance - total_send - fee
    change_amount = util.get_precision(change_amount, 8)
    if change_amount < 0:
        print("No enough money to send, balance: {}, send: {}".format(total_balance, total_send))
        return -1

    to_dict[change_address] = change_amount

    transaction_hash = rpc.createrawtransaction(input_list, to_dict)
    signed_hex = rpc.signrawtransaction(transaction_hash)['hex']
    out_txid = rpc.sendrawtransaction(signed_hex)

    print(
        "Balance: {}, send: {}, fee: {}, change: {}, out_txid: {}".format(total_balance, total_send, fee, change_amount,
                                                                          out_txid))
    return out_txid


def send_to_many_from_input_txid_list(_input_txid_list, _to_dict, _change_address):
    all_unspent_list = rpc.listunspent()
    unspent_dict = {}
    for unspent in all_unspent_list:
        unspent_dict[unspent["txid"]] = unspent

    input_unspent_list = []
    for txid in _input_txid_list:
        unspent = unspent_dict.get(txid, None)
        if unspent is None:
            print("Fatal Error, can not found unspent in unspent list: ", txid)
            return None
        input_unspent_list.append(unspent)

    return send_to_many_from_unspent_list(input_unspent_list, _to_dict, _change_address)


def get_block_hash(_block_height):
    block_hash = rpc.getblockhash(_block_height)
    return block_hash


def get_current_block_height():
    return rpc.getblockcount()


def get_block_height_nonce_timestamp_by_hash(_block_hash):
    block_info = rpc.getblockheader(_block_hash)
    return block_info['height'], block_info['nonce'], block_info['time']


def get_block_hash_nonce_timestamp_by_height(_block_height):
    block_hash = get_block_hash(_block_height)
    height, nonce, timestamp = get_block_height_nonce_timestamp_by_hash(block_hash)
    return block_hash, nonce, timestamp


def get_unspent_list_by_address(_address):
    unspent_list = rpc.listunspent(0, 999999999, [_address])
    return unspent_list


def get_raw_transaction_info(_txid):
    raw_transaction = rpc.getrawtransaction(_txid, 1)
    return raw_transaction


def get_input_addresses(_txid):
    raw_transaction = get_raw_transaction_info(_txid)
    input_address_list = []
    for vin in raw_transaction["vin"]:
        in_txid = vin["txid"]
        index = vin["vout"]
        info = get_raw_transaction_info(in_txid)
        input_address = None
        for vout_info in info["vout"]:
            if vout_info["n"] == index:
                input_address = vout_info["scriptPubKey"]["addresses"][0]
                break
        if input_address is None:
            print("Error, get input address faild!")
        input_address_list.append(input_address)
    return input_address_list


def get_block_height_hash_timestamp_by_txid(_txid):
    raw_transaction = get_raw_transaction_info(_txid)
    print("Raw Transacion: ", raw_transaction)
    if "height" in raw_transaction:
        height = raw_transaction["height"]
        hash = raw_transaction["blockhash"]
        timestamp = raw_transaction["blocktime"]
        return height, hash, timestamp
    return -1,-1,-1



#result = send_all_unspent_list_to_address("Gcx6ce8xpSjpNJPd9SrPYdhZ2Nim2eEhyQ")
#print(result)


"""
min_conf = 0
max_conf = 999999999

address_list = []

for x in range(500, 1001):
    account_name = "sub_{}".format(x)
    addresses = rpc.getaddressesbyaccount(account_name)
    print("account_name: ", account_name, "address: ", addresses)
    address_list += addresses

print(address_list)
unspent_list = rpc.listunspent(min_conf, max_conf, address_list)
print(unspent_list)
print("Count: ", len(unspent_list))

to_address = "GdKLkjAoWLfP169x5b4AsKkXaABsaGbUJp"
send_to_address_from_unspent_list(unspent_list, to_address)

"""

"""
 1. 收集下注，将所有的下注的unspent收集到奖池地址, 每次 input 控制在 500 以内
 2. - 合并奖池？？？暂时不需要，如果每一轮游戏产生过多的500下注，那说明这个游戏太火了，再优化
 3. 使用奖池中所有的unspent，进行奖金分配，（测试最多可支持向多少个地址发送）
 

"""

'''
best_block_hash = rpc_connection.getbestblockhash()
print(rpc_connection.getblock(best_block_hash))

unspent_list = rpc_connection.listunspent()
print(unspent_list)

result = rpc_connection.getrawtransaction("df98dad818a057daf5daf644dd61eb9034644d2e202a17755821661f6081e264", 1)
print(result)
'''

'''
input_list = [
    {
        "txid": "df98dad818a057daf5daf644dd61eb9034644d2e202a17755821661f6081e264",
        "vout": 0
    }
]

out_dict = {
    "GeJajKMpAirXdYEeWEHQDJtSfDv6F9p8a6": 1.0,
    "GYatfDCWQDPFJHMWsCLy2rcvN1RoZ5xNg8": 1.0,
    "GUnBgbWYcKiupH5Lk1H1AWqCHtUNfvzcAE": 0.9999
}

raw_transaction = rpc_connection.createrawtransaction(input_list, out_dict)
print(raw_transaction)
'''

'''
signed_raw_transaction_result = rpc_connection.signrawtransaction(raw_transaction)
print(signed_raw_transaction_result)
print(signed_raw_transaction_result['hex'])
send_txid = rpc_connection.sendrawtransaction(signed_raw_transaction_result['hex'])
print("txid:")
print(send_txid)
'''
