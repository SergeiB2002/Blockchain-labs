from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey
from bitcoinutils.script import Script
from bitcoinutils.keys import P2wshAddress

setup("testnet")

# 1) генерим 2 ключа (для двух пользователей)
k1 = PrivateKey()         # random
k2 = PrivateKey()         # random

wif1 = k1.to_wif()
wif2 = k2.to_wif()

pub1 = k1.get_public_key().to_hex()
pub2 = k2.get_public_key().to_hex()

# 2) witnessScript для 2-of-2: 2 <pub1> <pub2> 2 CHECKMULTISIG
# ВАЖНО: порядок pubkey фиксирует порядок подписей при трате.
witness_script = Script(["OP_2", pub1, pub2, "OP_2", "OP_CHECKMULTISIG"])
witness_script_hex = witness_script.to_hex()

# 3) P2WSH адрес из witnessScript
ms_addr = P2wshAddress.from_script(witness_script)
print("=== 2-of-2 P2WSH (testnet) ===")
print("multisig address (tb1q...):", ms_addr.to_string())
print("witnessScript hex:", witness_script_hex)
print("WIF user1:", wif1)
print("WIF user2:", wif2)

