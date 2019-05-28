import asyncio
from enum import Enum

from aiogram import types
from aiopg.sa import create_engine
from sqlalchemy import (
    Table, Column, Integer, UnicodeText, BigInteger, MetaData
)
from sqlalchemy.ext.declarative import declarative_base
from config import DATABASE


class AdminType(Enum):
    SUPER = 0
    FULL = 1
    GROUP = 2


class MessageType(Enum):
    TEXT = 0
    VOICE = 1
    DOCUMENT = 2
    STICKER = 3
    CONTACT = 4
    VIDEO = 5
    VIDEO_NOTE = 6
    LOCATION = 7
    AUDIO = 8
    PHOTO = 9


metadata = MetaData()
local_triggers = Table('local_triggers', metadata,
                       Column('id', BigInteger, autoincrement=True, primary_key=True),
                       Column('chat_id', BigInteger, primary_key=True, default=0),
                       Column('trigger', UnicodeText(2500)),
                       Column('message', UnicodeText(2500)),
                       Column('message_type', Integer, default=0),
                       )


# Base = declarative_base()
#
# class LocalTrigger(Base):
#     __tablename__ = 'local_triggers'
#
#     id = Column(BigInteger, autoincrement=True, primary_key=True)
#     chat_id = Column(BigInteger, primary_key=True, default=0)
#     trigger = Column(UnicodeText(2500))
#     message = Column(UnicodeText(2500))
#     message_type = Column(Integer, default=0)
#
#
# class Trigger(Base):
#     __tablename__ = 'triggers'
#
#     id = Column(Integer, primary_key=True, autoincrement=True)
#     trigger = Column(UnicodeText(2500))
#     message = Column(UnicodeText(2500))
#     message_type = Column(Integer, default=0)
#
#
# class Admin(Base):
#     __tablename__ = 'admins'
#
#     id = Column(BigInteger, primary_key=True)
#     username = Column(UnicodeText(250))
#     admin_type = Column(Integer)
#     admin_group = Column(BigInteger, primary_key=True, default=0)


async def create_tables(engine):
    async with engine.acquire() as conn:
        await conn.execute('''CREATE TABLE IF NOT EXISTS local_triggers (
                                        id serial PRIMARY KEY,
                                        chat_id bigint,
                                        trigger varchar(255),
                                        message varchar(255),
                                        message_type smallint DEFAULT 0)''')

        await conn.execute('''CREATE TABLE IF NOT EXISTS triggers (
                                        id serial PRIMARY KEY,
                                        trigger varchar(255),
                                        message varchar(255),
                                        message_type smallint DEFAULT 0)''')

        await conn.execute('''CREATE TABLE IF NOT EXISTS admins (
                                        id serial PRIMARY KEY,
                                        username varchar(255),
                                        admin_type smallint DEFAULT 0,
                                        admin_group bigint DEFAULT 0)''')


loop = asyncio.get_event_loop()
engine = loop.run_until_complete(create_engine(user=DATABASE['user'],
                                               database=DATABASE['database'],
                                               password=DATABASE['password'],
                                               host=DATABASE['host'], loop=loop))

# create tables if dosn't exist
loop.run_until_complete(create_tables(engine=engine))
