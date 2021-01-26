from spade.agent import Agent
from spade.behaviour import CyclicBehaviour, FSMBehaviour, State
from spade.template import Template
from spade.message import Message
from utils.messaging import Messaging
from constants.agents import Agents
from constants.performatives import Performatives
import pathlib
import sqlite3
from json import loads
import datetime



class Supervisor(Agent):
    
    class SupervisorBehav(CyclicBehaviour):
        async def run(self):
            msg = await self.receive(timeout=10)
            if msg:
                msg_performative = msg.get_metadata("performative")
                print(f"[{self.agent.jid.localpart}] Incoming msg_performative: {msg_performative}")
                if msg_performative == Performatives.USER_PENALTIES_VERIFICATION:
                    await self.send(self.send_user_penalties_verification_response(msg))
                    print(f"[{self.agent.jid.localpart}] Message sent to Client!") 
                elif msg_performative == Performatives.REQUEST_USER_AUTHENTICATION:
                    #ask timetable for user 
                    await self.send(self.check_user_reservation(msg))
                    print(f"[{self.agent.jid.localpart}] Message sent to Timetable!") 
                elif msg_performative == Performatives.RESERVATION_CHECK_RESPONSE_ACCEPTED:
                    await self.send(self.send_user_authentication_accepted(msg))
                elif msg_performative == Performatives.RESERVATION_CHECK_RESPONSE_REJECTED:
                    await self.send(self.send_user_authentication_rejected(msg))
                elif msg_performative == Performatives.USER_PAYMENT_INITIAL:
                    #if payment == accepted 
                    await self.send(self.send_user_payment_accepted(msg))
                    await self.send(self.send_grant_access_request(msg)) #send "open" message to washing machine 
                    #TODO informacje z której pralki będzie korzystał klient
                    #else send refused to client  
                    await self.send(self.send_user_payment_rejected(msg))
                elif msg_performative == Performatives.CONFIRM_ACCESS_GRANTED:
                    await self.send(self.send_user_access_granted(msg))
                elif msg_performative == Performatives.INFORM_USER_ABSENCE:
                    #self.agent.delete()
                    #self.agent.insert_test_data()
                    #self.agent.test_select()
                    result = self.send_absences_information(msg)
                    if result is not None:
                        await self.send(self.send_absences_information(msg))
            else:
                print(f"[{self.agent.jid.localpart}] Didn't receive a message!")     
            #await self.agent.stop()
                

        def send_absences_information(self, msg):
            
            self.agent.insert_absences(msg.body)
            #print (f"[{self.agent.jid.localpart}] Message received with content: {format(msg.body)}")
            #self.agent.test_select()
            self.absences = self.agent.check_absences()
            if self.absences:
                for client in self.absences:
                    metadata = {"performative": Performatives.ABSENCES}
                    return Messaging.prepare_message(Agents.SUPERVISOR, Agents.CLIENT, "", **metadata)
                                       # Set the message content
            else: return None


        def send_user_penalties_verification_response(self, msg):
            username = msg.sender.localpart
            #TODO tutaj też nie wiem jak się odwołać to funkcji spoza behav
            #if self.search_for_active_penalties(username) > 0:
            if True:
                #metadata["status"] = "rejected"
                metadata = {"performative": Performatives.USER_PENALTIES_VERIFICATION_REJECTED}
            else:
                #metadata["status"] = "accepted"
                metadata = {"performative": Performatives.USER_PENALTIES_VERIFICATION_ACCEPTED}
                        
            return Messaging.prepare_message(Agents.SUPERVISOR, username, "", **metadata)
                
        def check_user_reservation(self, msg):
            username = msg.sender.localpart
            metadata = {"performative": Performatives.RESERVATION_CHECK}
            #TODO wysylanie informacji o kliencie w wiadomości
            return Messaging.prepare_message(Agents.SUPERVISOR, Agents.TIMETABLE, "", **metadata)  

        def send_user_authentication_accepted(self, msg):
            #TODO pobieranie informacji o kliencie z wiadomości
            username = "client"
            metadata = {"performative": Performatives.USER_AUTHENTICATION_ACCEPTED}
            return Messaging.prepare_message(Agents.SUPERVISOR, username, "", **metadata)   
                
        def send_user_authentication_rejected(self, msg):
            #TODO pobieranie informacji o kliencie z wiadomości
            username = "client"
            metadata = {"performative": Performatives.USER_AUTHENTICATION_REJECTED}
            return Messaging.prepare_message(Agents.SUPERVISOR, username, "", **metadata) 

        def send_user_payment_accepted(self, msg):
            metadata = {"performative": Performatives.USER_PAYMENT_ACCEPTED}
            return Messaging.prepare_message(Agents.SUPERVISOR, msg.sender, "", **metadata) 
                
        def send_user_payment_rejected(self, msg):
            metadata = "AccessGranted"{"performative": Performatives.USER_PAYMENT_REJECTED}
            return Messaging.prepare_message(Agents.SUPERVISOR, msg.sender, "", **metadata) 
                
        def send_grant_access_request(self, msg):
            metadata = {"performative": Performatives.REQUEST_GRANT_ACCESS}
            #TODO potrzebne informacje którą pralkę poinformować
            return Messaging.prepare_message(Agents.SUPERVISOR, "washingmachine1@localhost", "", **metadata)
            
        def send_user_access_granted(self, msg):
            metadata = {"performative": Performatives.CONFIRM_ACCESS_GRANTED}
            #TODO potrzebne informacje któremu klientowi przyznano dostęp; "client" tymczasowo
            return Messaging.prepare_message(Agents.SUPERVISOR, "client", "", **metadata)

    async def setup(self):
        print("Supervisor stared")
        self.db_connection = self.connect_to_local_db()
        self.db_init()
        #verify_msg_template = Template()
        #verify_msg_template.set_metadata("performative", "UserPenaltiesVerification")
        sup_behav = self.SupervisorBehav()
        self.add_behaviour(sup_behav)

        #absences_behav = self.CountAbsencesBehav()
        #absences_msg_template = Template()
        #absences_msg_template.set_metadata("performative", "UserAbsence")
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
                                            id integer NOT NULL,
                                            user text NOT NULL,
                                            type text NOT NULL,
                                            end_date text NOT NULL,
                                            PRIMARY KEY("id" AUTOINCREMENT)
                                    ); """
    
        sql_create_absences_table = """ CREATE TABLE IF NOT EXISTS absences (
                                                id INTEGER NOT NULL,
                                            	date	TEXT NOT NULL,
                                            	client	text NOT NULL,
                                            	PRIMARY KEY("id" AUTOINCREMENT)
                                        ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_create_penalties_table)
        crsr.execute(sql_create_absences_table)

    def search_for_active_penalties(self, username):
        sql_get_user_penalties = f""" SELECT COUNT(end_date) FROM penalties as p
                                        WHERE p.user = \"{username}\"
                                        AND datetime(p.end_date) > datetime('now');
                                    ); """

        crsr = self.db_connection.cursor()
        crsr.execute(sql_get_user_penalties)
        active_penalties = int(crsr.fetchall())

        return active_penalties
    
    
    def insert_absences(self, data):
        
        
        data_dict = loads(data)
        
        crsr = self.db_connection.cursor()
       
        
        for key in data_dict.keys():
            sql_insert_into_absences = f""" INSERT INTO absences (date, client)
                                    values('{data_dict[key][0]}' , '{data_dict[key][1]}'); """
            
            try:
                crsr.execute(sql_insert_into_absences)
                self.db_connection.commit()
            
            except Exception as e:
                print(e)
            
        
    
    def check_absences(self):
        
        
        sql_chceck_absences = """ SELECT  count (client), client 
                                from absences GROUP BY client"""
                                
        absences = []
        
        
        try:
            crsr = self.db_connection.cursor()
            crsr.execute(sql_chceck_absences)
            sql_chceck_absences = crsr.fetchall()
        except Exception as e:
            print(e) 
        
        
      #  print ("test")
       # print( sql_chceck_absences)
        
        for i in sql_chceck_absences:
            if i[0] >= 3:
                sql_get_latest = f""" SELECT * from absences where client = '{i[1]}' 
                                    ORDER BY id DESC LIMIT 1;"""
                try:
                    crsr = self.db_connection.cursor()
                    crsr.execute(sql_get_latest)
                    sql_get_latest = crsr.fetchall()
                    #print ("testetst")
                   # print (sql_get_latest)
                   # print (sql_get_latest[0][2])
                    absences.append(sql_get_latest[0][2])
                    
                    date = datetime.datetime.strptime(sql_get_latest[0][1],'%Y-%m-%d %H:%M:%S' )+datetime.timedelta(days=7)
                    
                    
                    sql_insert_penalty = f""" INSERT INTO penalties (user, type, end_date)
                                    values('{sql_get_latest[0][2]}' , 'UserAbsence','{date}'); """
                    
                    sql_delete_from_absences = f""" DELETE FROM absences WHERE 
                                                client = '{sql_get_latest[0][2]}';"""
                    
                    
                    try:
                        crsr.execute(sql_insert_penalty)
                        crsr.execute(sql_delete_from_absences)
                        self.db_connection.commit()
                        print ("hello")
                    
                    except Exception as e:
                        print(e)
                    
                except Exception as e:
                    print(e) 
                    
            return absences
                
                
    def test_select(self):
        
        sql_chceck_penalties = """ SELECT  * from penalties;"""
        
        sql_chceck_absences = """ SELECT  * from absences;"""
        
        try:
            crsr = self.db_connection.cursor()
            crsr.execute(sql_chceck_absences)
            sql_chceck_absences = crsr.fetchall()
            crsr.execute(sql_chceck_penalties)
            sql_chceck_penalties = crsr.fetchall()
            
            print ("absences")
            print (sql_chceck_absences)
            
            print ("penalties")
            print (sql_chceck_penalties)
            
            
        except Exception as e:
            print(e) 
            
    def delete(self):
         sql_delete_from_absences = """ DELETE FROM absences;"""
         sql_delete_from_penalties = """ DELETE FROM penalties;"""
                    
                    
         try:
            crsr = self.db_connection.cursor()
            crsr.execute(sql_delete_from_absences)
            crsr.execute(sql_delete_from_penalties)
            self.db_connection.commit()
            
         except Exception as e:
            print(e)
        
    
    
    def insert_test_data(self):
        
       
        
       records = [('2021-01-22 00:00:00' , 'client1'),
                ('2021-01-23 00:00:00' , 'client2'),
                  ('2021-01-24 00:00:00' , 'client1')] 
            
       try:
            crsr = self.db_connection.cursor()
            crsr.executemany(" INSERT INTO absences (date, client) values(?, ?) ", records)
            self.db_connection.commit()
            
       except Exception as e:
                print(e)
        
        
    
    