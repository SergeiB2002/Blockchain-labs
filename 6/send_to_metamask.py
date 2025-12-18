import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import sys

def send_tokens_to_metamask():
    """Отправить токены на адрес MetaMask"""
    
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if not w3.is_connected():
        print("Не подключены к ноде Geth!")
        return
    
    # Загружаем информацию о контракте
    try:
        with open('deployed_contract.json', 'r') as f:
            contract_info = json.load(f)
    except FileNotFoundError:
        print("Сначала разверните контракт! Запустите deploy.py")
        return
    
    # Создаем экземпляр контракта
    contract = w3.eth.contract(
        address=contract_info['address'],
        abi=contract_info['abi']
    )
    
    # Получаем аккаунты из ноды
    node_accounts = w3.eth.accounts
    if not node_accounts:
        print("Нет доступных аккаунтов в ноде!")
        return
    
    sender = node_accounts[0]  # Используем первый аккаунт ноды
    print(f"Отправитель (нода): {sender}")
    
    # Запрашиваем адрес MetaMask у пользователя
    print("\n" + "=" * 60)
    print("ОТПРАВКА ТОКЕНОВ НА METAMASK")
    print("=" * 60)
    
    # Пример адреса MetaMask (замените на ваш реальный)
    metamask_address = input("\nВведите адрес вашего кошелька MetaMask (0x...): ").strip()
    
    # Валидация адреса
    if not w3.is_address(metamask_address):
        print("Ошибка: Неверный адрес Ethereum!")
        return
    
    metamask_address = w3.to_checksum_address(metamask_address)
    
    # Запрашиваем количество токенов
    try:
        token_amount = float(input(f"\nВведите количество токенов для отправки (max 1000): "))
        if token_amount <= 0 or token_amount > 1000:
            print("Количество должно быть от 0.001 до 1000")
            return
    except ValueError:
        print("Ошибка: Введите числовое значение!")
        return
    
    # Конвертируем в wei с учетом decimals
    decimals = contract.functions.decimals().call()
    amount_wei = int(token_amount * 10**decimals)
    
    print(f"\nПодготовка перевода:")
    print(f"  Отправитель: {sender}")
    print(f"  Получатель: {metamask_address}")
    print(f"  Количество: {token_amount} {contract_info['symbol']}")
    print(f"  В wei: {amount_wei}")
    
    # Проверяем баланс отправителя
    sender_balance = contract.functions.balanceOf(sender).call()
    if sender_balance < amount_wei:
        print(f"Ошибка: Недостаточно токенов!")
        print(f"  Доступно: {sender_balance / 10**decimals} {contract_info['symbol']}")
        return
    
    # Получаем nonce
    nonce = w3.eth.get_transaction_count(sender)
    
    # Строим транзакцию
    try:
        print(f"\nСоздание транзакции...")
        tx = contract.functions.transfer(metamask_address, amount_wei).build_transaction({
            'chainId': w3.eth.chain_id,
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
            'from': sender
        })
        
        # Отправляем транзакцию
        print("Отправка транзакции...")
        tx_hash = w3.eth.send_transaction(tx)
        print(f"  Хэш транзакции: {tx_hash.hex()}")
        
        # Ждем подтверждения
        print("Ожидание подтверждения...")
        tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if tx_receipt.status == 1:
            print(f"\n✓ Перевод успешно выполнен!")
            print(f"  Блок: {tx_receipt.blockNumber}")
            print(f"  Использовано газа: {tx_receipt.gasUsed}")
            
            # Проверяем новые балансы
            new_sender_balance = contract.functions.balanceOf(sender).call()
            receiver_balance = contract.functions.balanceOf(metamask_address).call()
            
            print(f"\nНовые балансы:")
            print(f"  Отправитель: {new_sender_balance / 10**decimals} {contract_info['symbol']}")
            print(f"  Получатель (MetaMask): {receiver_balance / 10**decimals} {contract_info['symbol']}")
       
        else:
            print("✗ Ошибка при выполнении транзакции!")
            
    except Exception as e:
        print(f"Ошибка: {e}")
        import traceback
        traceback.print_exc()

def check_balance(address):
    """Проверить баланс токенов по адресу"""
    
    w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    
    if not w3.is_connected():
        print("Не подключены к ноде Geth!")
        return
    
    try:
        with open('deployed_contract.json', 'r') as f:
            contract_info = json.load(f)
    except FileNotFoundError:
        print("Сначала разверните контракт!")
        return
    
    # Создаем экземпляр контракта
    contract = w3.eth.contract(
        address=contract_info['address'],
        abi=contract_info['abi']
    )
    
    # Валидация адреса
    if not w3.is_address(address):
        print("Ошибка: Неверный адрес Ethereum!")
        return
    
    address = w3.to_checksum_address(address)
    
    # Проверяем баланс
    token_balance = contract.functions.balanceOf(address).call()
    eth_balance = w3.eth.get_balance(address)
    
    print(f"\nБаланс для адреса {address}:")
    print(f"  Токены {contract_info['symbol']}: {token_balance / 10**contract_info['decimals']}")
    print(f"  ETH: {w3.from_wei(eth_balance, 'ether')}")
    
    return token_balance

def main():
    """Основная функция"""
    
    print("=" * 60)
    print("METAMASK INTEGRATION SCRIPT")
    print("=" * 60)
    
    while True:
        print(f"\nВыберите действие:")
        print(f"1. Отправить токены на адрес MetaMask")
        print(f"2. Проверить баланс по адресу")
        print(f"3. Выход")
        
        choice = input("\nВаш выбор (1-4): ").strip()
        
        if choice == "1":
            send_tokens_to_metamask()
        elif choice == "2":
            address = input("Введите адрес для проверки баланса: ").strip()
            check_balance(address)
        elif choice == "3":
            print("Выход...")
            break
        else:
            print("Неверный выбор!")

if __name__ == "__main__":
    main()
