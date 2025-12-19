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

export type NFTCollectionConfig = {
    owner: Address;
    nextIndex?: bigint; // default 0
    itemCode: Cell;     // code cell of NFTItem
};

export function nFTCollectionConfigToCell(config: NFTCollectionConfig): Cell {
    return beginCell()
        .storeAddress(config.owner)
        .storeUint(config.nextIndex ?? 0n, 64)
        .storeRef(config.itemCode)
        .endCell();
}

export class NFTCollection implements Contract {
    abi: ContractABI = { name: 'NFTCollection' };

    constructor(readonly address: Address, readonly init?: { code: Cell; data: Cell }) {}

    static createFromAddress(address: Address) {
        return new NFTCollection(address);
    }

    static createFromConfig(config: NFTCollectionConfig, code: Cell, workchain = 0) {
        const data = nFTCollectionConfigToCell(config);
        const init = { code, data };
        return new NFTCollection(contractAddress(workchain, init), init);
    }

    async sendDeploy(provider: ContractProvider, via: Sender, value: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().endCell(),
        });
    }

    // OP_MINT = 0x4d494e54
    async sendMint(provider: ContractProvider, via: Sender, value: bigint) {
        await provider.internal(via, {
            value,
            sendMode: SendMode.PAY_GAS_SEPARATELY,
            body: beginCell().storeUint(0x4d494e54, 32).endCell(),
        });
    }
}
