from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.template import Template
<<<<<<< HEAD
from utils.messaging import Messaging
=======
from spade.message import Message
from utils.messaging import Messaging
from constants.agents import Agents
>>>>>>> origin/Franek
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

    class CreateAuthenticationAndPaymentBehav(FSMBehaviour):

        async def on_start(self):
            print(f"FSM starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"FSM finished at state {self.current_state}")
            await self.agent.stop()
    
    class AuthenticationState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            CLIENT = msg.sender
            print(f"Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_TWO")


    class ReservationCheckState(State):
        async def run(self):
            metadata = {"type": "ReservationCheck"}
            msg = Messaging.prepare_message(Agents.TIMETABLE, "", **metadata)
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_THREE")


    class ReservationResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_FOUR")

    class AuthenticationAnswerState(State):
        async def run(self):
            metadata = {"type": "AuthenticationAnswerCheck"}
            msg = Messaging.prepare_message("client1@localhost", "", **metadata)
            
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_FIVE")
    
    class PaymentInitialState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_SIX")

    class PaymentAnswerState(State):
        async def run(self):
            metadata = {"type": "PaymentAnswerCheck"}
            msg = Messaging.prepare_message("client1@localhost", "", **metadata)
            
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_SEVEN")

    class GrantWashingMachineAccessState(State):
        async def run(self):
            metadata = {"type": "GrantAccess"}
            msg = Messaging.prepare_message("washingmachine1@localhost", "", **metadata)
            
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_EIGHT")
    
    class GrantAccessResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")

    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserPenaltiesVerification")
        vu_behav = self.VerifyUserBehav()
        #self.add_behaviour(vu_behav, verify_msg_template)
        fsm = self.CreateAuthenticationAndPaymentBehav()
        fsm.add_state(name="STATE_ONE", state=self.AuthenticationState(), initial=True)
        fsm.add_state(name="STATE_TWO", state=self.ReservationCheckState())
        fsm.add_state(name="STATE_THREE", state=self.ReservationResponseState())
        fsm.add_state(name="STATE_FOUR", state=self.AuthenticationAnswerState())
        fsm.add_state(name="STATE_FIVE", state=self.PaymentInitialState())
        fsm.add_state(name="STATE_SIX", state=self.PaymentAnswerState())
        fsm.add_state(name="STATE_SEVEN", state=self.GrantWashingMachineAccessState())
        fsm.add_state(name="STATE_EIGHT", state=self.GrantAccessResponseState())
        fsm.add_transition(source="STATE_ONE", dest="STATE_TWO")
        fsm.add_transition(source="STATE_TWO", dest="STATE_THREE")
        fsm.add_transition(source="STATE_THREE", dest="STATE_FOUR")
        fsm.add_transition(source="STATE_FOUR", dest="STATE_FIVE")
        fsm.add_transition(source="STATE_FIVE", dest="STATE_SIX")
        fsm.add_transition(source="STATE_SIX", dest="STATE_SEVEN")
        fsm.add_transition(source="STATE_SEVEN", dest="STATE_EIGHT")
        self.add_behaviour(fsm)

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