import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from solcx import compile_standard, install_solc
import os

# Установка конкретной версии solc
install_solc('0.8.0')

class ContractDeployer:
    def __init__(self, node_url=None, private_key=None, from_address=None):
        """
        Инициализация подключения к ноде Ethereum
        """
        self.node_url = node_url or "http://localhost:8545"
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Не удалось подключиться к ноде по адресу {self.node_url}")
        
        print(f"Успешное подключение к ноде Ethereum")
        print(f"   Chain ID: {self.w3.eth.chain_id}")
        print(f"   Номер блока: {self.w3.eth.block_number}")
        
        self.private_key = private_key
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.from_address = self.w3.to_checksum_address(self.account.address)
        
        print(f"Адрес отправителя: {self.from_address}")
        
    def compile_contract(self, contract_path="SimpleStorage.sol"):
        """
        Компилирует Solidity контракт
        """
        print(f"\nКомпиляция контракта из файла {contract_path}...")
        
        # Чтение исходного кода
        with open(contract_path, 'r') as file:
            source_code = file.read()
        
        # Настройки компиляции
        compile_settings = {
            "language": "Solidity",
            "sources": {
                "SimpleStorage.sol": {
                    "content": source_code
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]
                    }
                }
            }
        }
        
        # Компиляция
        compiled_sol = compile_standard(compile_settings, solc_version="0.8.0")
        
        # Извлечение ABI и байткода
        contract_data = compiled_sol["contracts"]["SimpleStorage.sol"]["SimpleStorage"]
        abi = contract_data["abi"]
        bytecode = contract_data["evm"]["bytecode"]["object"]
        
        print("Контракт успешно скомпилирован")
        print(f"   Длина байткода: {len(bytecode)} символов")
        print(f"   Количество функций в ABI: {len(abi)}")
        
        # Сохранение ABI в файл
        with open("SimpleStorage_abi.json", "w") as f:
            json.dump(abi, f, indent=2)
        
        # Сохранение байткода в файл
        with open("SimpleStorage_bytecode.txt", "w") as f:
            f.write(bytecode)
        
        return abi, bytecode
    
    def deploy_contract(self, abi, bytecode, initial_value=42):
        """
        Деплоит контракт в сеть
        """
        print(f"\nДеплой контракта с начальным значением: {initial_value}")
        
        # Создаем объект контракта
        Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        
        # Получаем nonce
        nonce = self.w3.eth.get_transaction_count(self.from_address)
        
        # Строим транзакцию для деплоя
        transaction = Contract.constructor(initial_value).build_transaction({
            'chainId': self.w3.eth.chain_id,
            'gas': 2000000,  # Больше газа для деплоя
            'gasPrice': self.w3.eth.gas_price,
            'nonce': nonce,
            'from': self.from_address
        })
        
        # Подписываем транзакцию
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        
        # Отправляем транзакцию
        print("Отправка транзакции деплоя...")
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        tx_hash_hex = tx_hash.hex() if hasattr(tx_hash, 'hex') else f"0x{tx_hash:064x}"
        print(f"Транзакция отправлена: {tx_hash_hex}")
        
        # Ждем подтверждения
        print("Ожидание подтверждения...")
        tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
        
        # Получаем адрес контракта
        contract_address = tx_receipt.contractAddress
        print(f"Контракт успешно развернут!")
        print(f"   Адрес контракта: {contract_address}")
        print(f"   Номер блока: {tx_receipt.blockNumber}")
        print(f"   Gas использовано: {tx_receipt.gasUsed}")
        
        # Сохраняем адрес контракта
        with open("contract_address.txt", "w") as f:
            f.write(contract_address)
        
        return contract_address, tx_receipt
    
    def get_contract_info(self, contract_address, abi):
        """
        Получает информацию о развернутом контракте
        """
        print(f"\nИнформация о контракте {contract_address}")
        
        # Создаем объект контракта
        contract = self.w3.eth.contract(
            address=self.w3.to_checksum_address(contract_address),
            abi=abi
        )
        
        # Получаем баланс контракта
        balance = self.w3.eth.get_balance(contract_address)
        print(f"   Баланс контракта: {self.w3.from_wei(balance, 'ether')} ETH")
        
        # Получаем код контракта
        code = self.w3.eth.get_code(contract_address)
        print(f"   Размер кода контракта: {len(code)} байт")
        
        return contract

def main():
    """Основная функция для деплоя контракта"""
    
    print("=" * 60)
    print("Деплой смарт-контракта SimpleStorage")
    print("=" * 60)
    
    try:
        # Инициализация деплоера
        deployer = ContractDeployer(
            node_url="http://localhost:8545",
            private_key="0x***"
        )
        
        # Шаг 1: Компиляция контракта
        abi, bytecode = deployer.compile_contract("5/SimpleStorage.sol")
        
        # Шаг 2: Деплой контракта
        contract_address, tx_receipt = deployer.deploy_contract(abi, bytecode, initial_value=100)
        
        # Шаг 3: Получение информации о контракте
        contract = deployer.get_contract_info(contract_address, abi)
        
        print("\nДеплой завершен успешно!")
        print(f"   ABI сохранен в: SimpleStorage_abi.json")
        print(f"   Байткод сохранен в: SimpleStorage_bytecode.txt")
        print(f"   Адрес контракта сохранен в: contract_address.txt")
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
