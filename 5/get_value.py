import json
from web3 import Web3
from web3.middleware import ExtraDataToPOAMiddleware

class ContractReader:
    def __init__(self, node_url=None, contract_address=None):
        """
        Инициализация для чтения данных из контракта
        """
        self.node_url = node_url or "http://localhost:8545"
        self.w3 = Web3(Web3.HTTPProvider(self.node_url))
        self.w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
        
        if not self.w3.is_connected():
            raise ConnectionError("Не удалось подключиться к ноде")
        
        print(f"Подключено к ноде Ethereum")
        
        # Загрузка адреса контракта
        if contract_address:
            self.contract_address = contract_address
        else:
            try:
                with open("contract_address.txt", "r") as f:
                    self.contract_address = f.read().strip()
            except:
                raise ValueError("Адрес контракта не найден. Укажите его вручную или убедитесь что contract_address.txt существует")
        
        self.contract_address = self.w3.to_checksum_address(self.contract_address)
        
        # Загрузка ABI
        try:
            with open("SimpleStorage_abi.json", "r") as f:
                self.abi = json.load(f)
        except:
            raise ValueError("ABI не найден. Сначала скомпилируйте контракт")
        
        # Создание объекта контракта
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )
    
    def get_current_value(self):
        """
        Вызывает метод get() контракта для получения текущего значения
        """
        print(f"\nПолучение текущего значения из контракта...")
        print(f"   Адрес контракта: {self.contract_address}")
        
        try:
            # Вызов метода get() (read-only, не требует газа)
            current_value = self.contract.functions.get().call()
            print(f"Текущее значение в контракте: {current_value}")
            return current_value
        except Exception as e:
            print(f"Ошибка при получении значения: {e}")
            return None
    
    def get_contract_info(self):
        """
        Получает дополнительную информацию о контракте
        """
        print(f"\nДополнительная информация о контракте:")
        
        # Баланс контракта
        balance = self.w3.eth.get_balance(self.contract_address)
        print(f"   Баланс контракта: {self.w3.from_wei(balance, 'ether')} ETH")
        
        # Код контракта
        code = self.w3.eth.get_code(self.contract_address)
        print(f"   Размер кода: {len(code)} байт")

def main():
    """Основная функция для чтения значения из контракта"""
    
    print("=" * 60)
    print("Чтение значения из смарт-контракта SimpleStorage")
    print("=" * 60)
    
    try:
        # Инициализация ридера
        reader = ContractReader(
            node_url="http://localhost:8545"
        )
        
        # Получение текущего значения
        value = reader.get_current_value()
        
        # Дополнительная информация
        reader.get_contract_info()
        
    except Exception as e:
        print(f"\nОшибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
