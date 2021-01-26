from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.template import Template
from spade.message import Message
from utils.messaging import Messaging
from constants.agents import Agents
import pathlib
import sqlite3
import random
from utils.messaging import Messaging 


class Supervisor(Agent):
    
    class SupervisorBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_type = msg.get_metadata("type")
                print(f"[{self.agent.jid.localpart}] Incoming msg_type: {msg_type}")
                if msg_type == "UserPenaltiesVerification":
                    await self.send(self.send_user_penalties_verification_response(msg))
                    print(f"[{self.agent.jid.localpart}] Message sent to Client!") 
                elif msg_type == "UserAuthentication":
                    #ask timetable for user 
                    await self.send(self.check_user_reservation(msg))
                    print(f"[{self.agent.jid.localpart}] Message sent to Timetable!") 
                elif msg_type == "ReservationCheckResponseAccepted":
                    await self.send(self.send_user_authentication_accepted(msg))
                elif msg_type == "ReservationCheckResponseRejected":
                    await self.send(self.send_user_authentication_rejected(msg))
                elif msg_type == "UserPaymentInitial":
                    #if payment == accepted 
                    await self.send(self.send_user_payment_accepted(msg))
                    await self.send(self.send_grant_access_request(msg)) #send "open" message to washing machine 
                    #TODO informacje z której pralki będzie korzystał klient
                    #else send refused to client  
                    await self.send(self.send_user_payment_rejected(msg))
                
                elif msg_type == "AccessGranted":
                    await self.send(self.send_user_access_granted(msg))
                elif msg_type == "UserAbsence":
                    await self.send(self.send_absences_information())
            else:
                print(f"[{self.agent.jid.localpart}] Didn't receive a message!")     
            #await self.agent.stop()
                
        def countAbsences(self):
                #check in db
                #absences = random.choice([0, 3])
                #  print (absences)
            return 3

        def send_absences_information(self):
            self.absences = self.countAbsences()
            if self.absences == 3:
                            
                metadata = {"type": "Absences"}
                return Messaging.prepare_message(Agents.SUPERVISOR, Agents.CLIENT, "", **metadata)
                    # Set the message content

        def send_user_penalties_verification_response(self, msg):
            username = msg.sender.localpart
            metadata = {"type": "UserPenaltiesVerificationResponse"}
            #TODO tutaj też nie wiem jak się odwołać to funkcji spoza behav
            #if self.search_for_active_penalties(username) > 0:
            if True:
                #metadata["status"] = "rejected"
                metadata = {"type": "UserPenaltiesVerificationRejected"}
            else:
                #metadata["status"] = "accepted"
                metadata = {"type": "UserPenaltiesVerificationAccepted"}
                        
            return Messaging.prepare_message(Agents.SUPERVISOR, msg.sender, "", **metadata)
                
        def check_user_reservation(self, msg):
            username = msg.sender.localpart
            metadata = {"type": "ReservationCheck"}
            #TODO wysylanie informacji o kliencie w wiadomości
            return Messaging.prepare_message(Agents.SUPERVISOR, Agents.TIMETABLE, "", **metadata)  

        def send_user_authentication_accepted(self, msg):
            #TODO pobieranie informacji o kliencie z wiadomości
            username = "client"
            metadata = {"type": "UserAuthenticationAccepted"}
            return Messaging.prepare_message(Agents.SUPERVISOR, username, "", **metadata)   
                
        def send_user_authentication_rejected(self, msg):
            #TODO pobieranie informacji o kliencie z wiadomości
            username = "client"
            metadata = {"type": "UserAuthenticationRejected"}
            return Messaging.prepare_message(Agents.SUPERVISOR, username, "", **metadata) 

        def send_user_payment_accepted(self, msg):
            metadata = {"type": "UserPaymentAccepted"}
            return Messaging.prepare_message(Agents.SUPERVISOR, msg.sender, "", **metadata) 
                
        def send_user_payment_rejected(self, msg):
            metadata = {"type": "UserPaymentRejected"}
            return Messaging.prepare_message(Agents.SUPERVISOR, msg.sender, "", **metadata) 
                
        def send_grant_access_request(self, msg):
            metadata = {"type": "GrantAccess"}
            #TODO potrzebne informacje którą pralkę poinformować
            return Messaging.prepare_message(Agents.SUPERVISOR, "washingmachine1@localhost", "", **metadata)
            
        def send_user_access_granted(self, msg):
            metadata = {"type": "AccessGranted"}
            #TODO potrzebne informacje któremu klientowi przyznano dostęp; "client" tymczasowo
            return Messaging.prepare_message(Agents.SUPERVISOR, "client", "", **metadata)

    async def setup(self):
        print("Supervisor stared")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        #verify_msg_template = Template()
        #verify_msg_template.set_metadata("type", "UserPenaltiesVerification")
        sup_behav = self.SupervisorBehav()
        self.add_behaviour(sup_behav)

        #absences_behav = self.CountAbsencesBehav()
        #absences_msg_template = Template()
        #absences_msg_template.set_metadata("type", "UserAbsence")
        #self.add_behaviour(absences_behav, absences_msg_template)

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
        crsr.execute(sql_get_user_penalties)
        active_penalties = int(crsr.fetchall())

        return active_penalties