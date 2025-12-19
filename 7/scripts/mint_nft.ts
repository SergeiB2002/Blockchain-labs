import { NetworkProvider } from '@ton/blueprint';
import { Address } from '@ton/core';

const { NFTCollection } = require('../wrappers/NFTCollection');

export async function run(provider: NetworkProvider) {
    const collectionAddress = Address.parseFriendly('EQD5CQ-dB9jikDZa_3CbLYbLn2zu1kg256YWAIIM6uQwaoNy').address; // адрес коллекции
    const collection = provider.open(NFTCollection.createFromAddress(collectionAddress));

    for (let i = 0; i < 3; i++) {
        await collection.sendMint(provider.sender(), 80000000n); // 0.08 TON
        console.log('Mint sent:', i + 1);
    }
}
