import { NetworkProvider } from '@ton/blueprint';
import { Address } from '@ton/core';

const { SimpleToken } = require('../wrappers/SimpleToken');

export async function run(provider: NetworkProvider) {
    const tokenAddress = Address.parse('EQ...'); // адрес токена
    const token = provider.open(SimpleToken.createFromAddress(tokenAddress));

    // get_total_supply
    const total = await token.getTotalSupply();
    console.log('Total supply:', total.toString());

    // get_balance(my)
    const me = provider.sender().address!;
    const bal = await token.getBalance(me);
    console.log('My balance:', bal.toString());
}
