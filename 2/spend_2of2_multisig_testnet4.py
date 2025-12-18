from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple
import requests
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import PrivateKey, P2wpkhAddress, P2wshAddress
from bitcoinutils.script import Script


# WIF двух участников (testnet)
WIF1 = "cT..."
WIF2 = "cT..."

# witnessScript (2-of-2) из gen_2of2_multisig.py
WITNESS_SCRIPT_HEX = "52...ae"

# адрес получателя (P2WPKH tb1q...)
TO_ADDRESS = "tb1q..."

# сумма перевода
AMOUNT_SATS = 25000

# комиссия (0 = авто)
FEE_RATE_SAT_VB = 0

# отправлять ли транзакцию
BROADCAST = True

MEMPOOL_TESTNET4 = "https://mempool.space/testnet4/api"


@dataclass(frozen=True)
class UTXO:
    txid: str
    vout: int
    value: int  # satoshis


def http_get_json(url: str, timeout: int = 20):
    r = requests.get(url, timeout=timeout)
    r.raise_for_status()
    return r.json()


def http_post_text(url: str, body: str, timeout: int = 20):
    r = requests.post(url, data=body.encode("utf-8"), timeout=timeout)
    if not r.ok:
        raise RuntimeError(
            f"Broadcast failed: HTTP {r.status_code}\nResponse: {r.text}\n"
        )
    return r.text.strip()


def fetch_utxos(address: str) -> List[UTXO]:
    data = http_get_json(f"{MEMPOOL_TESTNET4}/address/{address}/utxo")
    utxos = [
        UTXO(txid=x["txid"], vout=int(x["vout"]), value=int(x["value"]))
        for x in data
    ]
    utxos.sort(key=lambda u: u.value, reverse=True)
    return utxos


def fetch_fee_rate_sat_vb() -> int:
    fees = http_get_json(f"{MEMPOOL_TESTNET4}/v1/fees/recommended")
    return int(fees.get("halfHourFee", fees.get("minimumFee", 1)))


def estimate_vbytes_p2wsh_2of2(n_in: int, n_out: int) -> int:
    # Приближённая оценка для P2WSH 2-of-2
    return 10 + n_in * 110 + n_out * 31


def select_coins(utxos: List[UTXO], target_plus_fee: int) -> Tuple[List[UTXO], int]:
    picked, total = [], 0
    for u in utxos:
        picked.append(u)
        total += u.value
        if total >= target_plus_fee:
            return picked, total
    raise RuntimeError("Недостаточно средств (UTXO) для суммы + комиссии")


def main():
    setup("testnet")

    # ключи участников
    k1 = PrivateKey(WIF1)
    k2 = PrivateKey(WIF2)

    # восстановление witnessScript и multisig-адреса
    witness_script = Script.from_raw(WITNESS_SCRIPT_HEX)
    ms_addr = P2wshAddress.from_script(witness_script)
    ms_addr_str = ms_addr.to_string()

    # комиссия
    fee_rate = FEE_RATE_SAT_VB if FEE_RATE_SAT_VB > 0 else fetch_fee_rate_sat_vb()

    # UTXO multisig-адреса
    utxos = fetch_utxos(ms_addr_str)
    if not utxos:
        raise RuntimeError(f"Нет UTXO на multisig-адресе {ms_addr_str}")

    if not TO_ADDRESS.startswith("tb1q"):
        raise RuntimeError("Ожидается адрес получателя tb1q... (P2WPKH)")

    send_value = int(AMOUNT_SATS)
    if send_value <= 0:
        raise RuntimeError("AMOUNT_SATS должен быть > 0")

    to_addr = P2wpkhAddress(TO_ADDRESS)

    # подбор входов
    n_in_guess = 1
    while True:
        vbytes_guess = estimate_vbytes_p2wsh_2of2(n_in_guess, 2)
        fee_guess = fee_rate * vbytes_guess
        picked, picked_total = select_coins(utxos, send_value + fee_guess)
        if len(picked) == n_in_guess:
            break
        n_in_guess = len(picked)

    vbytes = estimate_vbytes_p2wsh_2of2(len(picked), 2)
    fee = fee_rate * vbytes + 2  # небольшой запас
    change = picked_total - send_value - fee

    dust_like = 330
    include_change = change >= dust_like

    outputs: List[TxOutput] = [TxOutput(send_value, to_addr.to_script_pub_key())]
    if include_change:
        outputs.append(TxOutput(change, ms_addr.to_script_pub_key()))
    else:
        fee = picked_total - send_value
        change = 0

    txins: List[TxInput] = [TxInput(u.txid, u.vout) for u in picked]
    tx = Transaction(txins, outputs, has_segwit=True)

    # для P2WSH scriptCode = witnessScript
    script_code = witness_script

    # подписи двумя ключами
    tx.witnesses = []
    for idx, u in enumerate(picked):
        sig1 = k1.sign_segwit_input(tx, idx, script_code, u.value)
        sig2 = k2.sign_segwit_input(tx, idx, script_code, u.value)

        # witness stack: OP_0, sig1, sig2, witnessScript
        tx.witnesses.append(
            TxWitnessInput(["", sig1, sig2, WITNESS_SCRIPT_HEX])
        )

    raw = tx.serialize()
    txid = tx.get_txid()

    print("FROM multisig:", ms_addr_str)
    print("TO:", TO_ADDRESS)
    print("fee_rate(sat/vB):", fee_rate)
    print("fee(sats):", fee)
    print("txid:", txid)
    print("raw:", raw)

    if BROADCAST:
        res = http_post_text(f"{MEMPOOL_TESTNET4}/tx", raw)
        print("broadcast:", res)


if __name__ == "__main__":
    main()
