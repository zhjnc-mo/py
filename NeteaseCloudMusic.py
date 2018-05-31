#! python2
# -*- coding: utf-8 -*-

import sys
import os
import re
import time 
import base64
import binascii
import hashlib
import urllib
import urllib2
import json
import threadpool
import subprocess
import requests
from Crypto.Cipher import AES
import threading

search_url = "http://music.163.com/api/search/pc"
song_url = "http://music.163.com/weapi/song/enhance/player/url?csrf_token="    
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

class CloudMusic():
    def __init__(self, ui, txt):
        self.mUI = ui
        self.kgMusic = KuGouMusic()
        self.downloadDir = txt
        self.pool = threadpool.ThreadPool(4)
        if not os.path.exists(self.downloadDir):
            os.makedirs(self.downloadDir)
    
    def rsa_encrypt(self, secKey, pubKey, modulus):
        text = secKey[::-1]
        rs = pow(int(binascii.hexlify(text), 16), int(pubKey, 16), int(modulus, 16))
        return format(rs, 'x').zfill(256)

    def aesEncrypt(self, text, secKey):
        pad = 16 - len(text) % 16
        text = text + chr(pad) * pad
        encryptor = AES.new(secKey, 2, '0102030405060708')
        ciphertext = encryptor.encrypt(text)
        ciphertext = base64.b64encode(ciphertext).decode('utf-8')
        return ciphertext

    def create_params(self, song_id):
        text = '{"ids":[' + str(song_id) + '], br:"320000",csrf_token:"csrf"}'
        nonce2 = 16 * 'F'
        encText = self.aesEncrypt(self.aesEncrypt(text, nonce).decode("utf-8"), nonce2)
        return encText

    def encrypted_request(self, text):
        text = json.dumps(text)
        secKey = binascii.hexlify(os.urandom(16))[:16]
        encText = self.aesEncrypt(self.aesEncrypt(text, nonce), secKey)
        encSecKey = self.rsa_encrypt(secKey, pubKey, modulus)
        data = {'params': encText, 'encSecKey': encSecKey}
        return data
        
    def download_song_by_id(self, song_id, nameSty=1, dDir = "000"):
        if dDir == "000":
            dDir = self.downloadDir

        self.mUI.msgBox.appendPlainText("downloading...." + song_id)
        try:
            data = {
                'params': self.create_params(song_id),
                'encSecKey': self.rsa_encrypt(secKey, pubKey, modulus)
            }
            
            req = requests.post(
                song_url, headers=header, data = data, timeout=10
            ).json()

            sn, ar = self.get_song_info_by_id(song_id)
            song_name = sn + " - " + ar
            if nameSty == 0:
                song_name = ar + " - " + sn
            print song_name

            if req['code'] == 200:
                #print req['data'][0]['url']
            
                fpath = os.path.join(dDir, song_name+'.mp3')
                if os.path.exists(fpath):
                    return "歌曲已存在"

                if req['data'][0]['url'] <> None: 
                    new_url = req['data'][0]['url']
                    resp = urllib2.urlopen(new_url)
                    data = resp.read()
                    f = open(fpath, 'wb')
                    f.write(data)
                    f.close()
                    self.mUI.msgBox.appendPlainText(song_id + " Download success")
                    return req['data'][0]['url'] + " == Download success"
                else:
                    print "err01:" + str(req)
                    self.mUI.msgBox.appendPlainText("Search "+ song_name + " by KuGou")
                    self.kgMusic.search_music_by_keyword(song_name, nameSty, dDir)
                    #return "无法获取链接"
            else:
                print "err02:" + str(req)
                return "连接错误  error code = " + req['code']
        except Exception as e:
            raise

    def download_album_by_id(self, album_id, nameSty):
        album_url = 'http://music.163.com/api/album/%s/' % album_id
        resp = requests.post(album_url, headers=header, timeout=10).json()
        if resp['code'] == 200 and len(resp['album']) > 0:
            #create dir
            albumDir = os.path.join(self.downloadDir, resp['album']['name'])
            if not os.path.exists(albumDir):
                os.makedirs(albumDir)

            songs = resp['album']['songs']

            arg_list = []
            for i in range(len(songs)):
                arg_list.append( (None, {'song_id':str(songs[i]['id']), 'nameSty':nameSty, 'dDir':albumDir}) )
                
            reqs = threadpool.makeRequests(self.download_song_by_id, arg_list)
            map(self.pool.putRequest, reqs)
            self.pool.poll()
            
            return "下载"+str(len(songs))+"首歌"
        else:
            return "无法找到专辑"

    def download_mlist_by_id(self, list_id, nameSty):
        mList_url = "http://music.163.com/weapi/v3/playlist/detail?csrf_token="
        data = {
            "id": list_id,
            "offset": 0,
            "total": "true",
            "limit": 1000,
            "n": 1000,
            "csrf_token": "csrf"
        }
        req = requests.post(
            mList_url, headers=header, data = self.encrypted_request(data), timeout=10
        ).json()
        
        if req['code'] == 200 and req['playlist']['trackCount'] > 0:
            mListDir = os.path.join(self.downloadDir, str(req['playlist']['id']))
            if not os.path.exists(mListDir):
                os.makedirs(mListDir)

            songs = req['playlist']['tracks']

            arg_list = []
            for i in range(len(songs)):
                arg_list.append( (None, {'song_id':str(songs[i]['id']), 'nameSty':nameSty, 'dDir':mListDir}) )

            reqs = threadpool.makeRequests(self.download_song_by_id, arg_list)
            map(self.pool.putRequest, reqs)
            self.pool.poll()
            
            return "下载"+str(req['playlist']['trackCount'])+"首歌"
        else:
            return "无法找到歌单"

    def search_song_by_name(self, key):
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
                self.download_song_by_id(str(song_id))
        except Exception as e:
            raise

    def get_song_info_by_id(self, song_id):
        info_url = "https://api.imjad.cn/cloudmusic/?type=detail&id=" + song_id
        req = requests.get(info_url).json()
        name = str(song_id)
        ar = '未知艺术家'
        if req['code'] == 200:
            name = req['songs'][0]['name']
            ar = req['songs'][0]['ar'][0]['name']
        return name, ar

kgSearchUrl = "http://songsearch.kugou.com/song_search_v2"
kgGetDownloadUrl = "http://www.kugou.com/yy/index.php"
class KuGouMusic(object):
    def __init__(self):
        super(KuGouMusic, self).__init__()

    def search_music_by_keyword(self, keyword, nameSty, downDir):
        self.nameSty = nameSty
        self.downDir = downDir
        payload = {
            'keyword': keyword,
            'page': 1,
            'pagesize': 1,
            'userid': -1,
            'clientver': "",
            'platform': 'WebFilter',
            'tag': 'em',
            'filter': 2,
            'iscorrection': 1,
            'privilege_filter': 0
        }
        req = requests.get(kgSearchUrl, params=payload).json()
        # print req.url
        if req['error_code'] == 0:
            file_hash = req['data']['lists'][0]['FileHash']
            album_id = req['data']['lists'][0]['AlbumID']
            #print "FileHash=" + file_hash
            self.kg_download(file_hash, album_id)
        else:
            print "KuGou 查找失败"
        pass

    def kg_download(self, file_hash, album):
        payload = {
            'r': 'play/getdata',
            'hash': file_hash,
            'album_id': album,
            '_': '1497972864535'
        }
        req = requests.get(kgGetDownloadUrl, params=payload).json()
        if req['err_code'] == 0:
            song_name = req['data']['song_name'] + " - " + req['data']['author_name']
            if self.nameSty == 0:
                song_name = req['data']['author_name'] + " - " + req['data']['song_name']
            print song_name

            fpath = os.path.join(self.downDir, song_name+'.mp3')
            new_url = req['data']['play_url']
            resp = urllib2.urlopen(new_url)
            data = resp.read()
            f = open(fpath, 'wb')
            f.write(data)
            f.close()
            print song_name + " Download success"
        pass
        

# if __name__ == '__main__':
#     if len(sys.argv) < 2:
#         sys.exit(0)
#     search_song_by_name(sys.argv[1])
    #download_song_by_id(sys.argv[1])