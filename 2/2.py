#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from typing import List, Tuple

import requests
from bitcoinutils.setup import setup
from bitcoinutils.transactions import Transaction, TxInput, TxOutput, TxWitnessInput
from bitcoinutils.keys import PrivateKey, P2wpkhAddress
from bitcoinutils.script import Script


WIF = "cTq..."

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
        raise RuntimeError(f"Broadcast failed: HTTP {r.status_code}\nResponse: {r.text}\n")
    return r.text.strip()


def fetch_utxos(address: str) -> List[UTXO]:
    data = http_get_json(f"{MEMPOOL_TESTNET4}/address/{address}/utxo")
    utxos = [UTXO(txid=x["txid"], vout=int(x["vout"]), value=int(x["value"])) for x in data]
    utxos.sort(key=lambda u: u.value, reverse=True)
    return utxos


def fetch_fee_rate_sat_vb() -> int:
    fees = http_get_json(f"{MEMPOOL_TESTNET4}/v1/fees/recommended")
    return int(fees.get("halfHourFee", fees.get("minimumFee", 1)))


def estimate_vbytes_p2wpkh(n_in: int, n_out: int) -> int:
    # приближённо, достаточно для практики
    return 10 + n_in * 68 + n_out * 31


def select_coins(utxos: List[UTXO], target_plus_fee: int) -> Tuple[List[UTXO], int]:
    picked, total = [], 0
    for u in utxos:
        picked.append(u)
        total += u.value
        if total >= target_plus_fee:
            return picked, total
    raise RuntimeError("Недостаточно средств (UTXO) для суммы + комиссии")

def main():
    parser = argparse.ArgumentParser(description="Create/sign/broadcast a Bitcoin testnet4 P2WPKH tx (tb1q -> tb1q)")
    parser.add_argument("--to", required=True, help="Recipient address (tb1q...)")
    parser.add_argument("--amount-sats", type=int, required=True, help="Amount to send in satoshis")
    parser.add_argument("--fee-rate", type=int, default=0, help="Fee rate in sat/vB (0 = auto)")
    parser.add_argument("--rbf", action="store_true", help="Enable RBF")
    parser.add_argument("--broadcast", action="store_true", help="Broadcast via mempool.space testnet4")
    parser.add_argument("--dry-run", action="store_true", help="Just print raw tx/txid, do not broadcast")
    args = parser.parse_args()

    if not WIF or WIF.startswith("cV....") or len(WIF) < 20:
        print("ERROR: Set WIF constant in code (testnet WIF).", file=sys.stderr)
        sys.exit(2)

    if not args.to.startswith("tb1q"):
        raise RuntimeError("Ожидается адрес получателя tb1q... (P2WPKH).")

    send_value = int(args.amount_sats)
    if send_value <= 0:
        raise RuntimeError("amount-sats должен быть > 0")

    setup("testnet")

    priv = PrivateKey(WIF)
    pub = priv.get_public_key()
    from_addr_obj = pub.get_segwit_address()  # tb1q...
    from_addr = from_addr_obj.to_string()

    fee_rate = args.fee_rate if args.fee_rate > 0 else fetch_fee_rate_sat_vb()
    utxos = fetch_utxos(from_addr)
    if not utxos:
        raise RuntimeError(f"Нет UTXO на адресе {from_addr}. Пополните testnet4 BTC.")

    to_addr_obj = P2wpkhAddress(args.to)

    # подберём UTXO итеративно
    n_in_guess = 1
    while True:
        vbytes_guess = estimate_vbytes_p2wpkh(n_in_guess, 2)  # to + change
        fee_guess = fee_rate * vbytes_guess
        picked, picked_total = select_coins(utxos, send_value + fee_guess)
        if len(picked) == n_in_guess:
            break
        n_in_guess = len(picked)

    # финальный расчёт
    vbytes = estimate_vbytes_p2wpkh(len(picked), 2)
    fee = fee_rate * vbytes
    change = picked_total - send_value - fee

    dust_like = 330
    include_change = change >= dust_like

    outputs: List[TxOutput] = [TxOutput(send_value, to_addr_obj.to_script_pub_key())]
    if include_change:
        outputs.append(TxOutput(change, from_addr_obj.to_script_pub_key()))
    else:
        fee = picked_total - send_value
        change = 0

    txins: List[TxInput] = []
    for u in picked:
        txin = TxInput(u.txid, u.vout)
        if args.rbf:
            txin.sequence = 0xFFFFFFFD
        txins.append(txin)

    tx = Transaction(txins, outputs, has_segwit=True)

    # scriptCode для P2WPKH
    h160 = pub.to_hash160()
    script_code = Script(["OP_DUP", "OP_HASH160", h160, "OP_EQUALVERIFY", "OP_CHECKSIG"])

    tx.witnesses = []
    for idx, u in enumerate(picked):
        sig = priv.sign_segwit_input(tx, idx, script_code, u.value)
        tx.witnesses.append(TxWitnessInput([sig, pub.to_hex()]))

    raw = tx.serialize()
    txid = tx.get_txid()

    print("FROM:", from_addr)
    print("TO:  ", args.to)
    print("fee_rate(sat/vB):", fee_rate)
    print("inputs:")
    for u in picked:
        print(f"  - {u.txid}:{u.vout} value={u.value}")
    print("outputs:")
    print("  - to:", send_value)
    if include_change:
        print("  - change:", change)
    print("fee(sats):", fee)
    print("txid:", txid)
    print("raw:", raw)

    if args.dry_run and not args.broadcast:
        return

    if args.broadcast:
        result = http_post_text(f"{MEMPOOL_TESTNET4}/tx", raw)
        print("broadcast:", result)


if __name__ == "__main__":
    main()
