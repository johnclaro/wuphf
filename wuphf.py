import uuid
import hashlib

import mysql.connector


class Database:

    def __init__(self):
        self.connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='Passw0rd'
        )
        self.cursor = self.connection.cursor()


# 1. To perform database operations relating to `accounts` and `woofs` table
# 2. To perform hashing and verification on password
class Account(Database):

    def __init__(self, username, password):
        Database.__init__(self)
        self.account_id = None
        self.username = username
        self.password = password
        self.salt = uuid.uuid4().hex

    def hash_password(self, password, salt):
        encoded = salt.encode() + password.encode()
        digest = hashlib.sha256(encoded).hexdigest()
        password_hashed = f'{digest}:{salt}'
        return password_hashed

    def check_password(self, password_input, password_database):
        _, salt = password_database.split(':')
        password_hashed = self.hash_password(password_input, salt)
        return password_hashed == password_database

    def register(self):
        try:
            password_hashed = self.hash_password(self.password, self.salt)
            sql = f"INSERT INTO wuphf.accounts(username, password) VALUES ('{self.username}', '{password_hashed}')"
            self.cursor.execute(sql)
            self.connection.commit()
        except mysql.connector.errors.IntegrityError:
            return 'Invalid username'
        else:
            return 'Success'

    def login(self):
        sql = f"SELECT id, password FROM wuphf.accounts WHERE username='{self.username}'"
        self.cursor.execute(sql)
        record = self.cursor.fetchone()
        if record:
            account_id = record[0]
            password = record[1]
            if self.check_password(self.password, password):
                # Set account ID if account exists in database so we can reference the account ID when creating a woof
                self.account_id = account_id
                return 'Success'
            else:
                return 'Invalid username or password'
        else:
            return 'Invalid username or password'

    def update_username(self, new_username):
        sql = f"""
        UPDATE wuphf.accounts
        SET username='{new_username}'
        WHERE username='{self.username}'
        """
        self.cursor.execute(sql)
        self.connection.commit()
        self.username = new_username

    def update_password(self, new_password):
        new_password_hashed = self.hash_password(new_password, self.salt)
        sql = f"""
        UPDATE wuphf.accounts
        SET password='{new_password_hashed}'
        WHERE username='{self.username}'
        """
        self.cursor.execute(sql)
        self.connection.commit()
        self.password = new_password_hashed

    def delete_account(self):
        sql = f"DELETE FROM wuphf.accounts WHERE username='{self.username}'"
        self.cursor.execute(sql)
        self.connection.commit()

    def create_woof(self, message):
        try:
            sql = f"INSERT INTO wuphf.woofs VALUES (NULL, {self.account_id}, '{message}')"
            self.cursor.execute(sql)
            self.connection.commit()
        except mysql.connector.errors.DataError:
            return 'Invalid message'
        else:
            return 'Success'

    def get_woofs(self):
        sql = f"SELECT id, message FROM wuphf.woofs WHERE account_id='{self.account_id}'"
        self.cursor.execute(sql)
        woofs = self.cursor.fetchall()
        return woofs

    def delete_woof(self, woof_id):
        sql = f"DELETE FROM wuphf.woofs WHERE id={woof_id} and account_id={self.account_id}"
        self.cursor.execute(sql)
        response = self.connection.commit()
        return response


# 1. To print out messages in command-line for user
# 2. To prompt for the 'action' input from user
# 3. To use the functions in the Account class
# 4. To initialize the database
class Wuphf(Database):

    def __init__(self):
        Database.__init__(self)
        self.account = None

    def initialize_database(self):
        self.cursor.execute('CREATE DATABASE IF NOT EXISTS wuphf')

        sql = """
        CREATE TABLE IF NOT EXISTS wuphf.accounts (
            id INT NOT NULL UNIQUE AUTO_INCREMENT,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL,
            PRIMARY KEY (id)
        );
        """
        self.cursor.execute(sql)

        sql = """
        CREATE TABLE IF NOT EXISTS wuphf.woofs (
            id INT NOT NULL UNIQUE AUTO_INCREMENT,
            account_id INT NOT NULL,
            message VARCHAR(280) NOT NULL,
            PRIMARY KEY (id),
            FOREIGN KEY (account_id)
                REFERENCES wuphf.accounts(id)
                ON DELETE CASCADE
        );
        """
        self.cursor.execute(sql)

        self.connection.commit()
        print('Database created')

    def show_landing_page(self):
        print('\n=== LANDING PAGE ===')
        print('1. Register')
        print('2. Login')
        print('0. Exit')
        action = input('> Welcome to Wuphf, what would you like to do? [Select a number]: ')
        return action

    def show_dashboard_page(self):
        print(f"\n=== {self.account.username}'s DASHBOARD PAGE ===")
        print('1. Create woof')
        print('2. List all my woofs')
        print('3. Delete woof')
        print('4. Update username')
        print('5. Update password')
        print('6. Delete account')
        print('7. Logout')
        print('0. Exit')
        action = input(f"> Welcome back, what would you like to do? [Select a number]: ")
        return action

    def show_register_page(self):
        print('\n=== REGISTER PAGE ===')
        username = input('> Enter a username: ')
        password = input('> Enter a password: ')
        account = Account(username, password)
        if username and password:
            response = account.register()
            if response == 'Success':
                print('Successfully created account, you may now login')
            elif response == 'Invalid username':
                print('That username has already been taken')
        else:
            print('Username or password cannot be empty')

    def show_login_page(self):
        print('\n=== LOGIN PAGE ===')
        username = input('> Enter a username: ')
        password = input('> Enter a password: ')
        account = Account(username, password)
        response = account.login()
        if response == 'Success':
            self.account = account
            print('Login successful')
        elif response == 'Invalid username or password':
            print('The username and password you entered did not match our records. Please double-check and try again.')

    def show_update_username_page(self):
        print('\n=== UPDATE USERNAME PAGE ===')
        new_username = input('> Enter new username: ')
        if new_username:
            self.account.update_username(new_username)
            print('Successfully updated username')
        else:
            print('New username cannot be empty')

    def show_update_password_page(self):
        print('\n=== UPDATE PASSWORD PAGE ===')
        new_password = input('> Enter new password: ')
        if new_password:
            self.account.update_password(new_password)
            self.account = None
            print('Successfully updated password, please login again')
        else:
            print('New password cannot be empty')

    def show_delete_account_page(self):
        print('\n=== DELETE ACCOUNT PAGE ===')
        confirm = input('> Are you sure you want to delete this account? (y/n): ')
        confirm = confirm.lower()
        if confirm == 'y':
            self.account.delete_account()
            self.account = None
            print('Successfully deleted account')
        else:
            print('Cancelled account deletion')

    def show_logout_page(self):
        print('\n=== LOG OUT PAGE ===')
        self.account = None
        print('Successfully logged out')

    def show_create_woof_page(self):
        print('\n=== CREATE WUPHF PAGE ===')
        message = input("> What's happening? ")
        if not message:
            print('Message cannot be empty')
        elif len(message) > 280:
            print('Message cannot exceed 280 characters')
        else:
            response = self.account.create_woof(message)
            if response == 'Success':
                print('Successfully created woof')
            else:
                print('The message cannot be empty or has exceeded 280 characters')

    def show_my_woofs_page(self):
        print(f"\n=== {self.account.username}'s WUPHFS PAGE ===")
        woofs = self.account.get_woofs()
        if woofs:
            for index, woof in enumerate(woofs):
                woof_id = woof[0]
                message = woof[1]
                print(f'\n{message}')
                print(f'(Tweet ID is {woof_id})')
        else:
            print('You have no woofs')

    def show_delete_woof_page(self):
        print('\n=== DELETE WUPHF PAGE ===')
        try:
            woof_id = input("> Which woof do you want to delete? [Enter ID of woof]: ")
            woof_id = int(woof_id)
            self.account.delete_woof(woof_id)
        except ValueError:
            print('Invalid input, please provide a valid ID of the woof')
        else:
            print('Successfully deleted woof')

    def prompt_action(self):
        if not self.account:
            action = self.show_landing_page()
        else:
            action = self.show_dashboard_page()

        try:
            action = int(action)
        except ValueError:
            print('Please provide a number for the action')
        else:
            return action


def main():
    wuphf = Wuphf()
    wuphf.initialize_database()

    action = wuphf.prompt_action()
    while action != 0:
        if not wuphf.account:
            if action == 1:
                wuphf.show_register_page()
            elif action == 2:
                wuphf.show_login_page()
            else:
                print('Invalid action, try again')
        else:
            if action == 1:
                wuphf.show_create_woof_page()
            elif action == 2:
                wuphf.show_my_woofs_page()
            elif action == 3:
                wuphf.show_delete_woof_page()
            elif action == 4:
                wuphf.show_update_username_page()
            elif action == 5:
                wuphf.show_update_password_page()
            elif action == 6:
                wuphf.show_delete_account_page()
            elif action == 7:
                wuphf.show_logout_page()
            else:
                print('Invalid action, try again')

        action = wuphf.prompt_action()

    print('Closing Wuphf...')


if __name__ == '__main__':
    main()
