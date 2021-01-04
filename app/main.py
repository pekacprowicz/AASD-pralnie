import spade
import time
import asyncio
from agents.supervisor import Supervisor
from agents.client import Client
from agents.timetable import Timetable

# asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # necessary on Windows


if __name__ == "__main__":
    '''
    sv = Supervisor("supervisor@localhost", "123456")
    future = sv.start(auto_register=True)
    future.result()
    sv.web.start()
    print("Agent web at {}:{}".format(sv.web.hostname, sv.web.port))
    cl = Client("client1@localhost", "123456")
    cl.start()
    cl.web.start()
    print("Agent web at {}:{}".format(cl.web.hostname, cl.web.port))

    while sv.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            cl.stop()
            sv.stop()
            break
    print("Agents finished")
    
    ''' 
    #informacja o (nie)wykorzystzanym praniu 
    
    clientAgent = Client("client@localhost", "aasd")
    clientAgent.start()
    supervisorAgent = Supervisor("supervisor@localhost", "123456")
    future = supervisorAgent.start()
   
    future.result() # wait for receiver agent to be prepared.
    
    timatableAgent = Timetable("timetable@localhost", "123456")
    timatableAgent.start()
   
    

    while supervisorAgent.is_alive():
        try:
            time.sleep(1)
        except KeyboardInterrupt:
            supervisorAgent.stop()
            timatableAgent.stop()
            clientAgent.stop()
            break
    print("Agents finished")
    
    
    