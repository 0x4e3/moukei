import os
import urllib.parse as urlparse
from array import *

import psycopg2
from enum import Enum


class RaidType(Enum):
    tickets = 0
    rankor = 1
    aat = 2


class Data(object):
    def __init__(self):
        print("Init storage!")
        self.conn = self.connectToDataBase()

    if self.conn is not None:
        self.create_tables()

        cur = None
        try:
            cur = self.conn.cursor()
        except psycopg2.Error as e:
            print("PG Error: %s" % e.pgerror)

        if cur is not None:
            print("create users dict")
            self.users = {}
            self.raids = {}
            self.raids_details = {}

            try:
                cur.execute("""set timezone = 'Europe/Moscow'""")
                print("PG timezone is set!")
            except psycopg2.Error as e:
                print("PG Error: %s" % e.pgerror)

            try:
                cur.execute("""SELECT chat_id, username from bot_users""")
                rows = cur.fetchall()

                for row in rows:
                    self.users[int(row[0])] = row[1]
                    print("Loaded user [%s] with chat id = %s" %
                          (row[1], row[0]))
            except psycopg2.Error as e:
                print("PG Error: %s" % e.pgerror)

        try:
            cur.execute("""SELECT type, start, period from bot_raid""")
            rows = cur.fetchall()

            for row in rows:
                raidType = int(row[0])
                self.raids[raidType] = [row[1], int(row[2])]
                print("Loaded raid [%d] with start stamp = %s, period = %d" % (
                    raidType,
                    self.raids[raidType][0],
                    self.raids[raidType][1]))

            cur.execute("""
                SELECT type, start, msg, icon, info from bot_raid_stages
                ORDER BY type, start
            """)
            rows = cur.fetchall()

            for row in rows:
                raidType = int(row[0])
                if raidType not in self.raids_details:
                    self.raids_details[raidType] = []
                self.raids_details[raidType].append(
                    [int(row[1]), row[2], row[3], row[4]])
                print("Loaded raid_details [%d] with start = %d, msg = %s, "
                      "icon = %s" %
                      (raidType, int(row[1]), row[2], row[3]))
        except psycopg2.Error as e:
            print("PG Error: %s" % e.pgerror)

    def create_tables(self):
        cur = None
        try:
            cur = self.conn.cursor()
        except psycopg2.Error as e:
            print("PG Error: %s" % e.pgerror)
            return 1

        try:
            cur.execute("""
                create table bot_users (chat_id integer
                NOT NULL PRIMARY KEY, username text);
            """)
        except:
            pass

        try:
            cur.execute("""
                create table bot_raid (type integer
                NOT NULL PRIMARY KEY, start timestamp with time zone);
            """)
        except:
            pass

        try:
            cur.execute("""alter table bot_raid add column period integer""")
        except:
            pass

        try:
            cur.execute("""
                create table bot_raid_stages (type integer references
                bot_raid(type), start integer, msg text, icon text,
                info text, PRIMARY KEY(type, start))
            """)

            cur.execute("""
                insert into bot_raid_stages values
                (1, 18*3600 + 30*60, 'Ранкор появился! Наносим 0 урона !!!',
                null, 'Запуск рейда')
            """)
            cur.execute("""
                insert into bot_raid_stages values
                (1, 24*3600 + 19*3600+45*60, 'Через 15 минут закрытие Ранкора,
                солисты закрывают в 20:10 !!!',
                'https://orig00.deviantart.net/94ba/f/2016/309/2/6/rancor_devours_gamorrean_guard__2_by_mgtowjabba-dane1vq.gif','Закрытие')
            """)

            cur.execute("""
                insert into bot_raid_stages values
                (2, 20*3600 + 30*60, 'ААТ обнаружен! Бьём Ф1 и Ф2!!!',
                'https://78.media.tumblr.com/8513f7d4550eb84ef9cf36c2e99fc15c/tumblr_nyt2y84irb1qb4meko1_400.gif', 'Запуск рейда (I и II фаза)')
            """)
            cur.execute("""
                insert into bot_raid_stages values
                (2, 24*3600 + 12*3600, 'Начинаем бить III фазу ААТ !!!',
                'http://pa1.narvii.com/6545/33737885d6f8ea4d2b4337d91772489226acee3f_hq.gif', 'Фаза III')
            """)
            cur.execute("""
                insert into bot_raid_stages values
                (2, 24*3600 + 20*3600+30*60, 'Добиваем ААТ. Все в атаку!!!',
                'http://i0.kym-cdn.com/photos/images/original/001/048/509/099.gif', 'Закрытие рейда')
            """)

            cur.execute("""
                insert into bot_raid_stages values
                (0, 15*3600, 'Не забываем про энку!!!', null, 'Напоминание')
            """)
            cur.execute("""
                insert into bot_raid_stages values
                (0, 17*3600, 'Не забываем про энку.
                Кто не сделает через 30 минут кик!!!',
                'https://media.tenor.com/images/98a43809f8b0052342fde3feed69a667/tenor.gif', 'Предупреждение')
            """)
        except:
            pass

    def connectToDataBase(self):
        print("ENV DATABASE_URL: %s" % os.environ['DATABASE_URL'])
        url = urlparse.urlparse(os.environ['DATABASE_URL'])
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port

        conn = None
    try:
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
    except psycopg2.Error as e:
        print("PG connect Error: %s" % e.pgerror)
    except:
        print("Unknown error whin PG connect!")
        return None

    print("connectToDataBase OK!")
    conn.autocommit = True
    return conn

    def addUser(self, user, chat_id):
        try:
            cur = self.conn.cursor()
            cur.execute("""
                INSERT INTO bot_users (chat_id,username)
                VALUES (%s,%s)
                """, (chat_id, user.username))
            self.users[chat_id] = user.username
            print("[storage]: new chat - %d added!" % chat_id)
        except psycopg2.Error as e:
            print("pg error when insert new user: %s" % e.pgerror)
