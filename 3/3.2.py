from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
from decimal import Decimal
import time

# ========== НАСТРОЙКИ ==========
RPC_USER = ""  
RPC_PASSWORD = ""  
RPC_HOST = "127.0.0.1"
RPC_PORT = 48332  
WALLET_NAME = "mywallet" 

# Адрес для отправки
TO_ADDRESS = "tb1qe6lzszgmh4p9n7ndch9u99d4npmw7754ctzy3r"

# ========== ОСНОВНОЙ КЛАСС ==========
class BitcoinTx:
    def __init__(self):
        self.rpc = None
        1
    def connect(self):
        """Подключиться к Bitcoin Core"""
        try:
            url = f"http://{RPC_USER}:{RPC_PASSWORD}@{RPC_HOST}:{RPC_PORT}/"
            if WALLET_NAME:
                url += f"wallet/{WALLET_NAME}"
            
            self.rpc = AuthServiceProxy(url)
            
            # Проверяем подключение
            info = self.rpc.getblockchaininfo()
            print(f"✓ Подключено к {info['chain']} сети")
            print(f"✓ Блоков: {info['blocks']}")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            return False
    
    def get_balance(self):
        """Получить баланс кошелька"""
        try:
            balance = self.rpc.getbalance()
            unconfirmed = self.rpc.getunconfirmedbalance()
            
            print(f"Баланс: {balance:.8f} BTC")
            print(f"Неподтвержденный: {unconfirmed:.8f} BTC")
            
            # Конвертируем в сатоши для удобства
            balance_sat = int(balance * Decimal('100000000'))
            print(f"Баланс в сатоши: {balance_sat:,}")
            
            return balance
        except Exception as e:
            print(f"Ошибка получения баланса: {e}")
            return 0
    
    def get_utxos(self):
        """Получить все UTXO"""
        try:
            utxos = self.rpc.listunspent(1)  # минимум 1 подтверждение
            total = Decimal('0')
            
            print(f"\nНайдено {len(utxos)} UTXO:")
            for i, utxo in enumerate(utxos[:10], 1):  # показываем первые 10
                amount_sat = int(Decimal(str(utxo['amount'])) * Decimal('100000000'))
                print(f"{i:2}. {utxo['txid'][:16]}... - {utxo['amount']:.8f} BTC "
                      f"({amount_sat:,} sat) - {utxo['confirmations']} conf")
                total += Decimal(str(utxo['amount']))
            
            if len(utxos) > 10:
                print(f"... и еще {len(utxos) - 10} UTXO")
            
            total_sat = int(total * Decimal('100000000'))
            print(f"\nОбщая сумма UTXO: {total:.8f} BTC ({total_sat:,} сатоши)")
            
            return utxos
        except Exception as e:
            print(f"Ошибка получения UTXO: {e}")
            return []
    
    def send_transaction(self, to_address, amount_btc):
        """
        Отправить транзакцию - ПРАВИЛЬНЫЙ СПОСОБ
        
        Args:
            to_address: адрес получателя
            amount_btc: сумма в BTC (Decimal или float)
        
        Returns:
            txid: ID транзакции или None в случае ошибки
        """
        print(f"\n{'='*60}")
        print("ОТПРАВКА ТРАНЗАКЦИИ")
        print(f"{'='*60}")
        
        # Конвертируем в Decimal для точных расчетов
        if not isinstance(amount_btc, Decimal):
            amount_btc = Decimal(str(amount_btc))
        
        print(f"Получатель: {to_address}")
        print(f"Сумма: {amount_btc:.8f} BTC")
        
        try:
            # 1. Получаем текущий баланс
            balance = Decimal(str(self.rpc.getbalance()))
            print(f"Баланс кошелька: {balance:.8f} BTC")
            
            if balance < amount_btc:
                print(f"✗ Недостаточно средств!")
                print(f"  Нужно: {amount_btc:.8f} BTC")
                print(f"  Есть: {balance:.8f} BTC")
                return None
            
            print("Создаем транзакцию...")
            
            # 2. Создаем выходы транзакции
            outputs = {
                to_address: float(amount_btc)
            }
            
            # 3. Создаем сырую транзакцию
            raw_tx = self.rpc.createrawtransaction([], outputs)
            
            # 4. Пополняем транзакцию (автоматически выбирает UTXO)
            print("Выбираем UTXO...")
            funded = self.rpc.fundrawtransaction(raw_tx)
            
            fee = abs(funded['fee'])
            print(f"Комиссия: {fee:.8f} BTC")
            print(f"Размер транзакции: {funded.get('vsize', '?')} vB")
            
            # 5. Подписываем транзакцию
            print("Подписываем...")
            signed = self.rpc.signrawtransactionwithwallet(funded['hex'])
            
            if not signed['complete']:
                print("✗ Транзакция не полностью подписана!")
                return None
            
            # 6. Проверяем транзакцию
            decoded = self.rpc.decoderawtransaction(signed['hex'])
            print(f"Входов: {len(decoded['vin'])}")
            print(f"Выходов: {len(decoded['vout'])}")
            
            # 7. Отправляем транзакцию
            print("Отправляем в сеть...")
            txid = self.rpc.sendrawtransaction(signed['hex'])
            
            print(f"\n{'='*60}")
            print(f"✓ ТРАНЗАКЦИЯ УСПЕШНО ОТПРАВЛЕНА!")
            print(f"{'='*60}")
            print(f"TXID: {txid}")
            
            # 8. Сохраняем информацию о транзакции
            self.save_transaction_info(txid, to_address, amount_btc, fee)
            
            return txid
            
        except JSONRPCException as e:
            print(f"✗ Ошибка RPC: {e}")
            return None
        except Exception as e:
            print(f"✗ Неизвестная ошибка: {e}")
            return None
    
    def send_transaction_with_custom_fee(self, to_address, amount_btc, fee_rate):
        """
        Отправить транзакцию с указанием комиссии
        
        Args:
            to_address: адрес получателя
            amount_btc: сумма в BTC
            fee_rate: комиссия в sat/vB
        
        Returns:
            txid: ID транзакции или None в случае ошибки
        """
        print(f"\n{'='*60}")
        print("ОТПРАВКА ТРАНЗАКЦИИ С УКАЗАНИЕМ КОМИССИИ")
        print(f"{'='*60}")
        
        # Конвертируем в Decimal для точных расчетов
        if not isinstance(amount_btc, Decimal):
            amount_btc = Decimal(str(amount_btc))
        
        print(f"Получатель: {to_address}")
        print(f"Сумма: {amount_btc:.8f} BTC")
        print(f"Комиссия: {fee_rate} sat/vB")
        
        try:
            # 1. Получаем текущий баланс
            balance = Decimal(str(self.rpc.getbalance()))
            print(f"Баланс кошелька: {balance:.8f} BTC")
            
            if balance < amount_btc:
                print(f"✗ Недостаточно средств!")
                print(f"  Нужно: {amount_btc:.8f} BTC")
                print(f"  Есть: {balance:.8f} BTC")
                return None
            
            print("Создаем транзакцию...")
            
            # 2. Создаем выходы транзакции
            outputs = {
                to_address: float(amount_btc)
            }
            
            # 3. Создаем сырую транзакцию
            raw_tx = self.rpc.createrawtransaction([], outputs)
            
            # 4. Пополняем транзакцию с указанием комиссии
            print("Выбираем UTXO с указанной комиссией...")
            options = {'feeRate': fee_rate}
            funded = self.rpc.fundrawtransaction(raw_tx, options)
            
            fee = abs(funded['fee'])
            print(f"Фактическая комиссия: {fee:.8f} BTC")
            print(f"Размер транзакции: {funded.get('vsize', '?')} vB")
            
            # 5. Подписываем транзакцию
            print("Подписываем...")
            signed = self.rpc.signrawtransactionwithwallet(funded['hex'])
            
            if not signed['complete']:
                print("✗ Транзакция не полностью подписана!")
                return None
            
            # 6. Отправляем транзакцию
            print("Отправляем в сеть...")
            txid = self.rpc.sendrawtransaction(signed['hex'])
            
            print(f"\n{'='*60}")
            print(f"✓ ТРАНЗАКЦИЯ УСПЕШНО ОТПРАВЛЕНА!")
            print(f"{'='*60}")
            print(f"TXID: {txid}")
            
            # 7. Сохраняем информацию о транзакции
            self.save_transaction_info(txid, to_address, amount_btc, fee)
            
            return txid
            
        except JSONRPCException as e:
            print(f"✗ Ошибка RPC: {e}")
            return None
        except Exception as e:
            print(f"✗ Неизвестная ошибка: {e}")
            return None
    
    def save_transaction_info(self, txid, to_address, amount, fee):
        """Сохранить информацию о транзакции"""
        with open('transaction.log', 'a') as f:
            f.write(f"[{time.ctime()}] SEND\n")
            f.write(f"TXID: {txid}\n")
            f.write(f"To: {to_address}\n")
            f.write(f"Amount: {amount:.8f} BTC\n")
            f.write(f"Fee: {fee:.8f} BTC\n")
            f.write("-" * 50 + "\n")
        
        print(f"✓ Информация сохранена в transaction.log")
    
    def wait_for_funds(self, target_amount_btc, timeout_minutes=10):
        """
        Ждать поступления средств на кошелек
        
        Args:
            target_amount_btc: целевая сумма в BTC
            timeout_minutes: время ожидания в минутах
        
        Returns:
            bool: True если средства поступили, False если таймаут
        """
        print(f"\nОжидание поступления {target_amount_btc:.8f} BTC...")
        print(f"Таймаут: {timeout_minutes} минут")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                balance = Decimal(str(self.rpc.getbalance()))
                
                if balance >= target_amount_btc:
                    print(f"✓ Средства поступили! Баланс: {balance:.8f} BTC")
                    return True
                
                # Проверяем UTXO
                utxos = self.rpc.listunspent(0)  # включая неподтвержденные
                if utxos:
                    print(f"Найдено {len(utxos)} UTXO")
                    for utxo in utxos[:3]:
                        print(f"  {utxo['amount']:.8f} BTC ({utxo['confirmations']} conf)")
                
                print(f"Текущий баланс: {balance:.8f} BTC - ждем...")
                time.sleep(30)  # Проверяем каждые 30 секунд
                
            except Exception as e:
                print(f"Ошибка проверки баланса: {e}")
                time.sleep(30)
        
        print(f"✗ Таймаут ожидания средств")
        return False
    
    def wait_for_confirmation(self, txid, timeout_minutes=30):
        """
        Ждать подтверждения транзакции
        
        Args:
            txid: ID транзакции
            timeout_minutes: время ожидания в минутах
        
        Returns:
            int: количество подтверждений или 0 если таймаут
        """
        print(f"\n⏳ Ожидание подтверждения транзакции...")
        print(f"TXID: {txid[:20]}...")
        
        start_time = time.time()
        timeout_seconds = timeout_minutes * 60
        
        while time.time() - start_time < timeout_seconds:
            try:
                tx_info = self.rpc.gettransaction(txid)
                confirmations = tx_info.get('confirmations', 0)
                
                if confirmations > 0:
                    print(f"✓ Транзакция подтверждена! Подтверждений: {confirmations}")
                    return confirmations
                
                print(f"  Ждем... (прошло {int(time.time() - start_time)} сек)")
                time.sleep(10)
                
            except JSONRPCException:
                # Транзакция еще может не быть в кошельке
                time.sleep(10)
            except Exception as e:
                print(f"  Ошибка проверки: {e}")
                time.sleep(10)
        
        print(f"✗ Таймаут ожидания подтверждения")
        return 0
    
    def get_transaction_details(self, txid):
        """
        Получить детали транзакции
        
        Args:
            txid: ID транзакции
        
        Returns:
            dict: информация о транзакции или None
        """
        try:
            tx_info = self.rpc.gettransaction(txid)
            
            print(f"\nДетали транзакции:")
            print(f"TXID: {txid}")
            print(f"Подтверждений: {tx_info.get('confirmations', 0)}")
            print(f"Дата: {time.ctime(tx_info.get('time', time.time()))}")
            
            if 'fee' in tx_info:
                print(f"Комиссия: {abs(tx_info['fee']):.8f} BTC")
            
            print(f"\nДетали:")
            print(f"  Размер: {tx_info.get('size', 'N/A')} байт")
            print(f"  Версия: {tx_info.get('version', 'N/A')}")
            print(f"  Locktime: {tx_info.get('locktime', 'N/A')}")
            
            return tx_info
        except Exception as e:
            print(f"✗ Ошибка получения деталей транзакции: {e}")
            return None

# ========== ГЛАВНАЯ ФУНКЦИЯ ==========
def main():
    print("БИТКОИН ТРАНЗАКЦИИ - TESTNET")
    print("="*60)
    
    # Создаем объект
    bitcoin = BitcoinTx()
    
    # Подключаемся
    if not bitcoin.connect():
        print("Не удалось подключиться к Bitcoin Core")
        return
    
    # Показываем баланс
    print("\n1. БАЛАНС КОШЕЛЬКА")
    balance = bitcoin.get_balance()
    
    # Показываем UTXO
    print("\n2. UTXO (НЕПОТРАЧЕННЫЕ ВЫХОДЫ)")
    utxos = bitcoin.get_utxos()
    
    # Если баланс нулевой, ждем поступления средств
    if balance <= Decimal('0'):
        print("\nБаланс нулевой. Нужно получить тестовые биткоины.")
        print("Получите тестовые BTC через краны:")
        print("1. https://testnet-faucet.com/btc-testnet/")
        print("2. https://bitcoinfaucet.uo1.net/")
        print("3. https://testnet.help/en/btcfaucet/testnet")
        
        # Ждем поступления средств
        bitcoin.wait_for_funds(Decimal('0.0001'), timeout_minutes=5)
        
        # Обновляем баланс
        balance = bitcoin.get_balance()
        utxos = bitcoin.get_utxos()
    
    # Меню выбора действия
    print("\n" + "="*60)
    print("МЕНЮ:")
    print("="*60)
    
    if balance >= Decimal('0.0001'):
        print("1. Отправить 0.0001 BTC (10,000 sat)")
        print("2. Отправить произвольную сумму")
        print("3. Отправить с указанием комиссии")
    else:
        print("1. [НЕДОСТУПНО] Недостаточно средств")
        print("2. [НЕДОСТУПНО] Недостаточно средств")
        print("3. [НЕДОСТУПНО] Недостаточно средств")
    
    print("4. Проверить баланс и UTXO")
    print("5. Выйти")
    
    try:
        choice = input("\nВаш выбор: ").strip()
        
        if choice == "1" and balance >= Decimal('0.0001'):
            # Отправляем 0.0001 BTC
            amount = Decimal('0.0001')
            print(f"\nОтправка {amount:.8f} BTC на {TO_ADDRESS}")
            
            confirm = input(f"Подтвердить отправку {amount:.8f} BTC? (y/n): ").lower()
            if confirm == 'y':
                txid = bitcoin.send_transaction(TO_ADDRESS, amount)
                if txid:
                    # Ждем подтверждения
                    bitcoin.wait_for_confirmation(txid, timeout_minutes=2)
        
        elif choice == "2" and balance > Decimal('0'):
            # Отправляем произвольную сумму
            try:
                amount_str = input("Введите сумму в BTC (например 0.0001): ").strip()
                amount = Decimal(amount_str)
                
                if amount <= Decimal('0'):
                    print("Сумма должна быть больше 0")
                elif amount > balance:
                    print(f"Недостаточно средств. Максимум: {balance:.8f} BTC")
                else:
                    print(f"\nОтправка {amount:.8f} BTC на {TO_ADDRESS}")
                    confirm = input(f"Подтвердить? (y/n): ").lower()
                    if confirm == 'y':
                        txid = bitcoin.send_transaction(TO_ADDRESS, amount)
                        if txid:
                            bitcoin.wait_for_confirmation(txid, timeout_minutes=2)
            except:
                print("Неверный формат суммы")
        
        elif choice == "3" and balance > Decimal('0'):
            # Отправляем с указанием комиссии
            try:
                amount_str = input("Введите сумму в BTC (например 0.0001): ").strip()
                amount = Decimal(amount_str)
                
                if amount <= Decimal('0'):
                    print("Сумма должна быть больше 0")
                elif amount > balance:
                    print(f"Недостаточно средств. Максимум: {balance:.8f} BTC")
                else:
                    fee_str = input("Введите комиссию в sat/vB (например 2.0): ").strip()
                    fee_rate = float(fee_str)
                    
                    print(f"\nОтправка {amount:.8f} BTC на {TO_ADDRESS}")
                    print(f"Комиссия: {fee_rate} sat/vB")
                    
                    confirm = input(f"Подтвердить? (y/n): ").lower()
                    if confirm == 'y':
                        txid = bitcoin.send_transaction_with_custom_fee(TO_ADDRESS, amount, fee_rate)
                        if txid:
                            bitcoin.wait_for_confirmation(txid, timeout_minutes=2)
            except:
                print("Неверный формат суммы или комиссии")
        
        elif choice == "4":
            # Обновляем информацию
            print("\nОБНОВЛЕНИЕ ИНФОРМАЦИИ")
            bitcoin.get_balance()
            bitcoin.get_utxos()
        
        elif choice == "5":
            print("Выход...")
        
        else:
            print("Неверный выбор или действие недоступно")
    
    except KeyboardInterrupt:
        print("\n\nОтменено пользователем")
    
    print("\n" + "="*60)
    print("ПРОГРАММА ЗАВЕРШЕНА")
    print("Проверьте файлы:")
    print("- transaction.log - история отправок")
    print("="*60)

# ========== ЗАПУСК ПРОГРАММЫ ==========
if __name__ == "__main__":
    main()
