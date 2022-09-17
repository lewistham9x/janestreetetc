#!/usr/bin/env python3
# ~~~~~==============   HOW TO RUN   ==============~~~~~
# 1) Configure things in CONFIGURATION section
# 2) Change permissions: chmod +x bot.py
# 3) Run in loop: while true; do ./bot.py --test prod-like; sleep 1; done

import argparse
from collections import deque
from enum import Enum
import time
import socket
import json
from datetime import datetime, timedelta

# ~~~~~============== CONFIGURATION  ==============~~~~~
# Replace "REPLACEME" with your team name!
team_name = "PLAINJANES"

# ~~~~~============== MAIN LOOP ==============~~~~~

# You should put your code here! We provide some starter code as an example,
# but feel free to change/remove/edit/update any of it as you'd like. If you
# have any questions about the starter code, or what to do next, please ask us!
#
# To help you get started, the sample code below tries to buy BOND for a low
# price, and it prints the current prices for VALE every second. The sample
# code is intended to be a working example, but it needs some improvement
# before it will start making good trades!

orderId = 100
lastTrade = datetime.now()
lastTrade2 = datetime.now()
valeCount = 0
valbzCount = 0

xlf = 0
gs = 0
ms = 0
bond = 0
wfc = 0


def make_order(exchange, symbol, dir, price, size):
    global orderId

    price_w_margin = price * 0.98

    if dir == Dir.BUY:
        price_w_margin = price * 1.02

    print(price_w_margin)

    exchange.send_add_message(
        order_id=orderId, symbol=symbol, dir=dir, price=int(price_w_margin), size=size
    )
    orderId += 1


def convert(exchange, symbol, dir, size):
    global orderId

    exchange.send_convert_message(order_id=orderId, symbol=symbol, dir=dir, size=size)

    orderId += 1


# def convert_order()
# asd
# arbitrage valbz and vale
def arbitrage_valbz_vale(
    exchange, vale_bid_price, vale_ask_price, valbz_bid_price, valbz_ask_price
):
    global lastTrade
    if lastTrade > datetime.now() - timedelta(seconds=0.5):
        return

    if vale_bid_price is not None and valbz_ask_price is not None:
        diff1 = vale_bid_price - valbz_ask_price

        if diff1 > 2:
            print("diff1: ", diff1)
            print("bid vale: ", vale_bid_price)
            print("ask valbz: ", valbz_ask_price)
            make_order(exchange, "VALE", Dir.BUY, vale_bid_price, 1)
            # sell valbz
            make_order(exchange, "VALBZ", Dir.SELL, valbz_ask_price, 1)
            lastTrade = datetime.now()

    if valbz_bid_price is not None and vale_ask_price is not None:
        diff2 = valbz_bid_price - vale_ask_price

        if diff2 > 2:
            print("diff2: ", diff2)
            print("bid valbz: ", valbz_bid_price)
            print("ask vale: ", vale_ask_price)
            make_order(exchange, "VALBZ", Dir.BUY, valbz_bid_price, 1)
            # sell valbz
            make_order(exchange, "VALE", Dir.SELL, vale_ask_price, 1)
            lastTrade = datetime.now()


def arbitrage_xlf(
    exchange,
    xlf_ob,
    bond_ob,
    gs_ob,
    ms_ob,
    wfc_ob,
):
    global lastTrade2, bond, xlf, gs, wfc, ms
    if lastTrade2 > datetime.now() - timedelta(seconds=0.5):
        return

    def findTotal(ob, needs):
        if not ob:
            return -1
        has = 0
        total = 0
        for price, number in ob:
            total += price * min(needs - has, number)
            has += number
            if has >= needs:
                return total
        return -1

    total_xlf_bid, total_xlf_ask = findTotal(xlf_ob["buy"], 10), findTotal(
        xlf_ob["sell"], 10
    )
    total_bond_bid, total_bond_ask = findTotal(bond_ob["buy"], 3), findTotal(
        bond_ob["sell"], 3
    )
    total_gs_bid, total_gs_ask = findTotal(gs_ob["buy"], 2), findTotal(gs_ob["sell"], 2)
    total_ms_bid, total_ms_ask = findTotal(ms_ob["buy"], 3), findTotal(ms_ob["sell"], 3)
    total_wfc_bid, total_wfc_ask = findTotal(wfc_ob["buy"], 2), findTotal(
        wfc_ob["sell"], 2
    )

    if -1 in [
        total_xlf_bid,
        total_xlf_ask,
        total_bond_bid,
        total_bond_ask,
        total_gs_bid,
        total_gs_ask,
        total_ms_bid,
        total_ms_ask,
        total_wfc_bid,
        total_wfc_ask,
    ]:
        return

    def getPrice(avg, dir):
        if dir == Dir.BUY:
            return avg * 1.03
        else:
            return avg * 0.97

    if total_xlf_ask + 1 < (
        total_bond_bid + total_gs_bid + total_ms_bid + total_wfc_bid
    ):
        print("buy xlf")
        make_order(exchange, "XLF", Dir.BUY, getPrice(total_xlf_ask / 10, Dir.BUY), 10)
        make_order(
            exchange, "BOND", Dir.SELL, getPrice(total_bond_bid / 3, Dir.SELL), 3
        )
        make_order(exchange, "GS", Dir.SELL, getPrice(total_gs_bid / 2, Dir.SELL), 2)
        make_order(exchange, "MS", Dir.SELL, getPrice(total_ms_bid / 3, Dir.SELL), 3)
        make_order(exchange, "WFC", Dir.SELL, getPrice(total_wfc_bid / 2, Dir.SELL), 2)
        lastTrade2 = datetime.now()

    if total_xlf_bid > (
        total_bond_ask + total_gs_ask + total_ms_ask + total_wfc_ask + 1
    ):
        print("buy indiv stocks")
        make_order(exchange, "BOND", Dir.BUY, getPrice(total_bond_ask / 3, Dir.BUY), 3)
        make_order(exchange, "GS", Dir.BUY, getPrice(total_gs_ask / 2, Dir.BUY), 2)
        make_order(exchange, "MS", Dir.BUY, getPrice(total_ms_ask / 3, Dir.BUY), 3)
        make_order(exchange, "WFC", Dir.BUY, getPrice(total_wfc_ask / 2, Dir.BUY), 2)
        make_order(
            exchange, "XLF", Dir.SELL, getPrice(total_xlf_bid / 10, Dir.SELL), 10
        )
        lastTrade2 = datetime.now()

    if xlf == 100:
        print("convert xlf to indiv")
        convert(exchange, "XLF", Dir.SELL, 100)
        lastTrade2 = datetime.now()
        xlf = 0
        gs = 0
        ms = 0
        bond = 0
        wfc = 0

    if bond + gs + ms + wfc == 100:
        print("convert indiv to XLF")
        convert(exchange, "XLF", Dir.BUY, 100)
        lastTrade2 = datetime.now()


def main():
    global valeCount
    global valbzCount
    global xlf
    global bond
    global gs
    global ms
    global wfc

    args = parse_arguments()

    exchange = ExchangeConnection(args=args)

    # Store and print the "hello" message received from the exchange. This
    # contains useful information about your positions. Normally you start with
    # all positions at zero, but if you reconnect during a round, you might
    # have already bought/sold symbols and have non-zero positions.
    hello_message = exchange.read_message()
    print("First message from exchange:", hello_message)

    # Send an order for BOND at a good price, but it is low enough that it is
    # unlikely it will be traded against. Maybe there is a better price to
    # pick? Also, you will need to send more orders over time.
    # exchange.send_add_message(
    #     order_id=1, symbol="BOND", dir=Dir.SELL, price=1005, size=13
    # )

    # Set up some variables to track the bid and ask price of a symbol. Right
    # now this doesn't track much information, but it's enough to get a sense
    # of the VALE market.
    vale_bid_price, vale_ask_price = None, None
    valbz_bid_price, valbz_ask_price = None, None
    vale_last_print_time = time.time()
    valbz_last_print_time = time.time()
    xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob = [], [], [], [], []

    # Here is the main loop of the program. It will continue to read and
    # process messages in a loop until a "close" message is received. You
    # should write to code handle more types of messages (and not just print
    # the message). Feel free to modify any of the starter code below.
    #
    # Note: a common mistake people make is to call write_message() at least
    # once for every read_message() response.
    #
    # Every message sent to the exchange generates at least one response
    # message. Sending a message in response to every exchange message will
    # cause a feedback loop where your bot's messages will quickly be
    # rate-limited and ignored. Please, don't do that!
    while True:
        global lastTrade

        message = exchange.read_message()
        # Some of the message types below happen infrequently and contain
        # important information to help you understand what your bot is doing,
        # so they are printed in full. We recommend not always printing every
        # message because it can be a lot of information to read. Instead, let
        # your code handle the messages and just print the information
        # important for you!
        if message["type"] == "close":
            print("The round has ended")
            break
        elif message["type"] == "error":
            print(message)
        elif message["type"] == "reject":
            print(message)
        elif message["type"] == "fill":
            print(message)
            if message["symbol"] == "VALE":
                qty = message["size"]
                if message["dir"] == Dir.SELL:
                    qty = -qty
                valeCount += qty
            if message["symbol"] == "VALBZ":
                qty = message["size"]
                if message["dir"] == Dir.SELL:
                    qty = -qty
                valbzCount += qty

            if message["symbol"] == "XLF":
                qty = message["size"] if message["dir"] == Dir.BUY else -message["size"]
                xlf += qty
            if message["symbol"] == "BOND":
                qty = message["size"] if message["dir"] == Dir.BUY else -message["size"]
                bond += qty
            if message["symbol"] == "GS":
                qty = message["size"] if message["dir"] == Dir.BUY else -message["size"]
                gs += qty
            if message["symbol"] == "MS":
                qty = message["size"] if message["dir"] == Dir.BUY else -message["size"]
                ms += qty
            if message["symbol"] == "WFC":
                qty = message["size"] if message["dir"] == Dir.BUY else -message["size"]
                wfc += qty
        elif message["type"] == "book":
            if message["symbol"] == "VALE":

                def best_price(side):
                    if message[side]:
                        return message[side][0][0]

                vale_bid_price = best_price("buy")
                vale_ask_price = best_price("sell")

                now = time.time()

                if now > vale_last_print_time + 1:
                    vale_last_print_time = now
                    # print(
                    #     {
                    #         "vale_bid_price": vale_bid_price,
                    #         "vale_ask_price": vale_ask_price,
                    #     }
                    # )
            if message["symbol"] == "VALBZ":

                def best_price(side):
                    if message[side]:
                        return message[side][0][0]

                valbz_bid_price = best_price("buy")
                valbz_ask_price = best_price("sell")

                now = time.time()

                if now > valbz_last_print_time + 1:
                    valbz_last_print_time = now
                    # print(
                    #     {
                    #         "valbz_bid_price": valbz_bid_price,
                    #         "valbz_ask_price": valbz_ask_price,
                    #     }
                    # )
            if message["symbol"] == "XLF":
                xlf_ob = {"buy": message["buy"], "sell": message["sell"]}
                arbitrage_xlf(exchange, xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob)

            if message["symbol"] == "BOND":
                bond_ob = {"buy": message["buy"], "sell": message["sell"]}
                arbitrage_xlf(exchange, xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob)

            if message["symbol"] == "GS":
                gs_ob = {"buy": message["buy"], "sell": message["sell"]}
                arbitrage_xlf(exchange, xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob)

            if message["symbol"] == "MS":
                ms_ob = {"buy": message["buy"], "sell": message["sell"]}
                arbitrage_xlf(exchange, xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob)

            if message["symbol"] == "WFC":
                wfc_ob = {"buy": message["buy"], "sell": message["sell"]}
                arbitrage_xlf(exchange, xlf_ob, bond_ob, gs_ob, ms_ob, wfc_ob)
            print("valeCount", valeCount)
            print("valbzCount", valbzCount)


            if valbzCount >= 10:
                if lastTrade <= datetime.now() - timedelta(seconds=0.5):
                    convert(exchange, "VALE", Dir.BUY, 10)
                    lastTrade = datetime.now()
                    valbzCount = 0
                    valeCount = 0
            if valeCount >= 10:
                if lastTrade <= datetime.now() - timedelta(seconds=0.5):
                    convert(exchange, "VALE", Dir.SELL, 10)
                    lastTrade = datetime.now()
                    valbzCount = 0
                    valeCount = 0
                    
            arbitrage_valbz_vale(
                exchange,
                valbz_bid_price,
                valbz_ask_price,
                vale_bid_price,
                vale_ask_price,
            )


# ~~~~~============== PROVIDED CODE ==============~~~~~

# You probably don't need to edit anything below this line, but feel free to
# ask if you have any questions about what it is doing or how it works. If you
# do need to change anything below this line, please feel free to


class Dir(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class ExchangeConnection:
    def __init__(self, args):
        self.message_timestamps = deque(maxlen=500)
        self.exchange_hostname = args.exchange_hostname
        self.port = args.port
        exchange_socket = self._connect(add_socket_timeout=args.add_socket_timeout)
        self.reader = exchange_socket.makefile("r", 1)
        self.writer = exchange_socket

        self._write_message({"type": "hello", "team": team_name.upper()})

    def read_message(self):
        """Read a single message from the exchange"""
        message = json.loads(self.reader.readline())
        if "dir" in message:
            message["dir"] = Dir(message["dir"])
        return message

    def send_add_message(
        self, order_id: int, symbol: str, dir: Dir, price: int, size: int
    ):
        """Add a new order"""
        self._write_message(
            {
                "type": "add",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "price": price,
                "size": size,
            }
        )

    def send_convert_message(self, order_id: int, symbol: str, dir: Dir, size: int):
        """Convert between related symbols"""
        self._write_message(
            {
                "type": "convert",
                "order_id": order_id,
                "symbol": symbol,
                "dir": dir,
                "size": size,
            }
        )

    def send_cancel_message(self, order_id: int):
        """Cancel an existing order"""
        self._write_message({"type": "cancel", "order_id": order_id})

    def _connect(self, add_socket_timeout):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        if add_socket_timeout:
            # Automatically raise an exception if no data has been recieved for
            # multiple seconds. This should not be enabled on an "empty" test
            # exchange.
            s.settimeout(5)
        s.connect((self.exchange_hostname, self.port))
        return s

    def _write_message(self, message):
        what_to_write = json.dumps(message)
        if not what_to_write.endswith("\n"):
            what_to_write = what_to_write + "\n"

        length_to_send = len(what_to_write)
        total_sent = 0
        while total_sent < length_to_send:
            sent_this_time = self.writer.send(
                what_to_write[total_sent:].encode("utf-8")
            )
            if sent_this_time == 0:
                raise Exception("Unable to send data to exchange")
            total_sent += sent_this_time

        now = time.time()
        self.message_timestamps.append(now)
        if len(
            self.message_timestamps
        ) == self.message_timestamps.maxlen and self.message_timestamps[0] > (now - 1):
            print(
                "WARNING: You are sending messages too frequently. The exchange will start ignoring your messages. Make sure you are not sending a message in response to every exchange message."
            )


def parse_arguments():
    test_exchange_port_offsets = {"prod-like": 0, "slower": 1, "empty": 2}

    parser = argparse.ArgumentParser(description="Trade on an ETC exchange!")
    exchange_address_group = parser.add_mutually_exclusive_group(required=True)
    exchange_address_group.add_argument(
        "--production", action="store_true", help="Connect to the production exchange."
    )
    exchange_address_group.add_argument(
        "--test",
        type=str,
        choices=test_exchange_port_offsets.keys(),
        help="Connect to a test exchange.",
    )

    # Connect to a specific host. This is only intended to be used for debugging.
    exchange_address_group.add_argument(
        "--specific-address", type=str, metavar="HOST:PORT", help=argparse.SUPPRESS
    )

    args = parser.parse_args()
    args.add_socket_timeout = True

    if args.production:
        args.exchange_hostname = "production"
        args.port = 25000
    elif args.test:
        args.exchange_hostname = "test-exch-" + team_name
        args.port = 25000 + test_exchange_port_offsets[args.test]
        if args.test == "empty":
            args.add_socket_timeout = False
    elif args.specific_address:
        args.exchange_hostname, port = args.specific_address.split(":")
        args.port = int(port)

    return args


if __name__ == "__main__":
    # Check that [team_name] has been updated.
    assert (
        team_name != "REPLACEME"
    ), "Please put your team name in the variable [team_name]."

    main()
