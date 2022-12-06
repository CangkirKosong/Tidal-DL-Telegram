#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File    :   __init__.py
@Time    :   2020/11/08
@Author  :   Yaronzz
@Version :   2.1
@Contact :   yaronhuang@foxmail.com
@Desc    :   
'''
from faulthandler import disable
import getopt
import ssl
import sys
import time

from aigpy.cmdHelper import green, yellow
from aigpy.pathHelper import mkdirs
from aigpy.pipHelper import getLastVersion
from aigpy.stringHelper import isNull
from aigpy.systemHelper import cmpVersion

from tidal_dl.download import start
from tidal_dl.enums import AudioQuality, VideoQuality, Type
from tidal_dl.lang.language import setLang, initLang, getLangChoicePrint
from tidal_dl.printf import Printf, VERSION
from tidal_dl.settings import Settings, TokenSettings, getLogPath
from tidal_dl.tidal import TidalAPI
from tidal_dl.util import API, CONF, TOKEN, LANG, displayTime, loginByConfig, loginByWeb
import tidal_dl.apiKey as apiKey

from bot.helpers.translations import lang
from bot.helpers.database.postgres_impl import TidalSettings
from bot.helpers.buttons.settings_buttons import tidal_auth_set

set_db = TidalSettings()

ssl._create_default_https_context = ssl._create_unverified_context

def login(bot=None, chat_id=None, update=None):
    """if bot:
        td_msg = bot.send_message(
            chat_id=chat_id,
            text=LANG.AUTH_START_LOGIN,
            reply_to_message_id=reply_to_id,
            disable_web_page_preview=True
        )
    else:
        print(LANG.AUTH_START_LOGIN)"""
    msg, check = API.getDeviceCode()
    if not check:
        Printf.err(msg)
        return

    # print(LANG.AUTH_LOGIN_CODE.format(green(API.key.userCode)))
    if bot:
        bot.edit_message_text(
            chat_id=chat_id,
            message_id=update.message.id, 
            text=LANG.AUTH_NEXT_STEP.format(
                "http://" + API.key.verificationUrl + "/" + API.key.userCode, 
                displayTime(API.key.authCheckTimeout)
            ),
            disable_web_page_preview=True
        )
    else:
        print(LANG.AUTH_NEXT_STEP.format(green("http://" + API.key.verificationUrl + "/" + API.key.userCode), yellow(displayTime(API.key.authCheckTimeout))))
        print(LANG.AUTH_WAITING)
    if bot:
        loginByWeb(bot, chat_id, update)
    else:
        loginByWeb()
    return


def setAccessToken():
    while True:
        print("-------------AccessToken---------------")
        token = Printf.enter("accessToken('0' go back):")
        if token == '0':
            return
        msg, check = API.loginByAccessToken(token, TOKEN.userid)
        if not check:
            Printf.err(msg)
            continue
        break

    print("-------------RefreshToken---------------")
    refreshToken = Printf.enter("refreshToken('0' to skip):")
    if refreshToken == '0':
        refreshToken = TOKEN.refreshToken

    TOKEN.accessToken = token
    TOKEN.refreshToken = refreshToken
    TOKEN.expiresAfter = 0
    TOKEN.countryCode = API.key.countryCode
    TokenSettings.save(TOKEN)


def setAPIKey():
    global LANG
    item = apiKey.getItem(CONF.apiKeyIndex)
    ver  = apiKey.getVersion()
    Printf.info(f'Current APIKeys: {str(CONF.apiKeyIndex)} {item["platform"]}-{item["formats"]}')
    Printf.info(f'Current Version: {str(ver)}')
    Printf.apikeys(apiKey.getItems())
    index = int(Printf.enterLimit("APIKEY index:", LANG.MSG_INPUT_ERR, apiKey.getLimitIndexs()))
    
    if index != CONF.apiKeyIndex:
        CONF.apiKeyIndex = index
        Settings.save(CONF)
        API.apiKey = apiKey.getItem(index)
        return True
    return False


def checkLogin(bot=None, chat_id=None, update=None, force_auth=False):
    txt, _ = set_db.get_variable("AUTH_DONE")
    if txt:
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                text=lang.ALREADY_AUTH.format(
                    displayTime(int(TOKEN.expiresAfter - time.time()))
                ),
                message_id=update.message.id,
                reply_markup=tidal_auth_set()
            )
        except:
            pass
        return True
    else:
        if force_auth:
            login(bot, chat_id, update)
            return
        else:
            return False

def checkLogout():
    login()
    return


def changeSettings():
    global LANG
    Printf.settings(CONF)
    choice = Printf.enter(LANG.CHANGE_START_SETTINGS)
    if choice == '0':
        return

    CONF.downloadPath = Printf.enterPath(LANG.CHANGE_DOWNLOAD_PATH, LANG.MSG_PATH_ERR, '0', CONF.downloadPath)
    CONF.audioQuality = AudioQuality(int(Printf.enterLimit(
        LANG.CHANGE_AUDIO_QUALITY, LANG.MSG_INPUT_ERR, ['0', '1', '2', '3'])))
    CONF.videoQuality = VideoQuality(int(Printf.enterLimit(
        LANG.CHANGE_VIDEO_QUALITY, LANG.MSG_INPUT_ERR, ['1080', '720', '480', '360'])))
    CONF.onlyM4a = Printf.enter(LANG.CHANGE_ONLYM4A) == '1'
    CONF.checkExist = Printf.enter(LANG.CHANGE_CHECK_EXIST) == '1'
    CONF.includeEP = Printf.enter(LANG.CHANGE_INCLUDE_EP) == '1'
    CONF.saveCovers = Printf.enter(LANG.CHANGE_SAVE_COVERS) == '1'
    CONF.showProgress = Printf.enter(LANG.CHANGE_SHOW_PROGRESS) == '1'
    CONF.saveAlbumInfo = Printf.enter(LANG.CHANGE_SAVE_ALBUM_INFO) == '1'
    CONF.showTrackInfo = Printf.enter(LANG.CHANGE_SHOW_TRACKINFO) == '1'
    CONF.usePlaylistFolder = Printf.enter(LANG.SETTING_USE_PLAYLIST_FOLDER + "('0'-No,'1'-Yes):") == '1'
    CONF.language = Printf.enter(LANG.CHANGE_LANGUAGE + "(" + getLangChoicePrint() + "):")
    CONF.albumFolderFormat = Printf.enterFormat(
        LANG.CHANGE_ALBUM_FOLDER_FORMAT, CONF.albumFolderFormat, Settings.getDefaultAlbumFolderFormat())
    CONF.trackFileFormat = Printf.enterFormat(LANG.CHANGE_TRACK_FILE_FORMAT,
                                              CONF.trackFileFormat, Settings.getDefaultTrackFileFormat())
    CONF.addLyrics = Printf.enter(LANG.CHANGE_ADD_LYRICS) == '1'
    CONF.lyricsServerProxy = Printf.enterFormat(
        LANG.CHANGE_LYRICS_SERVER_PROXY, CONF.lyricsServerProxy, CONF.lyricsServerProxy)
    CONF.lyricFile = Printf.enter(LANG.CHANGE_ADD_LRC_FILE) == '1'
    CONF.addTypeFolder = Printf.enter(LANG.CHANGE_ADD_TYPE_FOLDER) == '1'

    LANG = setLang(CONF.language)
    Settings.save(CONF)


def mainCommand():
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hvl:o:q:r:", ["help", "version",
                                                                "link=", "output=", "quality", "resolution"])
    except getopt.GetoptError as errmsg:
        Printf.err(vars(errmsg)['msg'] + ". Use 'tidal-dl -h' for useage.")
        return

    link = None
    for opt, val in opts:
        if opt in ('-h', '--help'):
            Printf.usage()
            continue
        if opt in ('-v', '--version'):
            Printf.logo()
            continue
        if opt in ('-l', '--link'):
            checkLogin()
            link = val
            continue
        if opt in ('-o', '--output'):
            CONF.downloadPath = val
            Settings.save(CONF)
            continue
        if opt in ('-q', '--quality'):
            CONF.audioQuality = Settings.getAudioQuality(val)
            Settings.save(CONF)
            continue
        if opt in ('-r', '--resolution'):
            CONF.videoQuality = Settings.getVideoQuality(val)
            Settings.save(CONF)
            continue

    if not mkdirs(CONF.downloadPath):
        Printf.err(LANG.MSG_PATH_ERR + CONF.downloadPath)
        return

    if link is not None:
        Printf.info(LANG.SETTING_DOWNLOAD_PATH + ':' + CONF.downloadPath)
        start(TOKEN, CONF, link)


def debug():
    checkLogin()
    API.key.accessToken = TOKEN.accessToken
    API.key.userId = TOKEN.userid
    API.key.countryCode = TOKEN.countryCode
    # https://api.tidal.com/v1/mixes/{01453963b7dbd41c8b82ccb678d127/items?countryCode={country}
    API.getMix("01453963b7dbd41c8b82ccb678d127")
    # msg, result = API.search('Mojito', Type.Null, 0, 10)
    msg, lyric = API.getLyrics('144909909')
    pass


def main():
    if len(sys.argv) > 1:
        mainCommand()
        return

    Printf.logo()
    Printf.settings(CONF)

    checkLogin()

    # onlineVer = getLastVersion('tidal-dl')
    # if not isNull(onlineVer):
    #     icmp = cmpVersion(onlineVer, VERSION)
    #     if icmp > 0:
    #         Printf.info(LANG.PRINT_LATEST_VERSION + ' ' + onlineVer)

    # Printf.info("For some reasons, this version only supports LOSSLESS.")

    while True:
        Printf.choices()
        choice = Printf.enter(LANG.PRINT_ENTER_CHOICE)
        if choice == "0":
            return
        elif choice == "1":
            checkLogin()
        elif choice == "2":
            changeSettings()
        elif choice == "3":
            checkLogout()
        elif choice == "4":
            setAccessToken()
        elif choice == '5':
            if setAPIKey():
                checkLogout()
        elif choice == "10":  # test track
            start(TOKEN, CONF, '70973230')
        elif choice == "11":  # test video
            start(TOKEN, CONF, '188932980')
        elif choice == "12":  # test album
            start(TOKEN, CONF, '58138532')
        elif choice == "13":  # test playlist
            start(TOKEN, CONF, '98235845-13e8-43b4-94e2-d9f8e603cee7')
        elif choice == "14":  # test playlist
            start(TOKEN, CONF, '01453963b7dbd41c8b82ccb678d127')
        else:
            start(TOKEN, CONF, choice)


#if __name__ == "__main__":
    # debug()
    #main() 
    # test example
    # track 70973230  77798028 212657
    # video 155608351 188932980
    # album 58138532  77803199  21993753   79151897  56288918
    # playlist 98235845-13e8-43b4-94e2-d9f8e603cee7
