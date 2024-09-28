import asyncio
import aiohttp
import json
from tqdm import tqdm
from itertools import islice
from proxy_manager import ProxyManager

async def fetch_proof(session, address, proxy_manager):
    url = f"https://layerzero.foundation/api/proof/{address}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': f'https://layerzero.foundation/claim/{address}',
        'Origin': 'https://layerzero.foundation',
    }

    connector = await proxy_manager.get_proxy_connector()

    try:
        async with aiohttp.ClientSession(connector=connector) as proxy_session:
            async with proxy_session.get(url, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if 'error' not in data and 'proof' in data and 'round1' in data and 'round2' in data:
                        return address, data
    except Exception as e:
        print(f"Error fetching proof for {address}: {str(e)}")
    
    await asyncio.sleep(0.5)
    return None

def wei_to_ether(wei_value):
    return float(wei_value) / 10**18


async def process_batch(session, batch, pbar, proxy_manager):
    tasks = [fetch_proof(session, address, proxy_manager) for address in batch]
    results = await asyncio.gather(*tasks)
    for result in results:
        if result:
            yield result
        pbar.update(1)
    await asyncio.sleep(0.1)  # Small delay to avoid overwhelming the server

async def main():
    proxy_manager = ProxyManager()
    await proxy_manager.generate_working_proxy_pool()
    if not proxy_manager.working_proxies:
        print("No working proxies found. Exiting.")
        return

    # Read addresses from evm.txt
    try:
        with open('evm.txt', 'r') as f:
            addresses = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print("Error: 'evm.txt' file not found.")
        return
    except Exception as e:
        print(f"Error reading 'evm.txt': {e}")
        return

    print(f"Loaded {len(addresses)} addresses from evm.txt")

    # Process addresses
    results = []
    batch_size = 5
    
    async with aiohttp.ClientSession() as session:
        with tqdm(total=len(addresses), desc="Processing", ncols=70, unit="addr") as pbar:
            for i in range(0, len(addresses), batch_size):
                batch = list(islice(addresses, i, i + batch_size))
                async for result in process_batch(session, batch, pbar, proxy_manager):
                    if result:
                        results.append(result)

    print(f"\nFetched {len(results)} valid results")

    # Remove duplicates
    unique_results = []
    seen_addresses = set()
    for address, data in results:
        if address not in seen_addresses:
            unique_results.append((address, data))
            seen_addresses.add(address)

    print(f"Found {len(unique_results)} unique valid results")

    # Save successful results to success_output.json
    eligible_claims = [
        {
            "address": address,
            "amount": wei_to_ether(data['amount']),
            "round1": wei_to_ether(data['round1']),
            "round2": wei_to_ether(data['round2'])
        }
        for address, data in unique_results
    ]
    with open('eligible_claims.json', 'w') as f:
        json.dump(eligible_claims, f, indent=2)

    print(f"Saved {len(eligible_claims)} unique eligible claims to eligible_claims.json")

if __name__ == "__main__":
    asyncio.run(main())