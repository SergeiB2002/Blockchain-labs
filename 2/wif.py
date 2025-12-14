from __future__ import annotations

import argparse
from bip_utils import (
    Bip39SeedGenerator,
    Bip44, Bip49, Bip84,
    Bip44Coins, Bip49Coins, Bip84Coins,
    Bip44Changes,
)
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey

MNEMONIC = "potato..."
MNEMONIC_PASSPHRASE = ""

PURPOSES = [
    ("BIP44", Bip44, Bip44Coins.BITCOIN_TESTNET),
    ("BIP49", Bip49, Bip49Coins.BITCOIN_TESTNET),
    ("BIP84", Bip84, Bip84Coins.BITCOIN_TESTNET),
]


def iter_paths(seed_bytes: bytes, account_max: int, scan: int, include_internal: bool):
    for pur_name, PurCls, coin_enum in PURPOSES:
        ctx = PurCls.FromSeed(seed_bytes, coin_enum)
        base = ctx.Purpose().Coin()

        for account in range(account_max + 1):
            acc = base.Account(account)

            changes = [Bip44Changes.CHAIN_EXT]
            if include_internal:
                changes.append(Bip44Changes.CHAIN_INT)

            for ch_enum in changes:
                ch = acc.Change(ch_enum)
                for index in range(scan + 1):
                    wif = ch.AddressIndex(index).PrivateKey().ToWif()
                    yield pur_name, account, (0 if ch_enum == Bip44Changes.CHAIN_EXT else 1), index, wif


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--addr", required=True, help="tb1q... address to find")
    ap.add_argument("--scan", type=int, default=5000, help="max index to scan")
    ap.add_argument("--account-max", type=int, default=10, help="max account (0..N)")
    ap.add_argument("--include-internal", action="store_true", help="also scan change=1")
    args = ap.parse_args()

    setup("testnet")

    target = args.addr.strip().lower()
    if not target.startswith("tb1q"):
        raise SystemExit("Ожидается tb1q...")

    seed_bytes = Bip39SeedGenerator(MNEMONIC).Generate(MNEMONIC_PASSPHRASE)

    checked = 0
    for pur, account, change, index, wif in iter_paths(
        seed_bytes,
        args.account_max,
        args.scan,
        args.include_internal,
    ):
        checked += 1

        priv = PrivateKey(wif)
        pub = priv.get_public_key()
        addr = pub.get_segwit_address().to_string().lower()

        if addr == target:
            print("\nFOUND!")
            print("purpose:", pur)
            print("path:", f"m/{ {'BIP44':44,'BIP49':49,'BIP84':84}[pur] }'/1'/{account}'/{change}/{index}")
            print("wif:", wif)
            return

        if checked % 50000 == 0:
            print(f"checked {checked} keys... last={pur} a={account} c={change} i={index}")

    raise SystemExit(
        "\nНЕ НАЙДЕНО.\n"
    )
if __name__ == "__main__":
    main()
