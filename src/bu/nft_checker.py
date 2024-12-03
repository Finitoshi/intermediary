from solana.rpc.api import Client
from solana.publickey import PublicKey

async def check_nft_ownership(wallet_address: str, nft_mint_address: str):
    solana_client = Client(SOLANA_RPC_URL)
    try:
        # Use Metaplex or similar to check NFT ownership here
        token_accounts = solana_client.get_token_accounts_by_owner(PublicKey(wallet_address))
        for account in token_accounts['result']['value']:
            if account['account']['data']['parsed']['info']['mint'] == nft_mint_address:
                return True
        return False
    except Exception as e:
        logger.error(f"Error checking NFT ownership: {e}")
        return False
