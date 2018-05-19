#! python2
# -*- coding: utf-8 -*-

import sys
import os
import re
import binascii
import hashlib
import base64
import urllib
import urllib2
import json
import random
import requests
from Crypto.Cipher import AES
from http.cookiejar import LWPCookieJar

#set cookie
cookie_opener = urllib2.build_opener()
#cookie_opener.addheaders.append(('Cookie', 'appver=2.0.2'))
cookie_opener.addheaders.append(('Referer', 'http://music.163.com'))
urllib2.install_opener(cookie_opener)

header = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip,deflate,sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,gl;q=0.6,zh-TW;q=0.4',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded',
    'Host': 'music.163.com',
    'Referer': 'http://music.163.com/search/',
    'User-Agent':
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_2) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/33.0.1750.152 Safari/537.36'  # NOQA
}
modulus = ('00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7'
           'b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280'
           '104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932'
           '575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b'
           '3ece0462db0a22b8e7')
nonce = '0CoJUm6Qyw8W8jud'
pubKey = '010001'

conf_dir = os.path.join(os.path.expanduser('~'), '.netease-box')
cookie_path = os.path.join(conf_dir, 'cookie')

if not os.path.isdir(conf_dir):
    os.mkdir(conf_dir)
    open(os.path.join(conf_dir, 'cookie'),"w+").close()
    

#歌曲加密算法
'''
def encrypted_id(id):
    byte1 = bytearray('3go8&$8*3*3h0k(2)2')
    byte2 = bytearray(id)
    byte1_len = len(byte1)
    for i in xrange(len(byte2)):
        byte2[i] = byte2[i]^byte1[i%byte1_len]
    m = md5.new()
    m.update(byte2)
    result = m.digest().encode('base64')[:-1]
    result = result.replace('/', '_')
    result = result.replace('+', '-')
    return result
'''
def encrypted_id(id):
    magic = bytearray('3go8&$8*3*3h0k(2)2', 'u8')
    song_id = bytearray(id, 'u8')
    magic_len = len(magic)
    for i, sid in enumerate(song_id):
        song_id[i] = sid ^ magic[i % magic_len]
    m = hashlib.sha512(song_id)
    result = m.digest()
    result = base64.b64encode(result)
    result = result.replace(b'/', b'_')
    result = result.replace(b'+', b'-')
    return result.decode('utf-8')
    
def createSecretKey(size):
    return binascii.hexlify(os.urandom(size))[:16]
    
def aesEncrypt(text, secKey):
    pad = 16 - len(text) % 16
    text = text + chr(pad) * pad
    encryptor = AES.new(secKey, 2, '0102030405060708')
    ciphertext = encryptor.encrypt(text)
    ciphertext = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext

def rsaEncrypt(text, pubKey, modulus):
    text = text[::-1]
    rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
    return format(rs, 'x').zfill(256)    
    
# 登录加密算法
def encrypted_request(text):
    text = json.dumps(text)
    secKey = createSecretKey(16)
    encText = aesEncrypt(aesEncrypt(text, nonce), secKey)
    encSecKey = rsaEncrypt(secKey, pubKey, modulus)
    data = {'params': encText, 'encSecKey': encSecKey}
    return data

def songs_detail_new_api(music_ids):
    session = requests.Session()
    bit_rate = 320000
    session.cookies = LWPCookieJar(cookie_path)
    try:
        session.cookies.load()
        cookie = ''
        if os.path.isfile(cookie_path):
            file = open(cookie_path, 'r')
            cookie = file.read()
            file.close()
        expire_time = re.compile(r'\d{4}-\d{2}-\d{2}').findall(cookie)
        if expire_time:
            if expire_time[0] < time.strftime('%Y-%m-%d', time.localtime(time.time())):
                os.remove(cookie_path)
    except IOError as e:
        session.cookies.save()
    
    action = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='  # NOQA
    session.cookies.load()
    csrf = ''
    for cookie in session.cookies:
        if cookie.name == '__csrf':
            csrf = cookie.value
    action += csrf
    print action
    data = {'ids': music_ids, 'br': bit_rate, 'csrf_token': csrf}
    connection = session.post(action,
                              data=encrypted_request(data),
                              headers=header, )
    result = json.loads(connection.text)
    print result
    return result['data']

def save_song_to_disk(song, folder):
    name = song['name']
    fpath = os.path.join(folder, name+'.mp3')
    if os.path.exists(fpath):
        return
    
    song_id = str(song['bMusic']['id'])
    url = songs_detail_new_api(song_id)[0]['url']
    '''
    song_dfsId = str(song['bMusic']['dfsId'])
    url = 'http://m%d.music.126.net/%s/%s.mp3' % (random.randrange(1, 3), encrypted_id(song_dfsId), song_dfsId)
    '''
    print '%s\t%s' % (url, name)
    #return
    resp = urllib2.urlopen(url)
    data = resp.read()
    f = open(fpath, 'wb')
    f.write(data)
    f.close()

def get_album_songs(album):
    url = 'http://music.163.com/api/album/%d/' % album['id']
    resp = urllib2.urlopen(url)
    songs = json.loads(resp.read())
    if songs['code'] == 200 and len(songs['album']) > 0:
        return songs['album']['songs']
    else:
        return None
    
def search_album_by_name(name):
    search_url = 'http://music.163.com/api/search/get'
    params = {
        's': name,
        'type': 10,
        'offset': 0,
        'sub': 'false',
        'limit': 20  
    }
    params = urllib.urlencode(params)
    resp = urllib2.urlopen(search_url, params)
    resp_js = json.loads(resp.read())
    if resp_js['code'] == 200 and resp_js['result']['albumCount'] > 0:
        result = resp_js['result']
        album_id = 0
        '''
        if result['albumCount'] > 1:
            for i in range(len(result['albums'])):
                album = result['albums'][i]
                print '[%2d]artist:%s\talbum:%s' % (i+1, album['artist']['name'], album['name'])
            select_i = int(raw_input('Select One: '))
            if select_i < 1 or select_i > (len(result['albums'])):
                print 'Error select!'
                return None
            else:
                album_id = select_i - 1
        '''
        return result['albums'][album_id]
    else:
        return None

    
def download_album_by_search(name, folder='.'):
    album = search_album_by_name(name)
    if not album:
        print 'Not Found album: ' + name
        return
    
    name = album['name']
    folder = os.path.join(folder, name)
    
    if not os.path.exists(folder):
        os.makedirs(folder)
        
    songs = get_album_songs(album)
    #for song in songs:
    save_song_to_disk(songs[0], folder)
    
    
if __name__ == '__main__':
    if len(sys.argv) < 3:
        sys.exit(0)
    download_album_by_search(sys.argv[1], sys.argv[2])
    
