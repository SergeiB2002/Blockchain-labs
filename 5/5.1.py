import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import os
from dotenv import load_dotenv
import time

# Загружаем переменные окружения из .env файла
load_dotenv()

class EthereumTransactionHandler:
    def __init__(self, node_url=None, private_key=None, from_address=None):
        """
        Инициализация подключения к ноде Ethereum
        
        Args:
            node_url: URL ноды (по умолчанию: локальная нода Geth в dev режиме)
            private_key: Приватный ключ отправителя
            from_address: Адрес отправителя
        """
        # URL ноды по умолчанию для Geth dev режима
        self.node_url = node_url or "http://localhost:8545"
        
        # Подключаемся к ноде
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        
        # Для dev сети (POA) добавляем middleware
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Проверяем подключение
        if not self.w3.is_connected():
            raise ConnectionError(f"Не удалось подключиться к ноде по адресу {self.node_url}")
        
        print(f"Успешное подключение к ноде Ethereum")
        print(f"   URL: {self.node_url}")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   Номер блока: {self.w3.eth.block_number}")
        print(f"   Синхронизирована: {self.w3.eth.syncing}")
        
        # Устанавливаем приватный ключ и адрес
        self.private_key = private_key or os.getenv('PRIVATE_KEY')
        self.from_address = from_address or os.getenv('FROM_ADDRESS')
        
        if not self.private_key:
            raise ValueError("Приватный ключ не указан. Укажите в аргументе или в .env файле")
        
        if not self.from_address:
            # Получаем адрес из приватного ключа и конвертируем в checksum формат
            self.from_address = self.w3.eth.account.from_key(self.private_key).address
            self.from_address = self.w3.to_checksum_address(self.from_address)
        else:
            # Конвертируем переданный адрес в checksum формат
            self.from_address = self.w3.to_checksum_address(self.from_address)
        
        # Проверяем баланс
        self.check_balance()
    
    def check_balance(self):
        """Проверяет баланс адреса отправителя"""
        balance_wei = self.w3.eth.get_balance(self.from_address)
        balance_eth = self.w3.from_wei(balance_wei, 'ether')
        
        print(f"\nБаланс адреса {self.from_address}:")
        print(f"   {balance_eth} ETH")
        print(f"   {balance_wei} Wei")
        
        return balance_wei
    
    def create_transaction(self, to_address, value_eth, gas_limit=21000, gas_price=None):
        """
        Создает транзакцию
        
        Args:
            to_address: Адрес получателя
            value_eth: Количество ETH для отправки
            gas_limit: Лимит газа
            gas_price: Цена газа (если None, будет получена автоматически)
        
        Returns:
            Словарь с данными транзакции
        """
        # Конвертируем ETH в Wei
        value_wei = self.w3.to_wei(value_eth, 'ether')
        
        # Получаем nonce (количество транзакций отправленных с адреса)
        nonce = self.w3.eth.get_transaction_count(self.from_address)

        # Конвертируем адрес получателя в checksum формат
        to_address_checksum = self.w3.to_checksum_address(to_address)
        
        # Получаем актуальную цену газа, если не указана
        if gas_price is None:
            gas_price = self.w3.eth.gas_price
        else:
            gas_price = self.w3.to_wei(gas_price, 'gwei')
        
        # Создаем транзакцию
        transaction = {
            'nonce': nonce,
            'to': to_address_checksum,
            'value': value_wei,
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': self.w3.eth.chain_id,
        }
        
        print(f"\nСоздана транзакция:")
        print(f"   От: {self.from_address}")
        print(f"   Кому: {to_address}")
        print(f"   Сумма: {value_eth} ETH ({value_wei} Wei)")
        print(f"   Nonce: {nonce}")
        print(f"   Gas Limit: {gas_limit}")
        print(f"   Gas Price: {gas_price} Wei ({self.w3.from_wei(gas_price, 'gwei')} Gwei)")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        
        # Рассчитываем комиссию
        fee_wei = gas_limit * gas_price
        fee_eth = self.w3.from_wei(fee_wei, 'ether')
        print(f"   Ориентировочная комиссия: {fee_eth} ETH")
        
        return transaction
    
    def sign_transaction(self, transaction):
        """Подписывает транзакцию приватным ключом"""
        print(f"\nПодписание транзакции...")
        
        signed_txn = self.w3.eth.account.sign_transaction(
            transaction, 
            self.private_key
        )

        # Конвертируем hash в hex строку
        tx_hash_hex = signed_txn.hash.hex() if hasattr(signed_txn.hash, 'hex') else f"0x{signed_txn.hash:064x}"
        
        print(f"   Хэш транзакции: {tx_hash_hex}")
        print(f"   Подпись r: {hex(signed_txn.r)[:20]}...")
        print(f"   Подпись s: ...{hex(signed_txn.s)[-20:]}")
        print(f"   V: {signed_txn.v}")
        
        return signed_txn
    
    def send_transaction(self, signed_txn):
        """Отправляет подписанную транзакцию в сеть"""
        print(f"\nОтправка транзакции в сеть...")
        
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
            
            # Ждем подтверждения
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            print(f"Транзакция успешно отправлена и подтверждена!")
            print(f"   Хэш транзакции: {tx_hash.hex()}")
            print(f"   Номер блока: {tx_receipt.blockNumber}")
            print(f"   Gas использовано: {tx_receipt.gasUsed}")
            print(f"   Статус: {'Успех' if tx_receipt.status == 1 else 'Ошибка'}")
            
            return tx_hash, tx_receipt
            
        except Exception as e:
            print(f"Ошибка при отправке транзакции: {e}")
            raise
    
    def get_transaction_info(self, tx_hash):
        """Получает информацию о транзакции"""
        print(f"\nПолучение информации о транзакции {tx_hash.hex()}...")
        
        # Получаем данные транзакции
        tx = self.w3.eth.get_transaction(tx_hash)
        
        print(f"   Хэш транзакции: {tx.hash.hex()}")
        print(f"   От: {tx['from']}")
        print(f"   Кому: {tx['to']}")
        print(f"   Сумма: {self.w3.from_wei(tx.value, 'ether')} ETH")
        print(f"   Gas Price: {self.w3.from_wei(tx.gasPrice, 'gwei')} Gwei")
        print(f"   Gas Limit: {tx.gas}")
        print(f"   Nonce: {tx.nonce}")
        print(f"   Номер блока: {tx.blockNumber if tx.blockNumber else 'Еще не в блоке'}")
        print(f"   Позиция в блоке: {tx.transactionIndex}")
        
        return tx
    
    def get_block_info(self, block_number):
        """Получает информацию о блоке"""
        print(f"\nПолучение информации о блоке #{block_number}...")
        
        block = self.w3.eth.get_block(block_number)
        
        print(f"   Номер блока: {block.number}")
        print(f"   Хэш блока: {block.hash.hex()}")
        print(f"   Хэш родителя: {block.parentHash.hex()}")
        print(f"   Timestamp: {block.timestamp} ({time.ctime(block.timestamp)})")
        print(f"   Nonce: {block.nonce.hex()}")
        print(f"   Miner: {block.miner}")
        print(f"   Difficulty: {block.difficulty}")
        print(f"   Gas Limit: {block.gasLimit}")
        print(f"   Gas Used: {block.gasUsed}")
        print(f"   Количество транзакций: {len(block.transactions)}")
        
        if block.transactions:
            print(f"   Транзакции в блоке:")
            for i, tx_hash in enumerate(block.transactions[:5]):  # Показываем первые 5
                tx = self.w3.eth.get_transaction(tx_hash)
                print(f"     {i+1}. {tx_hash.hex()} - {self.w3.from_wei(tx.value, 'ether')} ETH")
            
            if len(block.transactions) > 5:
                print(f"     ... и еще {len(block.transactions) - 5} транзакций")
        
        return block
    
    def transfer_ether(self, to_address, value_eth):
        """Полный процесс: создание, подписание и отправка транзакции"""
        print(f"\n{'='*60}")
        print(f"Начинаем процесс перевода {value_eth} ETH на адрес {to_address}")
        print(f"{'='*60}")
        
        # Проверяем баланс перед отправкой
        balance = self.check_balance()
        value_wei = self.w3.to_wei(value_eth, 'ether')
        
        if balance < value_wei:
            print(f"Недостаточно средств!")
            print(f"   Требуется: {value_wei} Wei")
            print(f"   Доступно: {balance} Wei")
            return None
        
        # 1. Создаем транзакцию
        transaction = self.create_transaction(to_address, value_eth)
        
        # 2. Подписываем транзакцию
        signed_txn = self.sign_transaction(transaction)
        
        # 3. Отправляем транзакцию
        tx_hash, tx_receipt = self.send_transaction(signed_txn)
        
        # 4. Получаем информацию о транзакции
        tx_info = self.get_transaction_info(tx_hash)
        
        # 5. Получаем информацию о блоке
        if tx_receipt.blockNumber:
            block_info = self.get_block_info(tx_receipt.blockNumber)
        
        print(f"\nПеревод завершен успешно!")
        return tx_hash

def main():
    """Основная функция с примером использования"""
    
    config = {
        # Для Geth dev режима (по умолчанию)
        'NODE_URL': 'http://localhost:8545',
        
        # Приватный ключ и адрес отправителя
        'PRIVATE_KEY': '0x***',
        'FROM_ADDRESS': '0x7e569a12e0cb2d6f7a7cc4a3d28eccdaef327ba9',
    }
    
    try:
        # Создаем обработчик транзакций
        eth_handler = EthereumTransactionHandler(
            node_url=config['NODE_URL'],
            private_key=config['PRIVATE_KEY'],
            from_address=config['FROM_ADDRESS']
        )
        
        # Адрес получателя
        to_address = '0xf02c7effdcfffa8279644648588d7652b8d08bc5'
        
        # Сумма для перевода (в ETH)
        amount_eth = 0.01
        
        # Выполняем перевод
        tx_hash = eth_handler.transfer_ether(to_address, amount_eth)
        
        if tx_hash:
            print(f"\nТранзакция успешно выполнена!")
            print(f"   Хэш: {tx_hash.hex()}")
            
            # Дополнительно: получаем текущий баланс
            print(f"\nТекущий баланс отправителя:")
            eth_handler.check_balance()
        
    except Exception as e:
        print(f"\nОшибка: {e}")

if __name__ == "__main__":
    main()
