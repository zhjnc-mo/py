#! python2
# -*- coding: utf-8 -*-

import sys
import os
import base64
import binascii
import hashlib
import urllib
import urllib2
import json
import subprocess
import requests
from Crypto.Cipher import AES

search_url = "http://music.163.com/api/search/pc"
url = "http://music.163.com/weapi/song/enhance/player/url?csrf_token="    
header = {
    'Referer': 'http://music.163.com/',
    'Host': 'music.163.com',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.95 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
}
modulus = '00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7'
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'
secKey = 16 * 'F'

aria2c_parameters = {
    'value': [],
    'default': [],
    'describe': 'The additional parameters when aria2c start to download something.'
}

def rsa_encrypt(secKey, pubKey, modulus):
    text = secKey[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)

def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext

def create_params(song_id):
    text = '{"ids":[' + str(song_id) + '], br:"320000",csrf_token:"csrf"}'
    nonce2 = 16 * 'F'
    encText = aesEncrypt(aesEncrypt(text, nonce).decode("utf-8"), nonce2)
    return encText
    
def download_by_id(song_id):
    data = {
        'params': create_params(song_id),
        'encSecKey': rsa_encrypt(secKey, pubKey, modulus)
    }
    fpath = os.path.join('.', song_id+'.mp3')
    if os.path.exists(fpath):
        return
    
    try:
        req = requests.post(
            url, headers=header, data = data, timeout=10
        ).json()
        if req['code'] == 200:
            #print req['data'][0]['url']
            if req['data'][0]['url'] <> None: 
                new_url = req['data'][0]['url']
                resp = urllib2.urlopen(new_url)
                data = resp.read()
                f = open(fpath, 'wb')
                f.write(data)
                f.close()
            else:
                print "err:" + str(req)
        else:
            print "err:" + str(req)
    except Exception as e:
        raise

def search_song_by_name(key):
    data = {
        's': key,
        'limit': 20,
        'type': 1,
        'offset':0
    }
    try:
        req = requests.post(
            search_url, headers=header, data = data, timeout=10
        ).json()
        if req['code'] == 200 and req['result']['songCount'] > 0:
            songs = req['result']['songs']
            song_id = req['result']['songs'][0]['id']
            if req['result']['songCount'] > 1:
                for i in range(len(songs)):
                    song_info = songs[i]
                    print '[%2d]artist: %s\talbum: %s' % (i+1, song_info['artists'][0]['name'], song_info['album']['name'])
                select_i = int(raw_input('Select One:'))
                if select_i < 1 or select_i > len(songs):
                    print 'error select'
                    return None
                else:
                    song_id = req['result']['songs'][select_i-1]['id']
            download_by_id(str(song_id))
    except Exception as e:
        raise

if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(0)
    search_song_by_name(sys.argv[1])
    #download_by_id(sys.argv[1])