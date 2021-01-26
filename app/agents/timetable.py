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

class Timetable(Agent):
    
    class VerifyUserBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                username = msg.sender.localpart
                metadata = {"performative": "UserPenaltiesVerificationResponse"}

                if self.search_for_active_penalties(username) > 0:
                    metadata["status"] = "rejected"
                else:
                    metadata["status"] = "accepted"
                
                response = Messaging.prepare_message(Agents.TIMETABLE, msg.sender, "", **metadata)
                await self.send(response)
            else:
                print(f"Supervisor's VerifyUser Behaviour hasn't received any message")

    class UserCameBehav(OneShotBehaviour):
        userCame = False

        async def run(self):
            
            self.userCame = self.check_if_user_came()
            
            if not self.userCame:
               
                print(f"[{self.agent.jid.localpart}] UserCameBehav running")
                
                metadata = {"performative": Performatives.INFORM_USER_ABSENCE}
                msg = Messaging.prepare_message(Agents.TIMETABLE, Agents.SUPERVISOR, "", **metadata)
                
    
                await self.send(msg)
                print(f"[{self.agent.jid.localpart}] Message sent!")

            # stop agent from behaviour
            await self.agent.stop()
            
        def check_if_user_came(self):
            userCame= random.choice([True, False])
            #  print (userCame)
    
            return False

    async def setup(self):
        print ("Timetable started")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        verify_msg_template = Template()
        verify_msg_template.set_metadata("performative", "UserPenaltiesVerificationResponse")
        vu_behav = self.VerifyUserBehav()
        #self.add_behaviour(vu_behav, verify_msg_template)

        b = self.UserCameBehav()
        self.add_behaviour(b)
        

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
        return f"db/db_{self.name}.db"

    def db_init(self):
        sql_create_prorities_table = """ CREATE TABLE IF NOT EXISTS priorities (
                                            id integer PRIMARY KEY,
                                            date text NOT NULL,
                                            washing_mashine integer NOT NULL,
                                            user text NOT NULL
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_prorities_table)

    def get_dates_with_priority(self):
        sql_get_user_penalties = f" SELECT * FROM priorities; "

        crsr = self.db_connection.cursor()
        crsr.execute(sql_get_user_penalties)
        sql_get_user_penalties = crsr.fetchall()
        return sql_get_user_penalties