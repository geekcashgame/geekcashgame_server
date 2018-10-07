import requests
import json
import time
from decimal import Decimal
import datetime
import log

def get_current_strtime():
    return time.strftime('%Y-%m-%d %H:%M:%S')


def log(log_str):
    sys_time = get_current_strtime()
    slog = '[{0}] {1}'.format(sys_time, log_str)
    log.Info(slog)


def get_format_json(data):
    try:
        json_str = json.dumps(data, indent=4,separators=(',',':'))
        return json_str
    except:
        log('get fromat json error: {}'.format(data))
        return ''


def timestamp2localtime(timestamp):
    timeArray = time.localtime(timestamp)
    otherStyleTime = time.strftime("%Y-%m-%d %H:%M:%S", timeArray)
    return otherStyleTime   # 2013-10-10 23:40:00


def timestamp2utctime(timestamp):
    dateArray = datetime.datetime.utcfromtimestamp(timestamp)
    otherStyleTime = dateArray.strftime("%Y-%m-%d %H:%M:%S")
    return otherStyleTime   # 2013-10-10 15:40:00


def get_precision(value, precision):
    if value < 0:
        sign = -1
    else:
        sign = 1

    value = abs(float(value))

    if value == 0.0:
        return value

    #if precision <= 0:
     #   return int(float(value))

    if precision > 20:
        tmpPrecision = precision + 10
    else:
        tmpPrecision = 20

    decimalStr = '0.' + '0' * tmpPrecision
    valueStr = str(Decimal(value).quantize(Decimal(decimalStr)))

    valueArray = valueStr.split('.')
    integerPart = valueArray[0]
    decimalPart = valueArray[1][0:precision]
    resultValueStr = integerPart + "." + decimalPart
    resultValue = float(resultValueStr)

    return resultValue * sign



def http_post_request(url, params, add_to_headers=None):
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json;charset=UTF-8',
        "origin": "https://explorer.geekcash.org",
        "referer": "https://explorer.geekcash.org/address/GaZVcUBuuMPbdqhf6uoR85vkVXYPfcpiLK",
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36',
    }
    if add_to_headers:
        headers.update(add_to_headers)

    postdata = json.dumps(params)

    response = requests.post(url, postdata, headers=headers, timeout=10)
    log.Info(response.text)
    json_obj = json.loads(response.text)
    return json_obj