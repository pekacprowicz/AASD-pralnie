from spade.agent import Agent
from spade.behaviour import CyclicBehaviour
from spade.template import Template
import pathlib
import sqlite3
import random
from utils.messaging import Messaging 

class Supervisor(Agent):

    class VerifyUser(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_type = msg.get_metadata("type")
                print(f"Incoming msg_type: {msg_type}")
            else:
                print(f"No message...")
                
    class CountAbsencesBehav(CyclicBehaviour):
        absences = 0
        
        async def run(self):
            print("CountAbsencesBehav running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                msg_type = msg.get_metadata("type")
                if msg_type == "UserAbsence":
                    print("Message received with content: {}".format(msg_type))
                    self.absences = self.countAbsences()
                    if self.absences == 3:
                        
                        metadata = {"type": "3 Absences"}
                        msg = Messaging.prepare_message("client@localhost", "", **metadata)
                                           # Set the message content
                        await self.send(msg)
                    
                    
            else:
                print("Did not received any message after 10 seconds")

            # stop agent from behaviour
            
           
                
            await self.agent.stop()
            
        def countAbsences(self):
            #check in db
            absences = random.choice([0, 3])
            #  print (absences)
    
            return 3


    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserVerification")
        vu_behav = self.VerifyUser()
        self.add_behaviour(vu_behav, verify_msg_template)
        
        absences_behav = self.CountAbsencesBehav()
        absences_msg_template = Template()
        absences_msg_template.set_metadata("type", "UserAbsence")
        self.add_behaviour(absences_behav, absences_msg_template)

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