import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour
from constants.agents import Agents
from spade.message import Message
from utils.messaging import Messaging
import sqlite3
import pathlib

class Client(Agent):
    
    class CreateReservationBehav(OneShotBehaviour):

        def __init__(self, dates_list):
            super().__init__()
            self.dates_list = dates_list

        async def run(self):
            # dates_list = self.dates_priority_list.copy()
            metadata = {"type": "UserVerification"}
            msg = Messaging.prepare_message(Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print("Message sent!")

            self.exit_code = "Finished"

            await self.agent.stop()

    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        self.dates_priority_list = list()
        self.create_res_behav = self.CreateReservationBehav(self.dates_priority_list)
        self.add_behaviour(self.create_res_behav)

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
        sql_create_prorities_table = """ CREATE TABLE IF NOT EXISTS prorities (
                                            id integer PRIMARY KEY,
                                            datetime text NOT NULL,
                                            prority integer NOT NULL
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_prorities_table)