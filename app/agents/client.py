import asyncio
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, FSMBehaviour, State, CyclicBehaviour
from constants.agents import Agents
from spade.message import Message
from utils.messaging import Messaging
from spade.template import Template

import sqlite3
import pathlib

class Client(Agent):
    
    class ClientBehav(CyclicBehaviour):
        index = 0
        wantToMakeReservation = True
        wantToAuthenticate = True
        async def run(self):
            if self.wantToMakeReservation:
                self.wantToMakeReservation = False
                print(f"[{self.agent.jid.localpart}] Making Reservation")
                await self.send(self.send_penalties_verification_mesage())
            elif self.wantToAuthenticate:
                self.wantToAuthenticate = False
                print(f"[{self.agent.jid.localpart}] Starting Authentication")
                await self.send(self.send_authentication_message())
            else:
                msg = await self.receive(timeout=10)
                if msg:
                    msg_type = msg.get_metadata("type")
                    print(f"[{self.agent.jid.localpart}] Incoming msg_type: {msg_type}")
                    if msg_type == "UserPenaltiesVerificationAccepted":
                        print(f"[{self.agent.jid.localpart}] Sending date proposals")
                        await self.send(self.send_date_proposal())
                    elif msg_type == "UserPenaltiesVerificationRejected":
                        print(f"[{self.agent.jid.localpart}] User cannot reserve machine due penalties")
                    elif msg_type == "DateAcceptred":
                        print(f"[{self.agent.jid.localpart}] Date accepted")
                    elif msg_type == "DateRejected":
                        print(f"[{self.agent.jid.localpart}] Date rejected")
                        #TODO jak zrobi się tworzenie tej klasy z listą, to tę listę trzeba wstawić w środek len()
                        if self.index < 3:# len(self.get_dates_with_priority()):
                            print(f"[{self.agent.jid.localpart}] Trying another date")
                            await self.send(self.send_date_proposal())
                        else:
                            print(f"[{self.agent.jid.localpart}] No date from the list is available, try later")
                    elif msg_type == "UserAuthenticationAccepted":
                        print(f"[{self.agent.jid.localpart}] Authentication Accepted")
                        print(f"[{self.agent.jid.localpart}] Payment Initializing")
                        await self.send(self.send_payment_initialize_message())
                    elif msg_type == "UserAuthenticationRejected":
                        print(f"[{self.agent.jid.localpart}] Authentication Rejected")
                    elif msg_type == "UserPaymentAccepted":
                        print(f"[{self.agent.jid.localpart}] Payment Accepted")
                        print(f"[{self.agent.jid.localpart}] Waiting for access to washing machine")
                    elif msg_type == "UserPaymentRejected":
                        print(f"[{self.agent.jid.localpart}] Payment Rejected")
                        #TODO co gdy odrzucona płatność?
                    elif msg_type == "AccessGranted":
                        print(f"[{self.agent.jid.localpart}] Access to washing machine grated")
                else:
                    print(f"[{self.agent.jid.localpart}] Didn't receive a message!") 

        def send_authentication_message(self):
            metadata = {"type": "UserAuthentication"}
            return Messaging.prepare_message(Agents.CLIENT, Agents.SUPERVISOR, "", **metadata)
        def send_payment_initialize_message(self):
            metadata = {"type": "UserPaymentInitial"}
            return Messaging.prepare_message(Agents.CLIENT, Agents.SUPERVISOR, "", **metadata)
        def send_penalties_verification_mesage(self):
            metadata = {"type": "UserPenaltiesVerification"}
            return Messaging.prepare_message(Agents.CLIENT, Agents.SUPERVISOR, "", **metadata)
        def send_date_proposal(self):
            #TODO trzeba to jakoś poprawić, bo na razie nie umiem odwołać się do tej funkcji zpoza behav
            #possible_dates = get_dates_with_priority()
            metadata = {"type": "DatetimeProposal"}
            self.index = self.index + 1
            #TODO jak uda się to poprawić to powinno też zadziałać
            #return Messaging.prepare_message(Agents.CLIENT, Agents.TIMETABLE, possible_dates[index], **metadata)
            return Messaging.prepare_message(Agents.CLIENT, Agents.TIMETABLE, "", **metadata)

    #def init_create_client_behaviour(self):
        #verify_msg_template = Template()
        #verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        # verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
    #    cli_behav = self.ClientBehav()
    #    self.add_behaviour(cli_behav)
            
    #class PenaltyNotificationBehav(CyclicBehaviour):
        
    #    async def run(self):
    #        print(f"[{self.agent.jid.localpart}] PenaltyNotificationBehav running")

    #        msg = await self.receive(timeout=10) # wait for a message for 10 seconds
    #        if msg:
    #            print(f"[{self.agent.jid.localpart}] Message received with content: {format(msg.body)}")
    #            print(f"[{self.agent.jid.localpart}] Message received with type: {format(msg.get_metadata('type'))}")
    #        else:
    #            print(f"[{self.agent.jid.localpart}] Did not received any message after 10 seconds")

            # stop agent from behaviour
    #        await self.agent.stop()
            

    async def setup(self):
        print ("Client started")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        
        self.dates_priority_list = list()
        #TODO ClientBehav nie ma obsługi utworzonej listy, trzeba to jakoś dodać
        cli_behav = self.ClientBehav()
        #cli_behav = self.ClientBehav(self.dates_priority_list)
        self.add_behaviour(cli_behav)
        
        

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
        crsr.execute(sql_get_user_penalties)
        dates_with_priorities = crsr.fetchall()

        return dates_with_priorities