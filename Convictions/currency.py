import os
import json

class CurrencyManager:
    def __init__(self, currency_folder):
        self.currency_folder = currency_folder
        self.currency_file = os.path.join(currency_folder, "currency.json")
        self.currency_data = self.load_currency_data()

    def load_currency_data(self):
        if os.path.exists(self.currency_file):
            with open(self.currency_file, "r") as file:
                data = json.load(file)
            return data
        return {}

    def save_currency_data(self):
        with open(self.currency_file, "w") as file:
            json.dump(self.currency_data, file, indent=4)

    def get_balance(self, user_id):
        return self.currency_data.get(str(user_id), 0)  # Default balance is 0

    def set_balance(self, user_id, balance):
        self.currency_data[str(user_id)] = balance
        self.save_currency_data()
