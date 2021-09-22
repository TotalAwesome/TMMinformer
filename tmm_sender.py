import requests
from pprint import pprint
import sqlite3
import time
import colorama
from config import token, auth_data, chatid

colorama.init()
red = colorama.Fore.RED
reset = colorama.Fore.RESET
white = colorama.Fore.WHITE
green = colorama.Fore.GREEN
cyan = colorama.Fore.CYAN
yellow = colorama.Fore.YELLOW
magenta = colorama.Fore.MAGENTA

total = {
    'fee' : 0,
    'profit' : 0
}

Session = requests.session()

class db:

    def __init__(self):
        filename = 'tm.db'
        self.connection = sqlite3.connect(filename)
        self.cursor = self.connection.cursor()
        self.cursor.execute(
            """
            create table if not exists trades (
                id integer primary key autoincrement,
                trade_id integer
            )
            """
        )
        self.connection.commit()

    def new_id(self, trade_id):
        """
        link_new(self, trade_id) - проверка есть ли hash в базе
        """
        self.cursor.execute(
            f"SELECT * FROM trades WHERE trade_id = '{trade_id}'"
        )
        result = self.cursor.fetchall()
        if len(result) > 0:
            return False
        else:
            self.add_hash(trade_id)
            return True

    def add_hash(self, trade_id):
        """
        add_link(self, trade_id) - Добавление hash в базу
        """
        self.cursor.execute(
            f'INSERT INTO trades (trade_id) VALUES ("{trade_id}")'
        )
        self.connection.commit()

def tg_send(msg):
    text = str(msg)
    bot_line = f"https://api.telegram.org/bot{token}/sendmessage?text={text}&parse_mode=html&chat_id={chatid}"
    retry = True
    end = int(time.time())-1
    while retry:
        if int(time.time()) > end:
            try:
                result = requests.get(bot_line).json()
                if not result['ok']:
                    print(result)
                    if result['error_code'] == 429:
                        end = int() + result['parameters']['retry_after']
                        time.sleep(result['parameters']['retry_after'])
                else:
                    retry = False
            except:
                pass
    return result

DB = db()
def auth(Session):
    
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.131 Safari/537.36',
        'accept': 'application/json'
    }
    try:
        res = Session.post(
            url='https://tradermake.money/api/auth/login',
            data=auth_data
        )
        token = res.json()['access_token']
        headers.update(
            {
                'authorization': f'Bearer {token}'
            }
        )
    except:
        print(str(Exception))
        time.sleep(120)
    return headers

headers = auth(Session)
while True:
    trades_url = 'https://tradermake.money/api/trades?time=0&include[0]=tags&include[1]=images&filter[side]=0&filter[durationBetween]=0&filter[volumeFrom]=0&filter[volumeTo]=0&filter[percentBetween]=0&filter[leverageBetween]=0&filter[openBetween]=&filter[category]=0&filter[id]=0&itemsPerPage=50&page=1&mustSort=false&multiSort=false'
    try:
        res = Session.get(
            url=trades_url,
            headers=headers
        )
        trades = res.json()
    except:
        print(str(Exception))
        trades = {}
    if 'data' in trades:
        for trade in trades['data']:
            hsh = trade['hash']
            trade_id = trade['id']
            side = trade['side']
            pair = trade['symbol']
            pnl = trade['realizedPnl']
            fee = trade['commission']
            total['fee'] += fee
            net_profit = trade['net_profit']
            total['profit'] += net_profit
            closetime = trade['close_time']
            if closetime > 0:
                new = DB.new_id(trade_id)
                if new:
                    trade_url = f'https://tradermake.money/ru/trade/{hsh}?ref=_TotalAwesome'
                    msg = f'<a href="{trade_url}">{"🟩" if pnl >0 else "🟥"} {side} {pair}</a>\n'
                    msg += f'<code><b>Профит: </b>{pnl}$\n'
                    msg += f'<b>Комиссия: </b>{fee}$\n'
                    msg += f'<b>Итого: </b>{net_profit}$\n</code>'
                    msg += '- '*6

                    tmp = tg_send(
                        msg
                    )
                    # 🟩🟥
                    print(
                        f'{"🟩" if pnl >0 else "🟥"} {yellow}{side}{reset} {magenta}{pair}{reset} profit {green if pnl >0 else red}{pnl}$ {reset}'
                    )
                    if not tmp['ok']:
                        print(tmp)
                    time.sleep(1)
    else:
        if 'message' in res.json():
            if res.json()['message'] == 'Unauthenticated.':
                print(f'{green}Пробую перелогиниться {reset}')
                headers = auth(Session)
        print(f'{red}Что-то не то получили{reset}\n')
        pprint(res.json())
    time.sleep(90)
