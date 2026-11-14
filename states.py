from aiogram.fsm.state import State, StatesGroup


class ClientForm(StatesGroup):
    """Состояния для формы заказа разработки."""
    title = State()
    description = State()
    budget = State()


class DevForm(StatesGroup):
    """Состояния для анкеты разработчика."""
    name = State()
    experience = State()
    level = State()
    portfolio = State()


class TesterForm(StatesGroup):
    """Состояния для анкеты тестировщика."""
    name = State()
    experience = State()
    level = State()


class PRForm(StatesGroup):
    """Состояния для анкеты пиарщика."""
    waiting_referrer = State()


class AssignForm(StatesGroup):
    """Состояния для назначения команды на проект."""
    senior = State()
    medium1 = State()
    medium2 = State()
    tester = State()
