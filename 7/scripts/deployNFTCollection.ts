import { NetworkProvider, compile } from '@ton/blueprint';

const { NFTCollection } = require('../wrappers/NFTCollection');

export async function run(provider: NetworkProvider) {
    const owner = provider.sender().address!;
    const collectionCode = await compile('NFTCollection');
    const itemCode = await compile('NFTItem');

    const collection = provider.open(
        NFTCollection.createFromConfig(
            { owner, nextIndex: 0n, itemCode },
            collectionCode
        )
    );

    await collection.sendDeploy(provider.sender(), 200000000n);
    await provider.waitForDeploy(collection.address);

    console.log('NFTCollection deployed at:', collection.address.toString());
}
