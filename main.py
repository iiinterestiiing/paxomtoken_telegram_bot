from aiogram import Bot, Dispatcher, executor, types

from datetime import datetime
from random import randint
from time import time

import config
import dill


bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)


def now() -> int:
	return int(round(time()))

def time_to_date(time) -> str:
	return datetime.utcfromtimestamp(time).strftime('%Y/%m/%d')
	

class Transaction:

	def __init__(self, sender_bot_id: int, recipient_bot_id: int, amount: int):
		self.sender_bot_id = sender_bot_id
		self.recipient_bot_id = recipient_bot_id
		self.amount = amount
		self.date = now()


class Mining:

	def __init__(self, miner_bot_id: int, reward: int):
		self.miner_bot_id = miner_bot_id
		self.reward = reward
		self.date = now()


class User:

	def __init__(self, telegram_id: int, network_id: int,
			mining_cooldown: int, mining_reward: int):

		self.telegram_id = telegram_id
		self.network_id = network_id
		self.mining_cooldown = mining_cooldown
		self.mining_reward = mining_reward
		self.registration_date = now()
		self.mining_history = []
		self.transactions = []
		self.balance = 0

	def all_mined(self, history: list) -> int:
		mined = 0

		for mining_history_unit in mining_history:
			mined += mining_history_unit.reward

		return mined

	def mined_for(self, date: str) -> int:
		mined = 0

		for mining_history_unit in self.mining_history:
			if time_to_date(mining_history_unit.date) == date:
				mined += mining_history_unit.reward
			else:
				break

		return mined

	def mined_today(self) -> int:
		date = time_to_date(now()-24*60*60)
		mined = self.mined_for(today_date)
		return mined

	def mined_yesterday(self) -> int:
		date = time_to_date(now()-datetime(date=1).total_seconds())
		mined = self.mined_for(date)
		return mined

	def last_mining_date(self):
		if len(self.mining_history) > 0:
			return self.mining_history[-1].date
		else:
			return 0

	def is_on_cooldown(self) -> bool:
		return now() - self.last_mining_date < self.mining_cooldown
	

class Network:

	mining_cooldown = config.MINING_COOLDOWN
	mining_reward = config.MINING_REWARD
	tokens_limit = config.TOKENS_LIMIT

	def __init__(self):
		self.users = []
		self.transactions = []
		self.mining_history = []

	def users_count() -> int:
		return len(self.users)

	def actual_id() -> int:
		return self.users_count() + 1

	def is_registred(self, telegram_id: int) -> bool:
		for user in self.users:
			if user.telegram_id == telegram_id:
				return True
		else:
			return False

	def get_user_from_bot_id(self, bot_id: int) -> User or None:
		for user in self.users:
			if user.bot_id == bot_id:
				return User
		else:
			return None

	def get_user(self, telegram_id: int) -> User or None:
		for user in self.users:
			if user.telegram_id == telegram_id:
				return user
		else:
			return None

	def add_user(self, telegram_id: int):
		user = User(telegram_id, self.actual_id(), self.mining_reward)
		self.users.append(user)

	def mine(self, telegram_id: int):
		user = self.get_user(telegram_id)
		mining_history_unit = Mining(user.bot_id, user.mining_reward)

		user.balance += user.mining_reward

		self.mining_history.append(mining_history_unit)
		user.append(mining_history_unit)

	def transfer(self, telegram_id: int, bot_id: int, amount: int):
		user = self.get_user(telegram_id)
		recipient = self.get_user_from_bot_id(bot_id)

		transaction_history_unit = Transaction(user.bot_id, recipient.bot_id, amount)

		user.balance -= amount
		user.transactions.append(transaction_history_unit)

		recipient.balance += amount
		recipient.transactions.append(transaction_history_unit)

		self.transactions.append(transaction_history_unit)


@dp.message_handler(commands=["start"])
async def start(message: types.Message):
	print(message)


#if __name__ == "__main__":
	#executor.start_polling(dispatcher=dp, skip_updates=True)