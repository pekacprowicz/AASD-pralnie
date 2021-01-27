import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from constants.agents import Agents
from constants.performatives import Performatives
from spade.message import Message
from utils.messaging import Messaging
from spade.template import Template
import sqlite3
import pathlib
import random
import time
import numpy as np
import datetime
from json import dumps

class Timetable(Agent):
    
    class TimetableBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_performative = msg.get_metadata("performative")
                print(f"[{self.agent.jid.localpart}] Incoming msg_performative: {msg_performative}")

                if msg_performative == Performatives.PROPOSE_DATETIME:

                    # TODO walidacja daty

                    if True:
                        metadata = {"performative": Performatives.DATE_ACCEPTED}
                        response = Messaging.prepare_message(Agents.TIMETABLE, str(msg.sender), "", **metadata)
                        await self.send(response)

                    else:
                        metadata = {"performative": Performatives.DATE_REJECTED}
                        response = Messaging.prepare_message(Agents.TIMETABLE, str(msg.sender), "", **metadata)
                        await self.send(response)

                elif msg_performative == Performatives.RESERVATION_CHECK:

                    # TODO walidacja rezerwacji
                    client = msg.get_metadata("client")

                    if True:
                        metadata = {"performative": Performatives.RESERVATION_CHECK_RESPONSE_ACCEPTED,
                                    "client": client}
                        response = Messaging.prepare_message(Agents.TIMETABLE, str(msg.sender), "", **metadata)
                        await self.send(response)

                    else:
                        metadata = {"performative": Performatives.RESERVATION_CHECK_RESPONSE_REJECTED,
                                    "client": client}
                        response = Messaging.prepare_message(Agents.TIMETABLE, str(msg.sender), "", **metadata)
                        await self.send(response)

            else:
                print(f"[{self.agent.jid.localpart}] Didn't receive a message!") 

    async def setup(self):
        print (f"[{self.jid.localpart}] started!")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        #verify_msg_template = Template()
        #verify_msg_template.set_metadata("performative")
        #vu_behav = self.VerifyUserBehav()
        #self.add_behaviour(vu_behav, verify_msg_template)

        timet_behav = self.TimetableBehav()
        self.add_behaviour(timet_behav)
        time.sleep(1)
            

    def connect_to_local_db(self):
        connection = None
        db_path = pathlib.Path.cwd() / 'db'
        db_path.mkdir(parents=True, exist_ok=True)
        try:
            connection = sqlite3.connect(self.get_local_db_path())
        except sqlite3.Error as e:
            print("Error while connecting to sqlite db")
        
        return connection

    def get_local_db_path(self):
        return "db/db_timetable.db"

    def db_init(self):
        sql_create_prorities_table = """ CREATE TABLE IF NOT EXISTS priorities (
                                            id integer PRIMARY KEY,
                                            date text NOT NULL,
                                            washing_mashine integer NOT NULL,
                                            user text NOT NULL
                                    ); """
    
        sql_create_timatable_table = """ CREATE TABLE IF NOT EXISTS timetable (
                                        	id INTEGER NOT NULL,
                                        	date	TEXT NOT NULL,
                                        	washing_machine	 TEXT NOT NULL,
                                        	client	INTEGER,
                                        	user_came	INTEGER,
                                        	PRIMARY KEY("id" AUTOINCREMENT)
                                        ); """
    
        
        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_prorities_table)
        crsr.execute(sql_create_timatable_table)
        

    def get_dates_with_priority(self):
        sql_get_user_penalties = f" SELECT * FROM priorities; "

        crsr = self.db_connection.cursor()
        crsr.execute(sql_get_user_penalties)
        sql_get_user_penalties = crsr.fetchall()
        return sql_get_user_penalties
    
    
    def check_absences(self):
        next_date = datetime.date.today()-datetime.timedelta(days=1)
        next_date = '2021-01-25 00:00:00'
        
        sql_chceck_absences = f""" SELECT date, client from timetable where 
                                    date(date) = date('{next_date}') and 
                                    user_came is null and client is not null"""
        
        try:
            crsr = self.db_connection.cursor()
            crsr.execute(sql_chceck_absences)
            sql_chceck_absences = crsr.fetchall()
        except Exception as e:
            print(e) 
        
        absences = dict()
        key = 0
        for client in sql_chceck_absences:
            absences[key] = client
            key+=1
            
        print (absences)
        
        return absences
    
    
    
    def add_test_data(self):
         crsr = self.db_connection.cursor()
        
         sql_add_new_dates = """ UPDATE timetable SET client = 'client1' where 
                                 washing_machine = '1'  and 
                                 date = '2021-01-25 10:00:00'; """
         try:
            crsr.execute(sql_add_new_dates)
            self.db_connection.commit()
            
         except Exception as e:
            print(e)

# =============================================================================
#     
# Dodaje nowy dzien do kalendarza  (lub więcej dni do testowania)
# 
# =============================================================================
    def add_new_dates(self):
                
                
        slots = [0, 2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22]
        aaa = list()
        
        
        #add 7 days do calendar
        for i in range(-2, 7):
            aaa.append(datetime.datetime.today()+datetime.timedelta(days=i))
        
        
        next_date = datetime.datetime.today()+datetime.timedelta(days=7)
        dates_list = list()
        
        for next_date in aaa:
            for i in slots:
                date = datetime.datetime(next_date.year ,next_date.month , next_date.day, i)
                dates_list.append(str(date))
            
        
        washing_machines = ["1", "2"]
        crsr = self.db_connection.cursor()
        
        
        for w in washing_machines:
            for date in dates_list:
                sql_add_new_dates = f""" INSERT INTO timetable (date, washing_machine)
                                    values('{date}' , '{w}'); """
                try:
                    crsr.execute(sql_add_new_dates)
                    self.db_connection.commit()
                    
                except Exception as e:
                    print(e)
                                            
            
    
    
    
# =============================================================================
#     
#    Do testów - usuwa wszysko z kalendarza i pokazuje co jest w kalendarzu    
#
# =============================================================================
    def delete_from_timetable(self):
         sql_delete_from_absences = """ DELETE FROM timetable;"""
                    
                    
         try:
            crsr = self.db_connection.cursor()
            crsr.execute(sql_delete_from_absences)
            self.db_connection.commit()
            
         except Exception as e:
            print(e)
        
        
    def select_timetable(self):
         select_from_timetable = """ SELECT * FROM timetable;"""
                    
                    
         try:
            crsr = self.db_connection.cursor()
            crsr.execute(select_from_timetable)
            select_from_timetable = crsr.fetchall()
            self.db_connection.commit()
            
            print (select_from_timetable)
            
            
         except Exception as e:
            print(e)
        

    #class VerifyUserBehav(CyclicBehaviour):
    #    async def run(self):
    #        msg = await self.receive(timeout=10)
    #        if msg:
    #            username = msg.sender.localpart
    #            metadata = {"performative": "UserPenaltiesVerificationResponse"}

    #            if self.search_for_active_penalties(username) > 0:
    #                metadata["status"] = "rejected"
    #            else:
    #                metadata["status"] = "accepted"
                
    #            response = Messaging.prepare_message(Agents.TIMETABLE, msg.sender, "", **metadata)
    #            await self.send(response)
    #        else:
    #            print(f"Supervisor's VerifyUser Behaviour hasn't received any message")

    #class UserCameBehav(OneShotBehaviour):
    #    userCame = False

    #    async def run(self):
            
    #        self.userCame = self.check_if_user_came()
            
            #self.agent.add_new_dates()
            #self.agent.delete_from_timetable()
            #self.agent.select_timetable()
            #self.agent.add_test_data()
            
    #        absences = self.agent.check_absences()
            
    #        if not self.userCame:
               
    #            print(f"[{self.agent.jid.localpart}] UserCameBehav running")
                
    #            metadata = {"performative": Performatives.INFORM_USER_ABSENCE}
    #            msg = Messaging.prepare_message(Agents.TIMETABLE, Agents.SUPERVISOR, "", **metadata)

                
    
    #            await self.send(msg)
    #            print(f"[{self.agent.jid.localpart}] Message sent!")

            # stop agent from behaviour
    #        await self.agent.stop()
            
    #    def check_if_user_came(self):
    #        userCame= random.choice([True, False])
            #  print (userCame)
    
    #        return False
        
                
        