import asyncio
import time
from spade.agent import Agent
from spade.behaviour import OneShotBehaviour, FSMBehaviour, State, CyclicBehaviour
from constants.agents import Agents
from constants.performatives import Performatives
from spade.message import Message
from utils.messaging import Messaging
from spade.template import Template

import sqlite3
import pathlib

class Client(Agent):
     
    class ClientBehav(CyclicBehaviour):
        # index = 0
        wantToMakeReservation = True
        wantToAuthenticate = False

        async def run(self):
            if self.wantToMakeReservation:
                self.wantToMakeReservation = False
                time.sleep(1)
                print(f"[{self.agent.jid.localpart}] Making Reservation")
                await self.send(self.send_penalties_verification_mesage())

            elif self.wantToAuthenticate:
                self.wantToAuthenticate = False
                print(f"[{self.agent.jid.localpart}] Starting Authentication")
                await self.send(self.send_authentication_message())

            else:
                msg = await self.receive(timeout=10)
                if msg:
                    msg_performative = msg.get_metadata("performative")
                    print(f"[{self.agent.jid.localpart}] Incoming msg_performative: {msg_performative}")

                    if msg_performative == Performatives.USER_PENALTIES_VERIFICATION_ACCEPTED:
                        print(f"[{self.agent.jid.localpart}] Sending date proposals")
                        await self.send(self.send_date_proposal())

                    elif msg_performative == Performatives.USER_PENALTIES_VERIFICATION_REJECTED:
                        print(f"[{self.agent.jid.localpart}] User cannot reserve machine due penalties")

                    elif msg_performative == Performatives.DATE_ACCEPTED:
                        print(f"[{self.agent.jid.localpart}] Date accepted")

                    elif msg_performative == Performatives.DATE_REJECTED:
                        print(f"[{self.agent.jid.localpart}] Date rejected")

                        # TODO proponowanie kolejnych dat / kontrolowanie wiadomości klienta z terminala i podawanie ręcznie daty

                        # jak zrobi się tworzenie tej klasy z listą, to tę listę trzeba wstawić w środek len()
                        if self.index < 3:# len(self.get_dates_with_priority()):
                            print(f"[{self.agent.jid.localpart}] Trying another date")
                            await self.send(self.send_date_proposal())
                        else:
                            print(f"[{self.agent.jid.localpart}] No date from the list is available, try later")

                    elif msg_performative == Performatives.USER_AUTHENTICATION_ACCEPTED:
                        print(f"[{self.agent.jid.localpart}] Authentication Accepted")
                        print(f"[{self.agent.jid.localpart}] Payment Initializing")
                        await self.send(self.send_payment_initialize_message())

                    elif msg_performative == Performatives.USER_AUTHENTICATION_REJECTED:
                        print(f"[{self.agent.jid.localpart}] Authentication Rejected")

                    elif msg_performative == Performatives.USER_PAYMENT_ACCEPTED:
                        print(f"[{self.agent.jid.localpart}] Payment Accepted")
                        print(f"[{self.agent.jid.localpart}] Waiting for access to washing machine")

                    elif msg_performative == Performatives.USER_PAYMENT_REJECTED:
                        print(f"[{self.agent.jid.localpart}] Payment Rejected")
                        #TODO co gdy odrzucona płatność?

                    elif msg_performative == Performatives.CONFIRM_ACCESS_GRANTED:
                        print(f"[{self.agent.jid.localpart}] Access to washing machine grated")

                    elif msg_performative == Performatives.ABSENCES:
                        print(f"[{self.agent.jid.localpart}] Received information about 3 absences")

                else:
                    print(f"[{self.agent.jid.localpart}] didn't receive a message!") 

        def send_authentication_message(self):
            metadata = {"performative": Performatives.REQUEST_USER_AUTHENTICATION}
            return Messaging.prepare_message(f"{self.agent.jid}", Agents.SUPERVISOR, "", **metadata)

        def send_payment_initialize_message(self):
            metadata = {"performative": Performatives.USER_PAYMENT_INITIAL}
            return Messaging.prepare_message(f"{self.agent.jid}", Agents.SUPERVISOR, "", **metadata)

        def send_penalties_verification_mesage(self):
            metadata = {"performative": Performatives.USER_PENALTIES_VERIFICATION}
            return Messaging.prepare_message(f"{self.agent.jid}", Agents.SUPERVISOR, "", **metadata)

        def send_date_proposal(self):
            #TODO trzeba to jakoś poprawić, bo na razie nie umiem odwołać się do tej funkcji zpoza behav
            #possible_dates = get_dates_with_priority()
            #self.index = self.index + 1
            #TODO jak uda się to poprawić to powinno też zadziałać
            #return Messaging.prepare_message(Agents.CLIENT, Agents.TIMETABLE, possible_dates[index], **metadata)
            metadata = {"performative": Performatives.PROPOSE_DATETIME,
                        "proposed_datetime": self.agent.datetime}
            return Messaging.prepare_message(f"{self.agent.jid}", Agents.TIMETABLE, "", **metadata)

    async def setup(self):
        print (f"[{self.jid.localpart}] started!")
        # self.db_connection = self.connect_to_local_db()
        # self.db_init()
    
        cli_behav = self.ClientBehav()

        # self.dates_priority_list = list()
        #TODO ClientBehav nie ma obsługi utworzonej listy, trzeba to jakoś dodać
        #cli_behav = self.ClientBehav(self.dates_priority_list)

        self.datetime = "30.01.2020 10:00"

        self.add_behaviour(cli_behav)
        time.sleep(1)



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

    #def init_create_client_behaviour(self):
        #verify_msg_template = Template()
        #verify_msg_template.set_metadata("performative", "UserPenaltiesVerificationResponse")
        # verify_msg_template.set_metadata("performative", "UserPenaltiesVerificationResponse")
    #    cli_behav = self.ClientBehav()
    #    self.add_behaviour(cli_behav)
            
    #class PenaltyNotificationBehav(CyclicBehaviour):
        
    #    async def run(self):
    #        print(f"[{self.agent.jid.localpart}] PenaltyNotificationBehav running")

    #        msg = await self.receive(timeout=10) # wait for a message for 10 seconds
    #        if msg:
    #            print(f"[{self.agent.jid.localpart}] Message received with content: {format(msg.body)}")
    #            print(f"[{self.agent.jid.localpart}] Message received with performative: {format(msg.get_metadata('performative'))}")
    #        else:
    #            print(f"[{self.agent.jid.localpart}] Did not received any message after 10 seconds")

            # stop agent from behaviour
    #        await self.agent.stop()
            
