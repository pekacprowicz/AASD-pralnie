#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Jan 25 18:01:27 2021

@author: nataliaszakiel
"""

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
    
    
    
    
    class NewBehav(CyclicBehaviour):
        async def run(self):
            print(f"[{self.agent.jid.localpart}] PenaltyNotificationBehav running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                msg_type = msg.get_metadata("type")
                if msg_type == "3 Absences":
                    print(f"[{self.agent.jid.localpart}] Message received with type: {format(msg.get_metadata('type'))}")
                
                if msg_type == "AuthenticationAnswerCheck":
                    print(f"[{self.agent.jid.localpart}] Message received with type: {format(msg.get_metadata('type'))}")
                
                if msg_type == "PaymentAnswerCheck":
                    print(f"[{self.agent.jid.localpart}] Message received with type: {format(msg.get_metadata('type'))}")

           
            else:
                print(f"[{self.agent.jid.localpart}] Did not received any message after 10 seconds")
    
   
    
   
    
   
    
   
    class CreateReservationBehav(FSMBehaviour):
        
        
        
        
        async def on_start(self):
            print(f"[{self.agent.jid.localpart}] Client CreateReservationBehav starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"[{self.agent.jid.localpart}] Client CreateReservationBehav finished at state {self.current_state}")
            await self.agent.stop()

    class UserPenaltiesVerificationState(State):
        async def run(self):
            metadata = {"type": "UserPenaltiesVerification"}
            msg = Messaging.prepare_message(Agents.CLIENT, Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print(f"[{self.agent.jid.localpart}] Message sent!")

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
                        msg = Messaging.prepare_message(Agents.CLIENT, Agents.TIMETABLE, date, **metadata)
                        print(f"Sending message")
                        await self.send(msg)
                        self.set_next_state("DateProposalResponse")

                else:
                    self.exit_code("User cannot reserve machine due penalties")
                    await self.agent.stop()

            else:
                print(f"[{self.agent.jid.localpart}] Client's {self.name} SendDateProposal State hasn't received any message")

    class DateProposalResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                response_status = msg.get_metadata("status")

                possible_dates = self.get_dates_with_priority()
                metadata = {"type": "DatetimeProposal"}
                
                for date in possible_dates:
                    msg = Messaging.prepare_message(Agents.CLIENT, Agents.TIMETABLE, date, **metadata)
                    print(f"[{self.agent.jid.localpart}] Sending message")
                    await self.send(msg)

            else:
                print(f"[{self.agent.jid.localpart}] Client's {self.name} SendDateProposal State hasn't received any message")

    class DateAcceptedState(State):
        async def run(self):
            print(f"[{self.agent.jid.localpart}] Date accepted")

    class DateAcceptedState(State):
        async def run(self):
            print(f"[{self.agent.jid.localpart}] Date rejected")

    def init_create_reservation_behaviour(self):
        verify_msg_template = Template()
        verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        # verify_msg_template.set_metadata("type", "UserPenaltiesVerificationResponse")
        vu_behav = self.VerifyUserBehav()
        fsm = self.CreateReservationBehav()
        fsm.add_state(name="UserPenaltiesVerificationState", state=self.UserPenaltiesVerificationState(), initial=True)
        fsm.add_state(name="SendDateProposal", state=self.SendDateProposalState())
        fsm.add_state(name="DateProposalResponse", state=self.DateProposalResponseState())
        fsm.add_state(name="DateAccepted", state=self.DateAcceptedState())
        fsm.add_state(name="DateRejected", state=self.DateRejectedState())
        fsm.add_transition(source="UserPenaltiesVerificationState", dest="SendDateProposal")
        fsm.add_transition(source="UserPenaltiesVerificationState", dest="DateRejected")
        fsm.add_transition(source="SendDateProposal", dest="DateProposalResponse")
        fsm.add_transition(source="DateProposalResponse", dest="SendDateProposal")
        fsm.add_transition(source="DateProposalResponse", dest="DateAccepted")
        fsm.add_transition(source="DateProposalResponse", dest="DateRejected")
        self.add_behaviour(fsm)


    class CreateAuthenticationAndPaymentBehav(FSMBehaviour):

        async def on_start(self):
            print(f"[{self.agent.jid.localpart}] Client fsm starting at initial state {self.current_state}")

        async def on_end(self):
            print(f"[{self.agent.jid.localpart}] Client fsm finished at state {self.current_state}")
            await self.agent.stop()
    
    class AuthenticationState(State):
        async def run(self):
            metadata = {"type": "UserAuthentication"}
            msg = Messaging.prepare_message(Agents.CLIENT,Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print(f"[{self.agent.jid.localpart}] Message sent!")
            self.set_next_state("STATE_TWO")


    class AuthenticationResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"[{self.agent.jid.localpart}] Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_THREE")


    class PaymentInitialState(State):
        async def run(self):
            metadata = {"type": "UserPaymentInitial"}
            msg = Messaging.prepare_message(Agents.CLIENT, Agents.SUPERVISOR, "", **metadata)
            
            await self.send(msg)
            print(f"[{self.agent.jid.localpart}] Message sent!")
            self.set_next_state("STATE_FOUR")

    class PaymentResponseState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"[{self.agent.jid.localpart}] Incoming msg_type: {msg_type}")
            self.set_next_state("STATE_FIVE")
    
    class MachineAvailableState(State):
        async def run(self):
            msg = await self.receive(timeout=10)
            msg_type = msg.get_metadata("type")
            print(f"[{self.agent.jid.localpart}] Incoming msg_type: {msg_type}")
            
    class PenaltyNotificationBehav(CyclicBehaviour):
        
        async def run(self):
            print(f"[{self.agent.jid.localpart}] PenaltyNotificationBehav running")

            msg = await self.receive(timeout=10) # wait for a message for 10 seconds
            if msg:
                print(f"[{self.agent.jid.localpart}] Message received with content: {format(msg.body)}")
                print(f"[{self.agent.jid.localpart}] Message received with type: {format(msg.get_metadata('type'))}")
            else:
                print(f"[{self.agent.jid.localpart}] Did not received any message after 10 seconds")

            # stop agent from behaviour
            await self.agent.stop()
            

    async def setup(self):
        print ("Client started")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        penalty_behav = self.PenaltyNotificationBehav()
        penalty_template = Template()
        penalty_template.set_metadata("type", "Absences")
        self.add_behaviour(penalty_behav, penalty_template)
        #self.create_res_behav = self.CreateReservationBehav()
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
        #self.add_behaviour(fsm)
        
        self.dates_priority_list = list()
        tmp_template = Template()
        tmp_template.set_metadata("type", "tmp")
        create_res_behav = self.CreateReservationBehav(self.dates_priority_list)
        #self.add_behaviour(create_res_behav, tmp_template)
        
        

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