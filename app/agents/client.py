import asyncio
from spade.agent import Agent
from spade.behaviour import FSMBehaviour, State
from constants.agents import Agents
from spade.message import Message
from utils.messaging import Messaging
import sqlite3
import pathlib

class Client(Agent):
    
    class CreateReservationBehav(FSMBehaviour):
        async def on_start(self):
            print(f"Client CreateReservationBehav starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"Client CreateReservationBehav finished at state {self.current_state}")
            await self.agent.stop()

    class UserPenaltiesVerificationState(State):
        async def run(self):
            metadata = {"type": "UserPenaltiesVerification"}
            msg = Messaging.prepare_message(Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print("Message sent!")

            self.set_next_state("SendDateProposal")

    class SendDateProposalState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                response_status = msg.get_metadata("status")

                if response_status == "accepted":
                    possible_dates = self.get_dates_with_priority()
                    metadata = {"type": "DatetimeProposal"}
                    
                    for date in possible_dates:
                        msg = Messaging.prepare_message(Agents.TIMETABLE, date, **metadata)
                        print(f"Sending message")
                        await self.send(msg)
                        self.set_next_state("DateProposalResponse")

                else:
                    self.exit_code("User cannot reserve machine due penalties")
                    await self.agent.stop()

            else:
                print(f"Client's {self.name} VerifyUser Behaviour hasn't received any message")

    class DateProposalResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                response_status = msg.get_metadata("status")

                possible_dates = self.get_dates_with_priority()
                metadata = {"type": "DatetimeProposal"}
                
                for date in possible_dates:
                    msg = Messaging.prepare_message(Agents.TIMETABLE, date, **metadata)
                    print(f"Sending message")
                    await self.send(msg)

            else:
                print(f"Client's {self.name} VerifyUser Behaviour hasn't received any message")

    def init_create_reservation_behaviour(self):
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        # verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        vu_behav = self.VerifyUserBehav()
        fsm = self.CreateReservationBehav()
        fsm.add_state(name="UserPenaltiesVerificationState", state=self.UserPenaltiesVerificationState(), initial=True)
        fsm.add_state(name="SendDateProposal", state=self.SendDateProposalState())
        fsm.add_state(name="DateProposalResponse", state=self.DateProposalResponseState())
        fsm.add_state(name="STATE_FOUR", state=self.PaymentResponseState())
        fsm.add_state(name="STATE_FIVE", state=self.MachineAvailableState())
        fsm.add_transition(source="STATE_ONE", dest="STATE_TWO")
        fsm.add_transition(source="STATE_TWO", dest="STATE_THREE")
        fsm.add_transition(source="STATE_THREE", dest="STATE_FOUR")
        fsm.add_transition(source="STATE_FOUR", dest="STATE_FIVE")
        self.add_behaviour(fsm)

    async def setup(self):
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        self.create_res_behav = self.CreateReservationBehav()
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
        sql_create_prorities_table = """ CREATE TABLE IF NOT EXISTS priorities (
                                            id integer PRIMARY KEY,
                                            prefered_date text NOT NULL,
                                            priority integer NOT NULL
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_prorities_table)

    def get_dates_with_priority(self):
        sql_get_user_penalties = f" SELECT * FROM priorities; "

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_penalties_table)
        dates_with_priorities = crsr.fetchall()

        return dates_with_priorities