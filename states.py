from aiogram.fsm.state import State, StatesGroup


class PRForm(StatesGroup):
    waiting_referrer = State()


class ClientForm(StatesGroup):
    title = State()
    description = State()
    budget = State()


class DevForm(StatesGroup):
    name = State()
    level = State()
    solution = State()


class TesterForm(StatesGroup):
    name = State()
    level = State()
    report = State()


class AssignForm(StatesGroup):
    senior = State()
    medium1 = State()
    medium2 = State()
    tester = State()