from aiohttp import (
    ClientResponseError,
    ClientSession,
    ClientTimeout
)
from aiohttp_socks import ProxyConnector
from fake_useragent import FakeUserAgent
from datetime import datetime, timezone
from colorama import *
import asyncio, json, os, pytz, base64

wib = pytz.timezone('Asia/Jakarta')

class ByData:
    def __init__(self) -> None:
        self.base_url = "https://mega-api.bydata.app"
        self.headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "id-ID,id;q=0.9,en-US;q=0.8,en;q=0.7",
            "Origin": "https://bydata.app",
            "Referer": "https://bydata.app/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": FakeUserAgent().random
        }
        self.proxies = []
        self.proxy_index = 0
        self.account_proxies = {}
        self.ref_code = "S4ML6AMW" # U can change it with yours.

    def clear_terminal(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def log(self, message):
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}{message}",
            flush=True
        )

    def welcome(self):
        print(
            f"""
        {Fore.GREEN + Style.BRIGHT}Auto Claim {Fore.BLUE + Style.BRIGHT}ByData - BOT
            """
            f"""
        {Fore.GREEN + Style.BRIGHT}Rey? {Fore.YELLOW + Style.BRIGHT}<INI WATERMARK>
            """
        )

    def format_seconds(self, seconds):
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}"
    
    async def load_proxies(self, use_proxy_choice: int):
        filename = "proxy.txt"
        try:
            if use_proxy_choice == 1:
                async with ClientSession(timeout=ClientTimeout(total=30)) as session:
                    async with session.get("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt") as response:
                        response.raise_for_status()
                        content = await response.text()
                        with open(filename, 'w') as f:
                            f.write(content)
                        self.proxies = content.splitlines()
            else:
                if not os.path.exists(filename):
                    self.log(f"{Fore.RED + Style.BRIGHT}File {filename} Not Found.{Style.RESET_ALL}")
                    return
                with open(filename, 'r') as f:
                    self.proxies = f.read().splitlines()
            
            if not self.proxies:
                self.log(f"{Fore.RED + Style.BRIGHT}No Proxies Found.{Style.RESET_ALL}")
                return

            self.log(
                f"{Fore.GREEN + Style.BRIGHT}Proxies Total  : {Style.RESET_ALL}"
                f"{Fore.WHITE + Style.BRIGHT}{len(self.proxies)}{Style.RESET_ALL}"
            )
        
        except Exception as e:
            self.log(f"{Fore.RED + Style.BRIGHT}Failed To Load Proxies: {e}{Style.RESET_ALL}")
            self.proxies = []

    def check_proxy_schemes(self, proxies):
        schemes = ["http://", "https://", "socks4://", "socks5://"]
        if any(proxies.startswith(scheme) for scheme in schemes):
            return proxies
        return f"http://{proxies}"

    def get_next_proxy_for_account(self, token):
        if token not in self.account_proxies:
            if not self.proxies:
                return None
            proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
            self.account_proxies[token] = proxy
            self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return self.account_proxies[token]

    def rotate_proxy_for_account(self, token):
        if not self.proxies:
            return None
        proxy = self.check_proxy_schemes(self.proxies[self.proxy_index])
        self.account_proxies[token] = proxy
        self.proxy_index = (self.proxy_index + 1) % len(self.proxies)
        return proxy
    
    def mask_account(self, account):
        mask_account = account[:6] + '*' * 6 + account[-6:]
        return mask_account
    
    def generate_salt(self, id: str):
        s = ["zuHtvmKPS3Wsj4hZbq62af", "hXEGaMzuVcf7R85HgvKSW9", "Mr2KZGkJyfRxUe9LaHACVw"]
        now = datetime.now(timezone.utc)
        today = now.strftime("%Y-%m-%d")
        index = now.day % len(s)
        return "qtA6LcU9JXTmuHMbD3GRea" + today + s[index] + id[:8]

    def encrypt_id(self, id: str):
        if not id:
            return ""
        salt = self.generate_salt(id)
        reversed_e = id[::-1]
        combined = f"{reversed_e}:{salt}"
        encoded = base64.b64encode(combined.encode()).decode()
        safe_encoded = encoded.replace("+", "-").replace("/", "_").replace("=", ".")
        return f"bd-{safe_encoded}"

    def is_valid_url(self, id: str):
        if not id:
            return ""
        return id if id.startswith("bd-") else self.encrypt_id(id)

    def generate_encrypted_id(self, id: str):
        encrypted_id = self.is_valid_url(id)
        return encrypted_id
        
    def print_question(self):
        while True:
            try:
                print("1. Run With Monosans Proxy")
                print("2. Run With Private Proxy")
                print("3. Run Without Proxy")
                choose = int(input("Choose [1/2/3] -> ").strip())

                if choose in [1, 2, 3]:
                    proxy_type = (
                        "Run With Monosans Proxy" if choose == 1 else 
                        "Run With Private Proxy" if choose == 2 else 
                        "Run Without Proxy"
                    )
                    print(f"{Fore.GREEN + Style.BRIGHT}{proxy_type} Selected.{Style.RESET_ALL}")
                    return choose
                else:
                    print(f"{Fore.RED + Style.BRIGHT}Please enter either 1, 2 or 3.{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.RED + Style.BRIGHT}Invalid input. Enter a number (1, 2 or 3).{Style.RESET_ALL}")
    
    async def user_login(self, address: str, proxy=None, retries=5):
        url = f"{self.base_url}/v1/users"
        data = json.dumps({"walletAddress":address, "referredCode":self.ref_code})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=300)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]["user"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def task_lists(self, encrypted_user_id: str, proxy=None, retries=5):
        url = f"{self.base_url}/v1/social/actions/{encrypted_user_id}"
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=300)) as session:
                    async with session.get(url=url, headers=self.headers) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def complete_tasks(self, encrypted_user_id: str, encrypted_task_id: str, proxy=None, retries=5):
        url = f"{self.base_url}/v1/social/actions/complete"
        data = json.dumps({"userId":encrypted_user_id, "templateId":encrypted_task_id})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=300)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
    
    async def claim_tasks(self, encrypted_user_id: str, encrypted_task_id: str, proxy=None, retries=5):
        url = f"{self.base_url}/v1/social/actions/claim"
        data = json.dumps({"userId":encrypted_user_id, "templateId":encrypted_task_id})
        headers = {
            **self.headers,
            "Content-Length": str(len(data)),
            "Content-Type": "application/json"
        }
        for attempt in range(retries):
            connector = ProxyConnector.from_url(proxy) if proxy else None
            try:
                async with ClientSession(connector=connector, timeout=ClientTimeout(total=300)) as session:
                    async with session.post(url=url, headers=headers, data=data) as response:
                        response.raise_for_status()
                        result = await response.json()
                        return result["data"]
            except (Exception, ClientResponseError) as e:
                if attempt < retries - 1:
                    await asyncio.sleep(5)
                    continue

                return None
        
    async def process_accounts(self, address: str, use_proxy: bool):
        proxy = self.get_next_proxy_for_account(address) if use_proxy else None
        user = None
        while user is None:
            user = await self.user_login(address, proxy)
            if not user:
                self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
                    f"{Fore.RED+Style.BRIGHT} Login Failed {Style.RESET_ALL}"
                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} Retrying... {Style.RESET_ALL}"
                )
                proxy = self.rotate_proxy_for_account(address) if use_proxy else None
                await asyncio.sleep(5)
                continue

        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Proxy     :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {proxy} {Style.RESET_ALL}"
        )
            
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Status    :{Style.RESET_ALL}"
            f"{Fore.GREEN+Style.BRIGHT} Login Success {Style.RESET_ALL}"
        )

        user_id = user["id"]
        encrypted_user_id = self.generate_encrypted_id(user_id)
        balance = user["totalXP"]
            
        self.log(
            f"{Fore.CYAN+Style.BRIGHT}Balance   :{Style.RESET_ALL}"
            f"{Fore.WHITE+Style.BRIGHT} {balance} PTS {Style.RESET_ALL}"
        )

        task_lists = await self.task_lists(encrypted_user_id, proxy)
        if task_lists:
            self.log(f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}")

            tasks = task_lists.get("socialActions", [])
            if isinstance(tasks, list) and len(tasks) == 0:
                return self.log(
                    f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                    f"{Fore.YELLOW+Style.BRIGHT} No Available Tasks {Style.RESET_ALL}"
                )
            
            for task in tasks:
                if task:
                    task_id = task.get("id")
                    title = task.get("title")
                    category = task.get("category")
                    reward = task.get("xpRewarded")
                    completed = task.get("completed")
                    claimed = task.get("claimed")

                    encrypted_task_id = self.generate_encrypted_id(task_id)

                    if completed and claimed:
                        self.log(
                            f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                            f"{Fore.YELLOW+Style.BRIGHT} Already Completed {Style.RESET_ALL}"
                        )
                        continue

                    if not completed and not claimed:
                        complete = await self.complete_tasks(encrypted_user_id, encrypted_task_id, proxy)
                        if complete:
                            is_completed = complete.get("socialAction", {}).get("completed", False)
                            if is_completed:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} Completed {Style.RESET_ALL}"
                                )
                                await asyncio.sleep(1)

                                claim = await self.claim_tasks(encrypted_user_id, encrypted_task_id, proxy)
                                if claim:
                                    is_claimed = claim.get("socialAction", {}).get("claimed", False)
                                    if is_claimed:
                                        self.log(
                                            f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                            f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                            f"{Fore.GREEN+Style.BRIGHT} Claimed {Style.RESET_ALL}"
                                            f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                            f"{Fore.CYAN+Style.BRIGHT} Reward {Style.RESET_ALL}"
                                            f"{Fore.WHITE+Style.BRIGHT}{reward} PTS{Style.RESET_ALL}"
                                        )
                                    else:
                                        self.log(
                                            f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                            f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                            f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                            f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                            f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                                        )
                                else:
                                    self.log(
                                        f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                        f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                        f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                        f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                                    )
                                await asyncio.sleep(1)

                            else:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                                )
                        else:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Not Completed {Style.RESET_ALL}"
                            )
                        await asyncio.sleep(1)

                    elif completed and not claimed:
                        claim = await self.claim_tasks(encrypted_user_id, encrypted_task_id, proxy)
                        if claim:
                            is_claimed = claim.get("socialAction", {}).get("claimed", False)
                            if is_claimed:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                    f"{Fore.GREEN+Style.BRIGHT} Claimed {Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT}-{Style.RESET_ALL}"
                                    f"{Fore.CYAN+Style.BRIGHT} Reward {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{reward} PTS{Style.RESET_ALL}"
                                )
                            else:
                                self.log(
                                    f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                    f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                    f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                    f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                                )
                        else:
                            self.log(
                                f"{Fore.CYAN+Style.BRIGHT}      > {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{category}{Style.RESET_ALL}"
                                f"{Fore.MAGENTA+Style.BRIGHT} - {Style.RESET_ALL}"
                                f"{Fore.WHITE+Style.BRIGHT}{title}{Style.RESET_ALL}"
                                f"{Fore.RED+Style.BRIGHT} Not Claimed {Style.RESET_ALL}"
                            )
                        await asyncio.sleep(1)

        else:
            self.log(
                f"{Fore.CYAN+Style.BRIGHT}Task Lists:{Style.RESET_ALL}"
                f"{Fore.RED+Style.BRIGHT} Data Is None {Style.RESET_ALL}"
            )

    async def main(self):
        try:
            with open('accounts.txt', 'r') as file:
                accounts = [line.strip() for line in file if line.strip()]
            
            use_proxy_choice = self.print_question()

            while True:
                use_proxy = False
                if use_proxy_choice in [1, 2]:
                    use_proxy = True

                self.clear_terminal()
                self.welcome()
                self.log(
                    f"{Fore.GREEN + Style.BRIGHT}Account's Total: {Style.RESET_ALL}"
                    f"{Fore.WHITE + Style.BRIGHT}{len(accounts)}{Style.RESET_ALL}"
                )

                if use_proxy:
                    await self.load_proxies(use_proxy_choice)
                
                separator = "=" * 23
                for address in accounts:
                    if address:
                        self.log(
                            f"{Fore.CYAN + Style.BRIGHT}{separator}[{Style.RESET_ALL}"
                            f"{Fore.WHITE + Style.BRIGHT} {self.mask_account(address)} {Style.RESET_ALL}"
                            f"{Fore.CYAN + Style.BRIGHT}]{separator}{Style.RESET_ALL}"
                        )
                        await self.process_accounts(address, use_proxy)
                        await asyncio.sleep(3)

                self.log(f"{Fore.CYAN + Style.BRIGHT}={Style.RESET_ALL}"*68)
                seconds = 24 * 60 * 60
                while seconds > 0:
                    formatted_time = self.format_seconds(seconds)
                    print(
                        f"{Fore.CYAN+Style.BRIGHT}[ Wait for{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} {formatted_time} {Style.RESET_ALL}"
                        f"{Fore.CYAN+Style.BRIGHT}... ]{Style.RESET_ALL}"
                        f"{Fore.WHITE+Style.BRIGHT} | {Style.RESET_ALL}"
                        f"{Fore.BLUE+Style.BRIGHT}All Accounts Have Been Processed.{Style.RESET_ALL}",
                        end="\r"
                    )
                    await asyncio.sleep(1)
                    seconds -= 1

        except FileNotFoundError:
            self.log(f"{Fore.RED}File 'accounts.txt' Not Found.{Style.RESET_ALL}")
            return
        except Exception as e:
            self.log(f"{Fore.RED+Style.BRIGHT}Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    try:
        bot = ByData()
        asyncio.run(bot.main())
    except KeyboardInterrupt:
        print(
            f"{Fore.CYAN + Style.BRIGHT}[ {datetime.now().astimezone(wib).strftime('%x %X %Z')} ]{Style.RESET_ALL}"
            f"{Fore.WHITE + Style.BRIGHT} | {Style.RESET_ALL}"
            f"{Fore.RED + Style.BRIGHT}[ EXIT ] ByData - BOT{Style.RESET_ALL}                                       "                              
        )