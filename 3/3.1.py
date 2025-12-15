from bitcoinrpc.authproxy import AuthServiceProxy, JSONRPCException
import json
from decimal import Decimal

class BitcoinWalletAnalyzer:
    def __init__(self, rpc_user, rpc_password, rpc_host='127.0.0.1', rpc_port=8332, wallet_name=''):
        """
        Инициализация подключения к Bitcoin Core RPC
        
        Args:
            rpc_user: RPC username
            rpc_password: RPC password
            rpc_host: RPC host (default: 127.0.0.1)
            rpc_port: RPC port
            wallet_name: Имя кошелька (если используется несколько кошельков)
        """
        self.rpc_user = rpc_user
        self.rpc_password = rpc_password
        self.rpc_host = rpc_host
        self.rpc_port = rpc_port
        self.wallet_name = wallet_name
        
        # Формируем URL для подключения
        if wallet_name:
            self.rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/wallet/{wallet_name}"
        else:
            self.rpc_url = f"http://{rpc_user}:{rpc_password}@{rpc_host}:{rpc_port}/"
        
        self.rpc_connection = None
    
    def connect(self):
        """Установить соединение с Bitcoin Core"""
        try:
            self.rpc_connection = AuthServiceProxy(self.rpc_url)
            # Проверяем соединение
            info = self.rpc_connection.getblockchaininfo()
            print(f"✓ Подключено к {info['chain']} сети")
            print(f"✓ Блоков: {info['blocks']}")
            return True
        except Exception as e:
            print(f"✗ Ошибка подключения: {e}")
            return False
    
    def get_address_utxo_sum(self, address):
        """
        Получить сумму всех UTXO для указанного адреса
        
        Args:
            address: Bitcoin адрес
        
        Returns:
            dict: {'total_btc': Decimal, 'total_satoshis': int, 'utxo_count': int, 'utxos': list}
        """
        if not self.rpc_connection:
            print("Сначала установите соединение с помощью метода connect()")
            return None
        
        try:
            # Получаем все непотраченные выходы
            unspent = self.rpc_connection.listunspent(0, 9999999, [address])
            
            total_satoshis = 0
            utxos = []
            
            for tx in unspent:
                # Проверяем, что UTXO принадлежит нашему адресу
                if tx['address'] == address:
                    amount_sat = int(Decimal(tx['amount']) * Decimal('1e8'))
                    total_satoshis += amount_sat
                    
                    utxo_info = {
                        'txid': tx['txid'],
                        'vout': tx['vout'],
                        'amount_btc': float(tx['amount']),
                        'amount_sat': amount_sat,
                        'confirmations': tx['confirmations'],
                        'spendable': tx['spendable'],
                        'safe': tx.get('safe', True)
                    }
                    utxos.append(utxo_info)
            
            total_btc = Decimal(total_satoshis) / Decimal('1e8')
            
            result = {
                'address': address,
                'total_btc': total_btc,
                'total_satoshis': total_satoshis,
                'utxo_count': len(utxos),
                'utxos': utxos
            }
            
            return result
            
        except JSONRPCException as e:
            print(f"✗ RPC ошибка: {e}")
            return None
        except Exception as e:
            print(f"✗ Ошибка: {e}")
            return None
    
    def get_wallet_balance(self):
        """Получить общий баланс кошелька"""
        try:
            balance = self.rpc_connection.getbalance()
            return {
                'total_balance_btc': Decimal(balance),
                'total_balance_sat': int(Decimal(balance) * Decimal('1e8'))
            }
        except Exception as e:
            print(f"✗ Ошибка получения баланса: {e}")
            return None
    
    def list_wallet_addresses(self):
        """Получить список адресов в кошельке"""
        try:
            # Получаем адреса из кошелька
            addresses = []
            
            # Получаем адреса с метками
            address_info = self.rpc_connection.listreceivedbyaddress(0, True)
            for addr_info in address_info:
                addresses.append({
                    'address': addr_info['address'],
                    'amount': addr_info['amount'],
                    'confirmations': addr_info['confirmations']
                })
            
            return addresses
        except Exception as e:
            print(f"✗ Ошибка получения адресов: {e}")
            return []

def print_utxo_summary(result):
    """Красиво вывести результат"""
    if not result:
        print("Нет данных для отображения")
        return
    
    print("\n" + "="*60)
    print(f"Анализ UTXO для адреса: {result['address']}")
    print("="*60)
    print(f"Общее количество UTXO: {result['utxo_count']}")
    print(f"Общий баланс: {result['total_btc']:.8f} BTC")
    print(f"Общий баланс: {result['total_satoshis']:,} сатоши")
    print("-"*60)
    
    if result['utxos']:
        print("\nДетали UTXO:")
        print("-"*60)
        for i, utxo in enumerate(result['utxos'], 1):
            print(f"{i}. TXID: {utxo['txid'][:20]}...")
            print(f"   Vout: {utxo['vout']}")
            print(f"   Сумма: {utxo['amount_btc']:.8f} BTC ({utxo['amount_sat']:,} сатоши)")
            print(f"   Подтверждений: {utxo['confirmations']}")
            print(f"   Доступно: {'Да' if utxo['spendable'] else 'Нет'}")
            print("-"*40)
    else:
        print("UTXO не найдены")

def main():
    # Конфигурация для testnet3
    RPC_USER = '***'
    RPC_PASSWORD = '***'
    RPC_HOST = '127.0.0.1'
    RPC_PORT =   # Порт для testnet
    WALLET_NAME = 'mywallet'  # Имя кошелька
    
    TARGET_ADDRESS = 'tb1qfzj8zf78efn054996k0twh9wfjpa9t5kxwu0qz'
    
    print("Bitcoin UTXO Calculator")
    print("="*60)
    
    # Инициализируем анализатор
    analyzer = BitcoinWalletAnalyzer(
        rpc_user=RPC_USER,
        rpc_password=RPC_PASSWORD,
        rpc_host=RPC_HOST,
        rpc_port=RPC_PORT,
        wallet_name=WALLET_NAME
    )
    
    # Подключаемся к Bitcoin Core
    if not analyzer.connect():
        print("Не удалось подключиться к Bitcoin Core")
        return
    
    # Получаем баланс кошелька
    wallet_balance = analyzer.get_wallet_balance()
    if wallet_balance:
        print(f"Баланс кошелька: {wallet_balance['total_balance_btc']:.8f} BTC")
    
    # Получаем сумму UTXO для адреса
    print(f"\nАнализируем адрес: {TARGET_ADDRESS}")
    result = analyzer.get_address_utxo_sum(TARGET_ADDRESS)
    
    # Выводим результат
    if result:
        print_utxo_summary(result)
        
        # Сохраняем в JSON файл
        with open('utxo_analysis.json', 'w') as f:
            json.dump({
                'address': result['address'],
                'total_btc': str(result['total_btc']),
                'total_satoshis': result['total_satoshis'],
                'utxo_count': result['utxo_count'],
                'utxos': result['utxos']
            }, f, indent=2)
        print("\nРезультат сохранен в utxo_analysis.json")
    else:
        print("Не удалось получить данные UTXO")

if __name__ == "__main__":
    main()
