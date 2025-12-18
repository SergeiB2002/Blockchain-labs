import json
import os
from solcx import compile_standard, install_solc
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware
import time

class ERC20Deployer:
    def __init__(self, node_url="http://127.0.0.1:8545"):
        """
        Инициализация подключения к ноде Geth
        """
        # Подключаемся к локальной ноде Geth
        self.w3 = Web3(Web3.HTTPProvider(node_url))
        
        # Добавляем middleware для работы с Geth dev режимом (PoA)
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        # Проверяем подключение
        if not self.w3.is_connected():
            raise ConnectionError("Не удалось подключиться к ноде Geth")
        
        print(f"✓ Подключено к ноде Geth: {node_url}")
        print(f"  Chain ID: {self.w3.eth.chain_id}")
        print(f"  Блоков в цепи: {self.w3.eth.block_number}")
        
        # Устанавливаем версию Solidity
        self.solc_version = "0.8.0"
        install_solc(self.solc_version)
        
    def get_accounts(self):
        """Получить список доступных аккаунтов"""
        try:
            accounts = self.w3.eth.accounts
            print(f"\nДоступные аккаунты:")
            for i, acc in enumerate(accounts):
                balance = self.w3.eth.get_balance(acc)
                print(f"  [{i}] {acc} - {self.w3.from_wei(balance, 'ether')} ETH")
            return accounts
        except Exception as e:
            print(f"Ошибка получения аккаунтов: {e}")
            return []
    
    def compile_contract(self, contract_path):
        """Компиляция смарт-контракта"""
        print(f"\nКомпиляция контракта из {contract_path}...")
        
        with open(contract_path, 'r') as file:
            contract_source = file.read()
        
        compiled_sol = compile_standard({
            "language": "Solidity",
            "sources": {
                os.path.basename(contract_path): {
                    "content": contract_source
                }
            },
            "settings": {
                "outputSelection": {
                    "*": {
                        "*": ["abi", "metadata", "evm.bytecode"]
                    }
                },
                "optimizer": {
                    "enabled": True,
                    "runs": 200
                }
            }
        }, solc_version=self.solc_version)
        
        # Извлекаем ABI и bytecode
        contract_key = list(compiled_sol['contracts'][os.path.basename(contract_path)].keys())[0]
        contract_data = compiled_sol['contracts'][os.path.basename(contract_path)][contract_key]
        
        abi = contract_data['abi']
        bytecode = contract_data['evm']['bytecode']['object']
        
        print("✓ Контракт скомпилирован успешно")
        return abi, bytecode
    
    def deploy_contract(self, account_index=0, token_name="MyToken", token_symbol="MTK", 
                        decimals=18, initial_supply=1000000):
        """Развертывание контракта"""
        try:
            # Получаем аккаунты
            accounts = self.get_accounts()
            if not accounts:
                raise ValueError("Нет доступных аккаунтов")
            
            deployer = accounts[account_index]
            print(f"\nИспользуем аккаунт для развертывания: {deployer}")
            
            # Компилируем контракт
            contract_path = os.path.join(os.path.dirname(__file__), '..', '6', 'MyToken.sol')
            abi, bytecode = self.compile_contract(contract_path)
            
            # Создаем экземпляр контракта
            Contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
            
            # Получаем nonce
            nonce = self.w3.eth.get_transaction_count(deployer)
            
            # Подготавливаем конструктор
            constructor_args = {
                "name_": token_name,
                "symbol_": token_symbol,
                "decimals_": decimals,
                "initialSupply_": initial_supply
            }
            
            # Строим транзакцию
            transaction = Contract.constructor(
                token_name,
                token_symbol,
                decimals,
                initial_supply
            ).build_transaction({
                'chainId': self.w3.eth.chain_id,
                'gas': 2000000,
                'gasPrice': self.w3.eth.gas_price,
                'nonce': nonce,
                'from': deployer
            })
            
            # В dev режиме Geth аккаунты разблокированы, можно просто отправить
            print(f"\nОтправка транзакции развертывания...")
            tx_hash = self.w3.eth.send_transaction(transaction)
            print(f"  Хэш транзакции: {tx_hash.hex()}")
            
            # Ждем подтверждения
            print("  Ожидание подтверждения...")
            tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            if tx_receipt.status == 1:
                contract_address = tx_receipt.contractAddress
                print(f"\n✓ Контракт успешно развернут!")
                print(f"  Адрес контракта: {contract_address}")
                print(f"  Блок развертывания: {tx_receipt.blockNumber}")
                print(f"  Использовано газа: {tx_receipt.gasUsed}")
                
                # Создаем экземпляр развернутого контракта
                deployed_contract = self.w3.eth.contract(
                    address=contract_address,
                    abi=abi
                )
                
                # Получаем информацию о токене
                print(f"\nИнформация о токене:")
                print(f"  Имя: {deployed_contract.functions.name().call()}")
                print(f"  Символ: {deployed_contract.functions.symbol().call()}")
                print(f"  Десятичных знаков: {deployed_contract.functions.decimals().call()}")
                print(f"  Общая эмиссия: {deployed_contract.functions.totalSupply().call()}")
                print(f"  Баланс владельца: {deployed_contract.functions.balanceOf(deployer).call()}")
                
                return contract_address, abi
            else:
                print("✗ Ошибка при развертывании контракта")
                return None, None
                
        except Exception as e:
            print(f"✗ Ошибка при развертывании: {e}")
            import traceback
            traceback.print_exc()
            return None, None
    
    def interact_with_contract(self, contract_address, abi):
        """Взаимодействие с развернутым контрактом"""
        try:
            contract = self.w3.eth.contract(address=contract_address, abi=abi)
            accounts = self.get_accounts()
            
            if len(accounts) >= 2:
                # Пример передачи токенов между аккаунтами
                sender = accounts[0]
                receiver = accounts[1]
                
                print(f"\nПример взаимодействия:")
                print(f"  Отправитель: {sender}")
                print(f"  Получатель: {receiver}")
                
                # Балансы до перевода
                sender_balance = contract.functions.balanceOf(sender).call()
                receiver_balance = contract.functions.balanceOf(receiver).call()
                
                print(f"  Баланс отправителя: {sender_balance}")
                print(f"  Баланс получателя: {receiver_balance}")
                
                # Перевод токенов
                amount = 100 * 10**18  # 100 токенов
                
                # Строим транзакцию
                nonce = self.w3.eth.get_transaction_count(sender)
                tx = contract.functions.transfer(receiver, amount).build_transaction({
                    'chainId': self.w3.eth.chain_id,
                    'gas': 100000,
                    'gasPrice': self.w3.eth.gas_price,
                    'nonce': nonce,
                    'from': sender
                })
                
                print(f"\nОтправка перевода {amount} токенов...")
                tx_hash = self.w3.eth.send_transaction(tx)
                tx_receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
                
                if tx_receipt.status == 1:
                    print("✓ Перевод успешен!")
                    
                    # Балансы после перевода
                    new_sender_balance = contract.functions.balanceOf(sender).call()
                    new_receiver_balance = contract.functions.balanceOf(receiver).call()
                    
                    print(f"  Новый баланс отправителя: {new_sender_balance}")
                    print(f"  Новый баланс получателя: {new_receiver_balance}")
        
        except Exception as e:
            print(f"Ошибка при взаимодействии: {e}")

def main():
    """Основная функция развертывания"""
    print("=" * 60)
    print("Развертывание ERC20 токена на локальной ноде Geth")
    print("=" * 60)
    
    # Создаем экземпляр деплоера
    deployer = ERC20Deployer()
    
    # Конфигурация токена
    token_config = {
        "name": "MyTestToken",
        "symbol": "MTT",
        "decimals": 18,
        "initial_supply": 1000000  # 1 миллион токенов
    }
    
    # Развертываем контракт
    contract_address, abi = deployer.deploy_contract(
        account_index=0,
        token_name=token_config["name"],
        token_symbol=token_config["symbol"],
        decimals=token_config["decimals"],
        initial_supply=token_config["initial_supply"]
    )
    
    if contract_address and abi:
        # Сохраняем информацию о контракте
        contract_info = {
            "address": contract_address,
            "abi": abi,
            "name": token_config["name"],
            "symbol": token_config["symbol"],
            "decimals": token_config["decimals"],
            "network": "localhost"
        }
        
        with open('deployed_contract.json', 'w') as f:
            json.dump(contract_info, f, indent=2)
        
        print(f"\n✓ Информация о контракте сохранена в deployed_contract.json")
        
        # Демонстрация взаимодействия
        deployer.interact_with_contract(contract_address, abi)
    
    print("\n" + "=" * 60)
    print("Готово!")
    print("=" * 60)

if __name__ == "__main__":
    main()
