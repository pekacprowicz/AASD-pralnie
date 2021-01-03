import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, FSMBehaviour, State
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

    class CreateAuthenticationAndPaymentBehav(FSMBehaviour):

        async def on_start(self):
            print(f"Client fsm starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"Client fsm finished at state {self.current_state}")
            await self.agent.stop()
    
    class AuthenticationState(State):
        async def run(self):
            metadata = {"type": "UserAuthentication"}
            msg = Messaging.prepare_message(Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_TWO")


    class AuthenticationResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_THREE")


    class PaymentInitialState(State):
        async def run(self):
            metadata = {"type": "UserPaymentInitial"}
            msg = Messaging.prepare_message(Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print("Message sent!")
            self.set_next_state("STATE_FOUR")

    class PaymentResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_FIVE")
    
    class MachineAvailableState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"Incoming msg_type: {msg_type}")

    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        self.dates_priority_list = list()
        self.create_res_behav = self.CreateReservationBehav(self.dates_priority_list)
        #self.add_behaviour(self.create_res_behav)
        fsm = self.CreateAuthenticationAndPaymentBehav()
        fsm.add_state(name="STATE_ONE", state=self.AuthenticationState(), initial=True)
        fsm.add_state(name="STATE_TWO", state=self.AuthenticationResponseState())
        fsm.add_state(name="STATE_THREE", state=self.PaymentInitialState())
        fsm.add_state(name="STATE_FOUR", state=self.PaymentResponseState())
        fsm.add_state(name="STATE_FIVE", state=self.MachineAvailableState())
        fsm.add_transition(source="STATE_ONE", dest="STATE_TWO")
        fsm.add_transition(source="STATE_TWO", dest="STATE_THREE")
        fsm.add_transition(source="STATE_THREE", dest="STATE_FOUR")
        fsm.add_transition(source="STATE_FOUR", dest="STATE_FIVE")
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
        return f"db/db_{self.name}.db"

    def db_init(self):
        sql_create_prorities_table = """ CREATE TABLE IF NOT EXISTS prorities (
                                            id integer PRIMARY KEY,
                                            datetime text NOT NULL,
                                            prority integer NOT NULL
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_prorities_table)