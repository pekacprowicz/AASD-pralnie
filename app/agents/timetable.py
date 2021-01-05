import asyncio
from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from constants.agents import Agents
from spade.message import Message
from utils.messaging import Messaging
import sqlite3
import pathlib

class Timetable(Agent):
    
    class VerifyUserBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                username = msg.sender.localpart
                metadata = {"type": "UserPenaltiesVerificationResponse"}

                if self.search_for_active_penalties(username) > 0:
                    metadata["status"] = "rejected"
                else:
                    metadata["status"] = "accepted"
                
                response = Messaging.prepare_message(msg.sender, "", **metadata)
                await self.send(response)
            else:
                print(f"Supervisor's VerifyUser Behaviour hasn't received any message")

    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        vu_behav = self.VerifyUserBehav()
        #self.add_behaviour(vu_behav, verify_msg_template)

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
        crsr.execute(sql_create_penalties_table)
        dates_with_priorities = crsr.fetchall()

        return dates_with_priorities