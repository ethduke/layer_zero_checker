import asyncio
import aiohttp
from aiohttp_socks import ProxyConnector
import random

class ProxyManager:
    def __init__(self, proxy_file='proxies.txt'):
        self.proxy_file = proxy_file
        self.working_proxies = []

    async def test_proxy(self, session, proxy):
        try:
            connector = ProxyConnector.from_url(proxy)
            async with aiohttp.ClientSession(connector=connector) as test_session:
                async with test_session.get('https://api.ipify.org', timeout=10) as response:
                    if response.status == 200:
                        return proxy
        except:
            pass
        return None

    async def generate_working_proxy_pool(self):
        with open(self.proxy_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        
        async with aiohttp.ClientSession() as session:
            tasks = [self.test_proxy(session, proxy) for proxy in proxies]
            results = await asyncio.gather(*tasks)
            self.working_proxies = [proxy for proxy in results if proxy]
        
        print(f"Found {len(self.working_proxies)} working proxies out of {len(proxies)}")

    def get_random_proxy(self):
        if not self.working_proxies:
            raise ValueError("No working proxies available")
        return random.choice(self.working_proxies)

    async def get_proxy_connector(self):
        proxy = self.get_random_proxy()
        return ProxyConnector.from_url(proxy)