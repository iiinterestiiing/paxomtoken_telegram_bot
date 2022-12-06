

# Импорт необходимых модулей

from aiogram import Bot, Dispatcher, executor, types

from datetime import datetime, timedelta
from random import randint
from time import time

import config
import dill
import os


# Инициализация объекта бота и диспетчера
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)


# Функции для UNIX времени и дат

def now() -> int:
	return int(round(time()))

def timestamp_to_date(time) -> str:
	return datetime.utcfromtimestamp(time).strftime('%Y/%m/%d')
	

# Информация о снятии токенов

class Payment:

	def __init__(self, payer_network_id: int, amount: int):
		self.payer_network_id = payer_network_id
		self.amount = amount
		self.timestamp = now()


# Информация о переводе между 2 пользователями

class Transaction:

	def __init__(self, sender_network_id: int, recipient_network_id: int, amount: int):
		self.sender_network_id = sender_network_id
		self.recipient_network_id = recipient_network_id
		self.amount = amount
		self.timestamp = now()


# Информация о майнинге

class Mining:

	def __init__(self, miner_network_id: int, reward: int):
		self.miner_network_id = miner_network_id
		self.reward = reward
		self.timestamp = now()


# Класс пользователя для дальнейшего добавления в общую сеть

class User:

	def __init__(self, telegram_id: int, network_id: int, username: str,
			mining_cooldown: int, mining_reward: int, month_payment: int):

		self.telegram_id = telegram_id
		self.network_id = network_id
		self.mining_cooldown = mining_cooldown
		self.mining_reward = mining_reward
		self.month_payment = month_payment
		self.timestamp = now()

		self.payments_history = []
		self.mining_history = []
		self.transactions = []

		self.partner_network_id = 0
		self.balance = 0

	def next_payment_timestamp() -> int:
		if len(self.payments_history) > 0:
			return self.payments_history[-1].timestamp
		else:
			return now()+timedelta(days=30).total_seconds()

	def all_mined(self) -> int:
		mined = 0

		for mining_unit in self.mining_history:
			mined += mining_unit.reward

		return mined

	def mined(self, timestamp: int) -> int:
		date = timestamp_to_date(timestamp)
		mined = 0

		for mining_unit in self.mining_history:
			if timestamp_to_date(mining_unit.timestamp) == date:
				mined += mining_unit.reward

		return mined

	def mined_today(self) -> int:
		return self.mined(now())

	def mined_yesterday(self) -> int:
		return self.mined(now()-timedelta(days=1).total_seconds())

	def all_received(self) -> int:
		received = 0

		for transaction in self.transactions:
			if transaction.recipient_network_id == self.network_id:
				received += transaction.amount

		return received

	def received(self, timestamp: int) -> int:
		date = timestamp_to_date(timestamp)
		received = 0

		for transaction in self.transactions:
			if transaction.recipient_network_id == self.network_id:
				if timestamp_to_date(transaction.timestamp) == date:
					received += transaction.amount

		return received

	def received_today(self) -> int:
		return self.received(now())

	def received_yesterday(self) -> int:
		return self.received(now()-timedelta(days=1).total_seconds())

	def all_sended(self) -> int:
		sended = 0

		for transaction in self.transactions:
			if transaction.sender_network_id == self.network_id:
				sended += transaction.amount

		return sended

	def sended(self, timestamp: int) -> int:
		date = timestamp_to_date(timestamp)
		sended = 0

		for transaction in self.transactions:
			if transaction.sender_network_id == self.network_id:
				if timestamp_to_date(transaction.timestamp) == date:
					sended += transaction.amount

		return sended

	def sended_today(self) -> int:
		return self.sended(now())

	def sended_yesterday(self) -> int:
		return self.sended(now()-timedelta(days=1).total_seconds())

	def senders_top(self) -> dict:
		senders = {}

		for transaction in self.transactions:
			if transaction.recipient_network_id == self.network_id:
				if transaction.sender_network_id not in senders:
					senders[transaction.sender_network_id] = transaction.amount
				else:
					senders[transaction.sender_network_id] += transaction.amount

		return senders

	def recipients_top(self) -> dict:
		recipients = {}

		for transaction in self.transactions:
			if transaction.sender_network_id == self.network_id:
				if transaction.recipient_network_id not in recipients:
					recipients[transaction.recipient_network_id] = transaction.amount
				else:
					recipients[transaction.recipient_network_id] += transaction.amount

		return recipients

	def last_mining_timestamp(self) -> int:
		if len(self.mining_history) > 0:
			return self.mining_history[-1].timestamp
		else:
			return 0

	def is_on_cooldown(self) -> bool:
		return now() - self.last_mining_date < self.mining_cooldown

	def have_partner(self) -> bool:
		return self.partner_network_id != 0
	

# Общая сеть, содержащая список пользователей, список всех транзакций, историй майнинга и т.п.

class Network:

	mining_cooldown = config.MINING_COOLDOWN
	mining_reward = config.MINING_REWARD
	tokens_limit = config.TOKENS_LIMIT
	upgrade_price = config.UPGRADE_PRICE
	month_payment = config.MONTH_PAYMENTS

	def __init__(self):
		self.users = []
		self.transactions = []
		self.mining_history = []

	def users_count() -> int:
		return len(self.users)

	def actual_id() -> int:
		return self.users_count() + 1

	def transactions_count() -> int:
		return len(self.transactions)

	def all_mined() -> int:
		mined = 0

		for mining_unit in self.mining_history:
			mined += mining_unit.reward

		return mined

	def mined(timestamp: int) -> int:
		date = timestamp_to_date(timestamp)
		mined = 0

		for mining_unit in self.mining_history:
			if timestamp_to_date(mining_unit.timestamp) == date:
				mined += mining_unit.reward

		return mined

	def mined_today() -> int:
		return self.mined(now())

	def mined_yesterday() -> int:
		return self.mined(now()-timedelta(days=1).total_seconds())

	def is_registred(self, telegram_id: int) -> bool:
		for user in self.users:
			if user.telegram_id == telegram_id:
				return True
		else:
			return False

	def get_user_from_network_id(self, network_id: int) -> User or None:
		for user in self.users:
			if user.network_id == network_id:
				return User
		else:
			return None

	def get_user(self, telegram_id: int) -> User or None:
		for user in self.users:
			if user.telegram_id == telegram_id:
				return user
		else:
			return None

	def add_user(self, telegram_id: int, username: str):
		user = User(telegram_id, self.actual_id(), self.username,
				self.mining_cooldown, self.mining_reward,
				self.month_payment)

		self.users.append(user)

	def mine(self, telegram_id: int):
		user = self.get_user(telegram_id)
		mining_unit = Mining(user.network_id, user.mining_reward)

		user.balance += user.mining_reward

		self.mining_history.append(mining_unit)
		user.append(mining_history_unit)

	def transfer(self, telegram_id: int, network_id: int, amount: int):
		user = self.get_user(telegram_id)
		recipient = self.get_user_from_network_id(network_id)

		transaction = Transaction(user.network_id, recipient.bot_id, amount)

		user.balance -= amount
		user.transactions.append(transaction)

		recipient.balance += amount
		recipient.transactions.append(transaction)

		self.transactions.append(transaction)

	def payment(self, telegram_id: int):
		user = self.get_user(telegram_id)
		payment = Payment(user.network_id, user.month_payment)
		user.balance -= user.month_payment

	def take_partner(self, telegram_id: int, network_id: int):
		user = get_user(telegram_id)
		partner = get_user_from_network_id(network_id)

		user.month_payment /= 2
		partner.month_payment /= 2

	def delete_partner(self, telegram_id: int):
		user = self.get_user(telegram_id)
		partner = self.get_user_from_network_id(user.partner_network_id)

		user.month_payment *= 2
		partner.month_payment *= 2

		user.partner_network_id = 0


# Загрузка сети

def load_network(path: str) -> Network:
	if os.path.exists(path) and os.path.getsize(path) > 0:
		with open(path, "rb") as file:
			return dill.load(file)

# Сохранение изменений в сети

def save_network(path: str, network: Network):
	with open(path, "wb") as file:
		dill.dump(network, file)


# Дальше будет привязка комманд к вышеперечисленным объектам 
