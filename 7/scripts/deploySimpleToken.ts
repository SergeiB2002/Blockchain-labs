import { NetworkProvider, compile } from '@ton/blueprint';

const { SimpleToken } = require('../wrappers/SimpleToken');

export async function run(provider: NetworkProvider) {
    const owner = provider.sender().address!;
    const code = await compile('SimpleToken');

    const token = provider.open(SimpleToken.createFromConfig({ owner }, code));

    await token.sendDeploy(provider.sender(), 200000000n); // 0.2 TON
    await provider.waitForDeploy(token.address);

    console.log('SimpleToken deployed at:', token.address.toString());
}
