from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import pathlib
import sqlite3

class Supervisor(Agent):

    class VerifyUser(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_type = msg.get_metadata("type")
                print(f"Incoming msg_type: {msg_type}")
            else:
                print(f"No message...")


    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserVerification")
        vu_behav = self.VerifyUser()
        self.add_behaviour(vu_behav, verify_msg_template)

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
        return f"db/db_supervisor.db"

    def db_init(self):
        sql_create_penalties_table = """ CREATE TABLE IF NOT EXISTS penalties (
                                            id integer PRIMARY KEY,
                                            user text NOT NULL,
                                            type text NOT NULL,
                                            end_date text NOT NULL
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_penalties_table)