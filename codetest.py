import rpcapi as api
import log

log.init_logger()

bank_address = api.get_or_create_address("bank")
print(bank_address)


result = api.send_all_unspent_list_to_address("GTDC6VoAALQtEra9n5tNu41PogPTojkqg2")
print(result)