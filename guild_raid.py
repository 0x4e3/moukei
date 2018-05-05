import datetime
import time

import pytz

from telegram.ext import (
    Updater,
    MessageHandler,
    Filters,
    InlineQueryHandler
)
from threading import Timer
from storage import *


def sendGraph(bot, chat, graph):
    print("HERE")
    if graph is not None:
        if graph[-4:] == '.gif':
            bot.sendDocument(chat, graph)
        else:
            bot.sendPhoto(chat, graph)


class Reminder:
    def __init__(self, updater, data):
        self.updater = updater
        self.data = data
        self.update()

    def update(self):
        wait = 3600  # a hour

    for key in self.data.raids:
        print("\ncheck raid: %d" % key)
        currWait = self.updateRaid(
            self.data.raids[key],
            self.data.raids_details[key])

        if currWait < wait:
            wait = currWait
 
    if wait <= 0:
        wait = 60
    print("strat timer for %d seconds" % wait)
    self.raidTimer = Timer(wait, self.update)
    self.timeout = wait
    self.time_start = time.time()
    self.raidTimer.start()

    def sendToAll(self, txt, img):
        for key in self.data.users:
            try:
                self.updater.bot.send_message(chat_id=key, text=txt)
                sendGraph(self.updater.bot, key, img)
            except:
                pass
 
    def updateRaid(self, raid, details):
        firstBegin = raid[0]
        period = raid[1]

        print("Raid first begin at: %s" % firstBegin)
        print("Raid period: %d" % period)

        tz = pytz.timezone('Europe/Moscow')
        today = datetime.datetime.now(tz)
        begin = firstBegin
        warnDelta = 5 # sec

        #print("raw system dt: %s" % datetime.datetime.now())
        #print("utc system dt: %s" % today)

        if today > begin:
            print("calc current begin")
            diff = int((today - firstBegin).total_seconds())
            print("diff: %d" % diff)
            n = diff // period
            print("n: %d" % n)
            begin = firstBegin + datetime.timedelta(seconds=n*period)
        else:
            print("first begin is current!")
            pass

        print("Current begin date: %s" % begin)

        for detail in details:
            if detail[1] is not None:
                stageBegin = begin + datetime.timedelta(seconds=detail[0])
                #print("Stage begin: %s" % stageBegin)
                if today < stageBegin:
                    if today + datetime.timedelta(seconds=warnDelta) > stageBegin:
                        #print("curr stage ALARM!!!")
                        self.sendToAll(detail[1], detail[2])
                        return warnDelta
                    else:
                        tm = int((stageBegin - today).total_seconds())
                        #print("curr stage is next! wait: %d seconds" % tm)
                        return tm
        tm = int(((begin + datetime.timedelta(seconds=period)) - today).total_seconds())
        #print("Raid ended!!! Wait %d secconds to new one" % tm)
        return tm

    def diag(self, bot, update):
        for key in self.data.raids:
            self.logRaid(key, bot, update)
     
        wait = 3600 # a hour

        for key in self.data.raids:
            currWait = self.updateRaid(
                self.data.raids[key], self.data.raids_details[key])
            if currWait < wait:
                wait = currWait 
     
        try:
            msg = 'До следуюущего события осталось ' + str(wait) + ' секунд\n'
            msg += 'Таймер: ' + str(self.timeout - (time.time() - self.time_start)) + ' секунд\n'
            bot.send_message(chat_id=update.message.chat_id, text=msg)
        except:
            pass
     
    def shedule(self, bot, update):
        self.logRaid(1, bot, update)
        self.logRaid(2, bot, update)
 
    def logRaid(self, key, bot, update):
        raid = self.data.raids[key]
        details = self.data.raids_details[key]
        firstBegin = raid[0]
        period = raid[1]

        tz = pytz.timezone('Europe/Moscow')
        today = datetime.datetime.now(tz)
        begin = firstBegin
        n = 0

        msg = ''
        if RaidType(key) is RaidType.rankor:
            msg = '=== РЕЙД ЯМА === \n'
        elif RaidType(key) is RaidType.aat:
            msg = '=== РЕЙД ТАНК ===\n'
        elif RaidType(key) is RaidType.tickets:
            msg = '=== Энка ===\n'

        if today > begin:
            diff = int((today - firstBegin).total_seconds())
            n = diff // period
        else:
            pass

        for i in range(n, n+3):
            begin = firstBegin + datetime.timedelta(seconds=i*period)
            for detail in details:
                if detail[3] is not None:
                    stageBegin = begin + datetime.timedelta(seconds=detail[0])
                    msg += '   ' + stageBegin.strftime("%d.%m %H:%M") + ' - ' + detail[3] + '\n'
            msg += '\n'

        try:
            bot.send_message(chat_id=update.message.chat_id, text=msg)
        except:
            pass
