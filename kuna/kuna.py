# -*- coding: utf-8 -*-

"""Main module."""
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
import time
import json
import hashlib
import warnings
import hmac
from typing import Union, List

API_VERSION = '3'

KEYS_NEED_MESSAGE = '''
    API initialized without public or private key. Only Public API is available.
    Get keys from "https://kuna.io/settings/api_tokens".
    '''

DEFAULT_HEADERS = {'accept': 'application/json', 'content-type': 'application/json', 'user-agent': 'python-kuna/0.4.0'}

class APIError(Exception):
    def __init__(self, result):
        if isinstance(result, HTTPError):
            result = json.load(result)
        if isinstance(result, dict) and 'messages' in result:
            message = result.get('messages')
        elif isinstance(result, str):
            message = result
        else:
            message = repr(result)
        Exception.__init__(self, message)


class KunaAPI(object):
    """
    Documentation sources
    - https://docs.kuna.io/docs
    - https://github.com/kunadevelopers/api-docs
    """
    def __init__(self, public_key=None, private_key=None, disable_warnings=False):
        self.public_key = public_key
        self.private_key = private_key
        self.endpoint = 'https://api.kuna.io'
        self.prefix = '/v3'

        self._check_keys(error=False)

        if disable_warnings:
            warnings.filterwarnings('ignore')

    def _check_keys(self, error: bool = True):
        if (self.public_key is None) or (self.private_key is None):
            if error:
                APIError(KEYS_NEED_MESSAGE)
            else:
                warnings.warn(KEYS_NEED_MESSAGE)

    def _generate_sign(self, uri: str, body: str, nonce: str) -> str:
        """
        Signature is generated by an algorithm: https://docs.kuna.io/docs/api-data-schema-and-serialization
        HEX(HMAC-SHA384(URI + timestamp + JSON(params), secret_key))
        :return:
        """
        payload = '{}{}{}'.format(uri, nonce, body)
        payload_bin = payload.encode('ascii')
        private_key_bin = self.private_key.encode('ascii')
        sign = hmac.new(private_key_bin, payload_bin, hashlib.sha384)
        return sign.hexdigest()

    def _request(self, path, args: dict = {}, body: dict = {}, is_user_method=False) -> Union[dict, APIError]:
        """
        Fetches the given path in the Kuna API.
        :param path: Api path
        :param args: args of GET-request
        :param body: body of request
        :param is_user_method:
        :return: Serialized server response or error
        """
        # If GET params available then add it to path
        if args:
            path += '?' + urlencode(args)
        uri = self.prefix + path
        url = self.endpoint + uri
        headers = DEFAULT_HEADERS.copy()
        body = json.dumps(body)

        if is_user_method:
            self._check_keys(error=True)
            method = 'POST'
            nonce = str(int(time.time() * 1000))
            headers['kun-nonce'] = nonce
            headers['kun-apikey'] = self.public_key
            headers['kun-signature'] = self._generate_sign(uri, body, nonce)
        else:
            method = 'GET'

        req = Request(url, body.encode(), headers, method=method)

        try:
            with urlopen(req) as resp:
                json_resp = json.load(resp)
        except HTTPError as err:
            raise APIError(err)
        else:
            return json_resp

    # Old methods
    def get_server_time(self):
        warnings.warn('Better use: "api.timestamp()"', DeprecationWarning)
        self.timestamp()

    def get_recent_market_data(self, market):
        warnings.warn('Better use: "api.tickers(market)"', DeprecationWarning)
        self.tickers(market)

    def get_order_book(self, market):
        warnings.warn('Better use: "api.book(market)"', DeprecationWarning)
        self.book()

    def get_trades_history(self, market):
        warnings.warn('Better use: "api.history(market)"', DeprecationWarning)
        self.history()

    def get_user_account_info(self):
        warnings.warn('Better use: "api.auth_me()"', DeprecationWarning)
        self.auth_me()

    def get_orders(self, market):
        warnings.warn('Better use: "api.auth_r_orders(market)"', DeprecationWarning)
        self.auth_r_orders(market)

    def put_order(self, side, amount, symbol, price):
        warnings.warn('Better use: "api.auth_w_order_submit()"', DeprecationWarning)
        if side.lower() == 'buy': amount = abs(amount)
        else: amount = -1 * abs(amount)
        self.auth_w_order_submit(symbol, 'limit', amount, price)

    def cancel_order(self, order_id):
        warnings.warn('Better use: "api.order_cancel(order_id)"', DeprecationWarning)
        self.order_cancel(order_id)

    def get_trade_history(self, market):
        warnings.warn('Better use: "api.auth_r_orders_hist(market)"', DeprecationWarning)
        self.auth_r_orders_hist(market)

    # PUBLIC API
    def timestamp(self):
        """
        # Kuna server time. https://docs.kuna.io/docs/time-on-server
        :return: https://docs.kuna.io/reference#timestamp
        """
        return self._request('/timestamp')

    def currencies(self):
        """
        List of available currencies. https://docs.kuna.io/docs/available-currencies-list
        :return: https://docs.kuna.io/reference#currencies
        """
        return self._request('/currencies')

    def exchange_rates(self, currency: str = None):
        """
        Exchange rates for all currencies or specified one
        :param currency: like 'eth' or 'uah'
        :return: https://docs.kuna.io/reference#exchange-rates
        """
        if currency:
            path = f'/exchange-rates/{currency}'
        else:
            path = '/exchange-rates'
        return self._request(path)

    def markets(self):
        """
        # List of available markets https://docs.kuna.io/docs/markets
        :return: https://docs.kuna.io/reference#markets-1
        """
        return self._request('/markets')

    def tickers(self, symbols: Union[str,list] = None):
        """
        # Last ticker for certain or all markets. https://docs.kuna.io/docs/%D0%BF%D0%BE%D1%81%D0%BB%D0%B5%D0%B4%D0%BD%D0%B8%D0%B5-%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D0%B5-%D0%BF%D0%BE-%D1%80%D1%8B%D0%BD%D0%BA%D1%83-%D1%82%D0%B8%D0%BA%D0%B5%D1%80%D1%8B
        :param symbols: 'btcuah' or ['btcuah','kunbtc','ethuah'], by default ALL
        :return: https://docs.kuna.io/reference#tickers
        """
        if isinstance(symbols, str):
            args = {'symbols': symbols}
        elif isinstance(symbols, list):
            args = {'symbols': ','.join(symbols)}
        else:
            args = {'symbols': 'ALL'}
        return self._request('/tickers', args=args)

    def book(self, market):
        """
        Actual Orderbook state for certain market. https://docs.kuna.io/docs/%D0%BE%D1%80%D0%B4%D0%B5%D1%80%D0%B1%D1%83%D0%BA
        :param market: 'btcuah'
        :return: https://docs.kuna.io/reference#book
        """
        return self._request(f'/book/{market}')

    def history(self, *args, **kwargs):
        """
        Not implemented. https://docs.kuna.io/docs/transaction-history
        :return:
        """
        raise NotImplementedError

    def price_changes(self, *args, **kwargs):
        """
        Not implemented. https://docs.kuna.io/docs/%D0%B3%D1%80%D0%B0%D1%84%D0%B8%D0%BA-%D0%B8%D0%B7%D0%BC%D0%B5%D0%BD%D0%B5%D0%BD%D0%B8%D1%8F-%D1%86%D0%B5%D0%BD%D1%8B
        :return:
        """
        raise NotImplementedError

    def fees(self):
        """
        Withdraw and deposit methods. Withdrawal fees. https://docs.kuna.io/docs/deposits-withdrowals-fees
        :return: https://docs.kuna.io/reference#fees
        """
        return self._request('/fees')

    # PRIVATE API
    def http_test(self):
        """
        Test HTTP connection to private API
        :return: https://docs.kuna.io/reference#http_test
        """
        return self._request('/http_test', is_user_method=True)

    def auth_me(self):
        """
        # Information about the User-account
        :return: https://docs.kuna.io/docs/%D0%B4%D0%B0%D0%BD%D0%BD%D1%8B%D0%B5-%D0%B0%D0%BA%D0%BA%D0%B0%D1%83%D0%BD%D1%82%D0%B0
        """
        return self._request('/auth/me', is_user_method=True)

    def auth_r_wallets(self):
        """
        Account balance in all wallets
        :return: https://docs.kuna.io/docs/account-balance
        """
        return self._request('/auth/r/wallets', is_user_method=True)

    def auth_history_trades(self, market: str, date_from: int = None, date_to: int = None):
        """
        Send history of trade in csv-file to user EMAIL. https://docs.kuna.io/docs/%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B5%D0%BD%D0%B8%D0%B5-%D0%B8%D1%81%D1%82%D0%BE%D1%80%D0%B8%D0%B8-%D1%81%D0%B4%D0%B5%D0%BB%D0%BE%D0%BA-%D0%BF%D0%BE-%D0%BF%D0%BE%D1%87%D1%82%D0%B5
        :param market: 'ethuah'
        :param date_from: UNIX timestamp. Default: year ago (now - 60*60*24*365)
        :param date_to: UNIX timestamp. Default: now
        :return:
        """
        body = {'market': market, 'date_from': date_from, 'date_to': date_to}
        return self._request('/auth/history/trades', body=body, is_user_method=True)

    # TRADE API
    def auth_r_orders(self, market: str = None):
        """
        List of active orders
        https://docs.kuna.io/docs/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D0%BD%D1%8B%D1%85-%D0%BE%D1%80%D0%B4%D0%B5%D1%80%D0%BE%D0%B2
        :param market: Optional, by default returns all markets
        :return:
        """
        if market:
            path = f'/auth/r/orders/{market}'
        else:
            path = '/auth/r/orders'
        return self._request(path, is_user_method=True)

    def auth_r_orders_hist(self, market: str = None):
        """
        List of executed orders
        https://docs.kuna.io/docs/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%B8%D1%81%D0%BF%D0%BE%D0%BB%D0%BD%D0%B5%D0%BD%D0%BD%D1%8B%D1%85-%D0%BE%D1%80%D0%B4%D0%B5%D1%80%D0%BE%D0%B2
        :param market:
        :return:
        """
        if market:
            path = f'/auth/r/orders/{market}/hist'
        else:
            path = '/auth/r/orders/hist'
        return self._request(path, is_user_method=True)

    def auth_r_order_trades(self, market: str, order_id: int):
        """
        List of dealings for certain order
        https://docs.kuna.io/docs/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D0%BD%D1%8B%D1%85-%D0%BE%D1%80%D0%B4%D0%B5%D1%80%D0%BE%D0%B2
        :param market: like 'btcuah'
        :param order_id: like 10000000
        :return:
        """
        return self._request(f'/auth/r/order/{market}:{order_id}/trades', is_user_method=True)

    def auth_w_order_submit(self, symbol: str, type: str, amount: float, price: float = None, stop_price: float = None):
        """
        Creates order
        https://docs.kuna.io/docs/%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D1%82%D1%8C-%D0%BE%D1%80%D0%B4%D0%B5%D1%80-1
        :param symbol: like 'ethuah'
        :param type: may be 'limit', 'market', 'market_by_quote', 'limit_stop_loss'
        :param amount: if BUY ETH - positive number, if SELL ETH - negative number
        :param price: price for 1 ETH in UAH. Necessary only when type='limit'
        :param stop_price: price when activates 'limit_stop_loss' type order. If None then price
        :return:
        """
        available_types = ('limit', 'market', 'market_by_quote', 'limit_stop_loss')
        if type.lower() not in available_types:
            raise APIError(f'"{type}" is not one of available types {available_types}')

        body = {'symbol': symbol, 'type': type, 'amount': amount, 'price': price, 'stop_price': stop_price}

        return self._request('/auth/w/order/submit', body=body, is_user_method=True)

    def order_cancel(self, order_id: int):
        """
        Cancel one order
        https://docs.kuna.io/docs/%D0%BE%D1%82%D0%BC%D0%B5%D0%BD%D0%B8%D1%82%D1%8C-%D0%BE%D1%80%D0%B4%D0%B5%D1%80
        :param order_id:
        :return: https://docs.kuna.io/reference#postv3ordercancel
        """
        body = {'order_id': order_id}
        return self._request('/order/cancel', body=body, is_user_method=True)

    def order_cancel_multi(self, order_ids: List[int]):
        """
        Cancel many orders
        https://docs.kuna.io/docs/%D0%BE%D1%82%D0%BC%D0%B5%D0%BD%D0%B8%D1%82%D1%8C-%D0%BE%D1%80%D0%B4%D0%B5%D1%80
        :param order_ids:
        :return: https://docs.kuna.io/reference#postv3ordercancelmulti
        """
        body = {'order_ids': order_ids}
        return self._request('/order/cancel/multi', body=body, is_user_method=True)

    # MERCHANT API
    def auth_payment_requests_address(self, currency: str, blockchain: str = None, callback_url: str = None):
        """
        Generates new address for crypto deposit or error if address exists
        https://docs.kuna.io/docs/generate-new-address-for-deposit
        :param currency: like 'usdt'
        :param blockchain: like 'eth', 'trx'
        :param callback_url: to this URL will be send POST-request after successful deposit
        :return:
        """
        body = {'currency': currency, 'blockchain': blockchain, 'callback_url': callback_url}
        return self._request('/auth/payment_requests/address', body=body, is_user_method=True)

    def auth_deposit_info(self, currency: str):
        """
        Get deposit address
        https://docs.kuna.io/docs/%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B8%D1%82%D1%8C-%D0%B0%D0%B4%D1%80%D0%B5%D1%81-%D0%B4%D0%BB%D1%8F-%D0%B4%D0%B5%D0%BF%D0%BE%D0%B7%D0%B8%D1%82%D0%B0
        :param currency: like 'eth'
        :return:
        """
        body = {'currency': currency}
        return self._request('/auth/deposit/info', body=body, is_user_method=True)

    def auth_deposit(self, currency: str, amount: float, payment_service: str, deposit_from: str):
        """
        Deposit fiat money
        https://docs.kuna.io/docs/%D0%BF%D0%BE%D0%BF%D0%BE%D0%BB%D0%BD%D0%B5%D0%BD%D0%B8%D0%B5-%D1%84%D0%B8%D0%B0%D1%82%D0%BE%D0%BC-%D1%81-%D0%B8%D1%81%D0%BF%D0%BE%D0%BB%D1%8C%D0%B7%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%D0%BC-%D1%81%D1%82%D0%B0%D0%BD%D0%B4%D0%B0%D1%80%D1%82%D0%BD%D0%BE%D0%B3%D0%BE-%D0%BF%D0%BB%D0%B0%D1%82%D0%B5%D0%B6%D0%BD%D0%BE%D0%B3%D0%BE-%D1%81%D0%B5%D1%80%D0%B2%D0%B8%D1%81%D0%B0
        :param currency:
        :param amount:
        :param payment_service:
        :param deposit_from:
        :return:
        """
        body = {'currency': currency, 'amount': amount, 'payment_service': payment_service, 'deposit_from': deposit_from}
        return self._request('/auth/deposit', body=body, is_user_method=True)

    def auth_deposit_details(self, id: int):
        """
        Get info about deposin with given ID
        https://docs.kuna.io/docs/get-info-about-deposit
        :param id: like 581303
        :return:
        """
        body = {'id': id}
        return self._request('/auth/deposit/details', body=body, is_user_method=True)

    def auth_withdraw(self, withdraw_type: str, amount: float, address: str = None, gateway: str = None,
                      fields: dict = None, withdraw_to: str = None, fund_source_id: int = None,
                      payment_id: str = None, allow_blank_memo: bool = None, withdrawall: bool = None):
        """
        Create request for withdrawal
        https://docs.kuna.io/docs/create-request-for-withdrawal
        :param withdraw_type: like 'btc' or 'uah'. 'default' for fiat to card
        :param amount: amount to withdraw. By default without fee
        :param address: for crypto withdraw
        :param gateway: for fiat withdraw
        :param withdraw_to: Credit card number
        :param fields: additional params for fiat withdraw
        :param fund_source_id: saved fiat withdraw gateway
        :param payment_id: Memo / Tag / Payment ID etc for cryptos like XRP, EOS, Stellar
        :param allow_blank_memo: should be True if payment_id is blank
        :param withdrawall: if True then amount includes fee
        :return:
        """
        body = {'withdraw_type': withdraw_type,'amount': amount, 'address': address, 'gateway': gateway,
                'fields': fields, 'withdraw_to': withdraw_to, 'fund_source_id': fund_source_id,
                'payment_id': payment_id, 'allow_blank_memo': allow_blank_memo, 'withdrawall': withdrawall}
        return self._request('/auth/withdraw', body=body, is_user_method=True)

    def auth_withdraw_details(self, id: int):
        """
        Get withdraw details by id
        https://docs.kuna.io/docs/get-status-request-for-withdrawal
        :param id:
        :return:
        """
        body = {'id': id}
        return self._request('/auth/withdraw/details', body=body, is_user_method=True)

    def assets_history(self, type: str = None):
        """
        Info about all deposits or withdraws or both
        https://docs.kuna.io/docs/get-deposits-and-withdrawals-history
        :param type: may be 'withdraws' or 'deposits'
        :return:
        """
        if type.lower() not in ['withdraws', 'deposits']:
            raise APIError("type must by 'withdraws', 'deposits' or None")
        if type:
            path = f'/auth/assets-history/{type}'
        else:
            path = '/auth/assets-history'
        return self._request(path, is_user_method=True)

    def auth_merchant_deposit(self, currency: str, amount: float, return_url: str = None, callback_url: str = None):
        """
        Deposit using default payment service
        https://docs.kuna.io/docs/deposits-using-default-payment-service
        :param currency: like 'uah'
        :param amount:
        :param return_url:
        :param callback_url:
        :return:
        """
        body = {'currency': currency, 'amount': amount, 'payment_service': 'default',
                'return_url': return_url, 'callback_url': callback_url}

        return self._request('/auth/merchant/deposit', body=body, is_user_method=True)

    def auth_merchant_payment_services(self, currency: str):
        """
        Get available payment services - gateways
        :param currency: like 'uah'
        :return:
        """
        body = {'currency': currency}
        return self._request('/auth/merchant/payment_services', body=body, is_user_method=True)

    # KUNA CODES
    def kuna_codes_check(self, code: str):
        """
        Check kuna code by first 5 symbols of code
        :param code:
        :return: https://docs.kuna.io/reference#kuna_codes
        """
        return self._request(f'/kuna_codes/{code}/check')

    def kuna_codes(self, currency: str, amount: float, recipient: str = None, non_refundable_before: str = None,
                   comment: str = None, private_comment: str = None):
        """
        Create Kuna code
        https://docs.kuna.io/docs/%D1%81%D0%BE%D0%B7%D0%B4%D0%B0%D1%82%D1%8C-kuna-code
        :param currency: like 'btc'
        :param amount: 0.1
        :param recipient:
        :param non_refundable_before: time in ISO-8601 "YYYY-MM-DDThh:mm:ss" - strftime('%Y-%m-%dT%H:%M:%S')
        :param comment: public comment
        :param private_comment: private comment
        :return:
        """
        body = {'currency': currency, 'amount': amount, 'recipient': recipient,
                'non_refundable_before': non_refundable_before, 'comment': comment, 'private_comment': private_comment}

        return self._request('/auth/kuna_codes', body=body, is_user_method=True)

    def auth_kuna_codes_details(self, id: int):
        """
        Info about code. Only for creator
        https://docs.kuna.io/docs/%D0%BF%D0%BE%D0%BB%D1%83%D1%87%D0%B8%D1%82%D1%8C-%D0%B8%D0%BD%D1%84%D0%BE%D1%80%D0%BC%D0%B0%D1%86%D0%B8%D1%8E-%D0%BE-kuna-code-%D0%BF%D0%BE-id
        :param id:
        :return:
        """
        body = {'id': id}
        return self._request('/auth/kuna_codes/details', body=body, is_user_method=True)

    def auth_kuna_codes_redeem(self, code):
        """
        Activate Kuna code
        https://docs.kuna.io/docs/%D0%BF%D1%80%D0%BE%D0%B2%D0%B5%D1%80%D0%B8%D1%82%D1%8C-kuna-code
        :param code: like "857ny-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX-KUN-KCode"
        :return:
        """
        body = {'code': code}
        return self._request('/auth/kuna_codes/redeem', body=body, is_user_method=True)

    def auth_kuna_codes_issued_by_me(self, page: int = None, per_page: int = None,
                                     order_by: str = None, order_dir: str = None, status: List[str] = None):
        """
        All kuna codes issued by user
        https://docs.kuna.io/docs/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%B2%D1%8B%D0%BF%D1%83%D1%89%D0%B5%D0%BD%D0%BD%D1%8B%D1%85-%D0%BA%D0%BE%D0%B4%D0%BE%D0%B2
        :param page: by default 1
        :param per_page: by default = 10
        :param order_by: order attribute: 'redeemed_at', 'amount', 'created_at' (default)
        :param order_dir: order direction: 'asc', 'desc' (default)
        :param status: filter by status: 'created', 'processing', 'active', 'redeeming', 'redeemed', 'onhold', 'canceled'
        :return:
        """
        body = {'page': page, 'per_page': per_page, 'order_by': order_by, 'order_dir': order_dir, 'status': status}
        return self._request('/auth/kuna_codes/issued-by-me', body=body, is_user_method=True)

    def auth_kuna_codes_redeemed_by_me(self, page: int = None, per_page: int = None, order_by: str = None, order_dir: str = None):
        """
        All kuna codes redeemed by user
        https://docs.kuna.io/docs/%D1%81%D0%BF%D0%B8%D1%81%D0%BE%D0%BA-%D0%B0%D0%BA%D1%82%D0%B8%D0%B2%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%BD%D1%8B%D1%85-%D0%BA%D0%BE%D0%B4%D0%BE%D0%B2
        :param page: by default 1
        :param per_page: by default = 10
        :param order_by: order attribute: 'created_at', 'amount','redeemed_at' (default)
        :param order_dir: order direction: 'asc', 'desc' (default)
        :return:
        """
        body = {'page': page, 'per_page': per_page, 'order_by': order_by, 'order_dir': order_dir}
        return self._request('/auth/kuna_codes/redeemed-by-me', body=body, is_user_method=True)


if __name__ == '__main__':
    from tests.secret import public_key, private_key
    api = KunaAPI(public_key, private_key)
    #res = api.auth_w_order_submit('ethuah', 'limit', 1.0, 600.0)
    res = api.auth_kuna_codes_redeemed_by_me()
    print(res)


