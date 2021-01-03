from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
from utils.messaging import Messaging
import pathlib
import sqlite3

class Supervisor(Agent):

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
        verify_msg_template.set_metadata("type", "UserPenaltiesVerification")
        vu_behav = self.VerifyUserBehav()
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

    def search_for_active_penalties(self, username):
        sql_get_user_penalties = f""" SELECT COUNT(end_date) FROM penalties as p
                                        WHERE p.user = \"{username}\"
                                        AND datetime(p.end_date) > datetime('now');
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_penalties_table)
        active_penalties = int(crsr.fetchall())

        return active_penalties