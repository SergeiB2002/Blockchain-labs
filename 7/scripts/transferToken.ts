import { NetworkProvider } from '@ton/blueprint';
import { Address } from '@ton/core';

const { SimpleToken } = require('../wrappers/SimpleToken');

export async function run(provider: NetworkProvider) {
    const tokenAddress = Address.parse('EQ...'); // адрес токена
    const receiver = Address.parse('EQ...');     // кому отправить
    const token = provider.open(SimpleToken.createFromAddress(tokenAddress));

    await token.sendTransfer(provider.sender(), 80000000n, receiver, 250n);

    console.log('Transferred 250 tokens to:', receiver.toString());
}
