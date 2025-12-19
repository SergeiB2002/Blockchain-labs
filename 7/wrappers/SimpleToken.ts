import {
    Address,
    beginCell,
    Cell,
    Contract,
    ContractABI,
    contractAddress,
    ContractProvider,
    Sender,
    SendMode,
} from '@ton/core';

export type SimpleTokenConfig = {
    owner: Address;
};

export function simpleTokenConfigToCell(config: SimpleTokenConfig): Cell {
    return beginCell()
        .storeAddress(config.owner)
        .storeUint(0n, 128)               // total_supply
        .storeRef(beginCell().endCell())  // empty dict cell
        .endCell();
}

export class SimpleToken implements Contract {
    abi: ContractABI = { name: 'SimpleToken' };

    constructor(readonly address: Address, readonly init?: { code: Cell; data: Cell }) {}

    static createFromAddress(address: Address) {
        return new SimpleToken(address);
    }

    static createFromConfig(config: SimpleTokenConfig, code: Cell, workchain = 0) {
        const data = simpleTokenConfigToCell(config);
        const init = { code, data };
        return new SimpleToken(contractAddress(workchain, init), init);
    }

    async sendDeploy(provider: ContractProvider, via: Sender, value: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().endCell(),
        });
    }

    async sendMint(provider: ContractProvider, via: Sender, value: bigint, to: Address, amount: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell()
                .storeUint(0x4d494e54, 32) // MINT
                .storeAddress(to)
                .storeUint(amount, 128)
                .endCell(),
        });
    }

    async sendTransfer(provider: ContractProvider, via: Sender, value: bigint, to: Address, amount: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell()
                .storeUint(0x5452414e, 32) // TRAN
                .storeAddress(to)
                .storeUint(amount, 128)
                .endCell(),
        });
    }
}
