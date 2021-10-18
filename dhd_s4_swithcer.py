import json
import os
import sys
import telnetlib
import threading
import time

from loguru import logger as log

mic_table = {}
is_debug = True


def logger_config(is_debug):
    if os.path.basename(sys.executable) == 'python.exe':
        if is_debug:
            log.remove()
            log.add(sys.stderr, level='DEBUG')
        else:
            log.remove()
            log.add(sys.stderr, level='INFO')
    else:
        log.remove()
    return log.add('./logs/{time:YYYY-MM-DD}.txt', level='DEBUG', rotation='00:00', retention='1 month')


def set_s4_preset(mic):
    try:
        log.debug('s4 send {} '.format(mic))
        instance = telnetlib.Telnet(mic["ip"], 3003)
        instance.read_until('READY\r\n'.encode('ascii'), 3)
        instance.write('login {} {} \r\n'.format(mic["login"], mic["pass"]).encode('ascii'))
        instance.read_until('OK : LOGIN {}\r\n'.format(mic["login"]).encode('ascii'), 3)
        instance.write(('CH{}.Preset.ONAIR={}\r\n'.format(mic["ch"], mic["preset_name"])).encode('ascii'))
        instance.read_until(b'OK\r\n')
        instance.close()
        log.debug('On bigvoice {} ch{} preset is {}'.format(mic["ip"], mic["ch"], mic["preset_name"]))
    except Exception:
        log.error('Cannot set preset on bigvoice')
        return 

def find_key(str):
    for i in mic_table:
        if str.find('030e{}01'.format(i.lower())) != -1:
            log.info('in sting {} find {} mic_table for i {}'.format(str, i, mic_table[i]))
            return i
    return None


def read_dhd(telnet_instance):
    try:
        data = telnet_instance.read_very_eager()
        # data = b'\x03\x0e\x01\xfa\x01\x03\x0e\x01\xfa'
        # data = b'\x03\x0e\x01\xf9\x01'
        if data != b'':
            data_string = data.hex()
            log.info('recieved data {}'.format(data_string))
            res = find_key(data_string)
            if res:
                threading.Thread(target=set_s4_preset, args=(mic_table[res],)).start()


    except Exception:
        e = sys.exc_info()[1]
        log.error(sys.exc_info()[:2])
        return -1


if __name__ == '__main__':
    with open(os.path.join(os.getcwd(), 'settings.json'), encoding='utf8') as f:
        mic_table = json.load(f)
    logger_config(is_debug)
    instance = telnetlib.Telnet('192.168.10.222', 2008)
    while True:
        try:
            res = read_dhd(instance)
            if res == -1:
                log.error("Cannot read data starting new connection")
                instance.close()
                instance = telnetlib.Telnet('192.168.10.222', 2008)
        except Exception:
            time.sleep(10)
        time.sleep(0.1)
