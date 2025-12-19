import { NetworkProvider } from '@ton/blueprint';
import { Address } from '@ton/core';

const { SimpleToken } = require('../wrappers/SimpleToken');

export async function run(provider: NetworkProvider) {
    const tokenAddress = Address.parseFriendly('EQCtaVB358owMuBVjfh0QuRt2O74hykh15UhwvxQhRc-Uonz').address; // <-- вставь адрес после deploy
    const token = provider.open(SimpleToken.createFromAddress(tokenAddress));

    const to = provider.sender().address!;
    await token.sendMint(provider.sender(), 100000000n, to, 1000n);

    console.log('Minted 1000 tokens to:', to.toString());
}
