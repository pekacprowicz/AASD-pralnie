import time

from spade.agent import Agent
from spade.message import Message
from utils.messaging import Messaging
from spade.behaviour import FSMBehaviour, State
from constants.agents import Agents

STATE_FREE = "STATE_FREE"
STATE_AUTH = "STATE_AUTH"
STATE_WORKING = "STATE_WORKING"

class WashingMachineFSMBehaviour(FSMBehaviour):
    async def on_start(self):
        print(f"Washing machine starting at initial state {self.current_state}")

    async def on_end(self):
        print(f"Washing machine finished at state {self.current_state}")
        await self.agent.stop()

class StateFree(State):
    async def run(self):
        print("I'm at state free")
        msg = await self.receive(timeout=10)
        if msg:
            msg_performative = msg.get_metadata("performative")
            print(f"Incoming msg_performative: {msg_performative}")
            if msg_performative == "GrantAccessRequest":
                self.agent.supervisor = msg.sender
                self.agent.client = msg.get_metadata("client")
                self.set_next_state(STATE_AUTH)

        print(f"No message...")
        self.set_next_state(STATE_FREE)
        
class StateAuth(State):
    async def run(self):
        print("I'm at state auth")

        metadata = {"performative": "AccessGrantedConfirm", "client": self.agent.client}
        msg = Messaging.prepare_message(self.agent.jid, self.agent.supervisor, "", **metadata)
        await self.send(msg)

        self.set_next_state(STATE_WORKING)

class StateWorking(State):
    async def run(self):
        print("I'm at state working")
        time.sleep(10)

        metadata = {"performative": "WorkCompletedInform"}
        msg = Messaging.prepare_message(self.agent.jid, self.agent.client, "", **metadata)
        await self.send(msg)

        self.set_next_state(STATE_FREE)

class WashingMachine(Agent):
    supervisor: str
    client: str

    async def setup(self):
        fsm = WashingMachineFSMBehaviour()
        fsm.add_state(name=STATE_FREE, state=StateFree(), initial=True)
        fsm.add_state(name=STATE_AUTH, state=StateAuth())
        fsm.add_state(name=STATE_WORKING, state=StateWorking())
        fsm.add_transition(source=STATE_FREE, dest=STATE_FREE)
        fsm.add_transition(source=STATE_FREE, dest=STATE_AUTH)
        fsm.add_transition(source=STATE_AUTH, dest=STATE_WORKING)
        fsm.add_transition(source=STATE_WORKING, dest=STATE_FREE)
        self.add_behaviour(fsm)