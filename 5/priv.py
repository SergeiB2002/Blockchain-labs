import json
from eth_account import Account

# Загрузить keystore файл
with open('5/UTC', 'r') as f:
    keystore = json.load(f)

# Расшифровать с паролем
private_key = Account.decrypt(keystore, '***')
account = Account.from_key(private_key)

print(f"Адрес: {account.address}")
print(f"Приватный ключ: {private_key.hex()}")
