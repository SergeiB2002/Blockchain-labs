import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import os

class ContractWriter:
    def __init__(self, node_url=None, private_key=None, contract_address=None):
        """
        Инициализация для записи данных в контракт
        """
        self.node_url = node_url or "http://localhost:8545"
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not self.w3.is_connected():
            raise ConnectionError("Не удалось подключиться к ноде")
        
        print(f"Подключено к ноде Ethereum")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   Номер блока: {self.w3.eth.block_number}")
        
        # Приватный ключ
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.from_address = self.w3.to_checksum_address(self.account.address)
        
        print(f"Адрес отправителя: {self.from_address}")
        
        # Загрузка адреса контракта
        if contract_address:
            self.contract_address = contract_address
        else:
            try:
                with open("contract_address.txt", "r") as f:
                    self.contract_address = f.read().strip()
            except:
                raise ValueError("Адрес контракта не найден")
        
        self.contract_address = self.w3.to_checksum_address(self.contract_address)
        
        # Загрузка ABI
        try:
            with open("SimpleStorage_abi.json", "r") as f:
                self.abi = json.load(f)
        except:
            raise ValueError("ABI не найден")
        
        # Создание объекта контракта
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )
    
    def set_value(self, new_value):
        """
        Вызывает метод set() контракта для установки нового значения
        """
        print(f"\nУстановка нового значения: {new_value}")
        print(f"   Адрес контракта: {self.contract_address}")
        
        try:
            # Получаем текущее значение перед изменением
            current_value = self.contract.functions.get().call()
            print(f"   Текущее значение: {current_value}")
            
            # Строим транзакцию для вызова set()
            nonce = self.w3.eth.get_transaction_count(self.from_address)
            
            transaction = self.contract.functions.set(new_value).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'from': self.from_address
            })
            
            # Подписываем транзакцию
            print("Подписание транзакции...")
            signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
            
            # Отправляем транзакцию
            print("Отправка транзакции...")
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            tx_hash_hex = tx_hash.hex() if hasattr(tx_hash, 'hex') else f"0x{tx_hash:064x}"
            print(f"Транзакция отправлена: {tx_hash_hex}")
            
            # Ждем подтверждения
            print("Ожидание подтверждения...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            print(f"Транзакция подтверждена!")
            print(f"   Номер блока: {tx_receipt.blockNumber}")
            print(f"   Gas использовано: {tx_receipt.gasUsed}")
            print(f"   Статус: {'Успех' if tx_receipt.status == 1 else 'Ошибка'}")
            
            # Проверяем новое значение
            updated_value = self.contract.functions.get().call()
            print(f"   Новое значение в контракте: {updated_value}")
            
            return tx_hash, tx_receipt
            
        except Exception as e:
            print(f"Ошибка при установке значения: {e}")
            raise
    
    def get_transaction_info(self, tx_hash):
        """
        Получает информацию о транзакции
        """
        print(f"\nИнформация о транзакции {tx_hash.hex() if hasattr(tx_hash, 'hex') else tx_hash}...")
        
        try:
            tx = self.w3.eth.get_transaction(tx_hash)
            
            print(f"   Хэш: {tx.hash.hex()}")
            print(f"   От: {tx['from']}")
            print(f"   Кому: {tx['to']}")
            print(f"   Сумма: {self.w3.from_wei(tx.value, 'ether')} ETH")
            print(f"   Gas Price: {self.w3.from_wei(tx.gasPrice, 'gwei')} Gwei")
            print(f"   Gas Limit: {tx.gas}")
            print(f"   Nonce: {tx.nonce}")
            print(f"   Номер блока: {tx.blockNumber}")
            
            # Декодируем input данные (вызов функции)
            if tx.input and tx.input != '0x':
                print(f"   Input данные: {tx.input[:50]}...")
            
            return tx
        except Exception as e:
            print(f"Ошибка при получении информации о транзакции: {e}")
            return None
    
    def get_block_info(self, block_number):
        """
        Получает информацию о блоке
        """
        print(f"\nИнформация о блоке #{block_number}...")
        
        try:
            import time
            block = self.w3.eth.get_block(block_number)
            
            print(f"   Номер блока: {block.number}")
            print(f"   Хэш блока: {block.hash.hex()}")
            print(f"   Время: {block.timestamp} ({time.ctime(block.timestamp)})")
            print(f"   Miner: {block.miner}")
            print(f"   Gas Limit: {block.gasLimit}")
            print(f"   Gas Used: {block.gasUsed}")
            print(f"   Количество транзакций: {len(block.transactions)}")
            
            if block.transactions:
                print(f"   Транзакции в блоке:")
                for i, tx_hash in enumerate(block.transactions[:3]):
                    print(f"     {i+1}. {tx_hash.hex()}")
            
            return block
        except Exception as e:
            print(f"Ошибка при получении информации о блоке: {e}")
            return None

def main():
    """Основная функция для установки значения в контракте"""
    
    print("=" * 60)
    print("Установка значения в смарт-контракте SimpleStorage")
    print("=" * 60)
    
    try:
        # Инициализация врайтера
        writer = ContractWriter(
            node_url="http://localhost:8545",
            private_key="0x***"
        )
        
        # Устанавливаем новое значение
        new_value = 999  # Пример нового значения
        tx_hash, tx_receipt = writer.set_value(new_value)
        
        # Получаем информацию о транзакции
        if tx_hash:
            writer.get_transaction_info(tx_hash)
        
        # Получаем информацию о блоке
        if tx_receipt and tx_receipt.blockNumber:
            writer.get_block_info(tx_receipt.blockNumber)
        
        print(f"\nЗначение успешно обновлено!")
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
