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

export type NFTItemConfig = {};

export function nFTItemConfigToCell(config: NFTItemConfig): Cell {
    return beginCell().endCell();
}

export class NFTItem implements Contract {
    abi: ContractABI = { name: 'NFTItem' };

    constructor(readonly address: Address, readonly init?: { code: Cell; data: Cell }) {}

    static createFromAddress(address: Address) {
        return new NFTItem(address);
    }

    static createFromConfig(config: NFTItemConfig, code: Cell, workchain = 0) {
        const data = nFTItemConfigToCell(config);
        const init = { code, data };
        return new NFTItem(contractAddress(workchain, init), init);
    }

    async sendDeploy(provider: ContractProvider, via: Sender, value: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().endCell(),
        });
    }

    // OP_TRANSFER = 0x5fcc3d14, body: op(32) + new_owner(Address)
    async sendTransfer(provider: ContractProvider, via: Sender, value: bigint, newOwner: Address) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().storeUint(0x5fcc3d14, 32).storeAddress(newOwner).endCell(),
        });
    }
}
