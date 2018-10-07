import rpcapi as api
import log

log.init_logger()

bank_address = api.get_or_create_address("dev")
print(bank_address)
