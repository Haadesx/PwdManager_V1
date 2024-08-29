from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.core.clipboard import Clipboard
from kivy.uix.checkbox import CheckBox
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
import sqlite3
import hashlib
import secrets
import string
from cryptography.fernet import Fernet

# Set the default window size
Window.size = (400, 600)

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        title = Label(text='Password Manager', font_size=24, size_hint_y=None, height=50, halign='center')
        layout.add_widget(title)
        
        username_label = Label(text='Username:', size_hint_y=None, height=30)
        self.username = TextInput(hint_text='Enter your username', multiline=False, size_hint_y=None, height=40)
        password_label = Label(text='Password:', size_hint_y=None, height=30)
        self.password = TextInput(hint_text='Enter your password', password=True, multiline=False, size_hint_y=None, height=40)
        
        login_button = Button(text='Login', size_hint_y=None, height=40, background_color=get_color_from_hex('#0080FF'), padding=(10, 10))
        register_button = Button(text='Register', size_hint_y=None, height=40, background_color=get_color_from_hex('#4CAF50'), padding=(10, 10))
        
        layout.add_widget(username_label)
        layout.add_widget(self.username)
        layout.add_widget(password_label)
        layout.add_widget(self.password)
        layout.add_widget(login_button)
        layout.add_widget(register_button)
        
        login_button.bind(on_press=self.login)
        register_button.bind(on_press=self.register)
        
        self.add_widget(layout)

    def login(self, instance):
        app = App.get_running_app()
        username = self.username.text.strip()
        password = self.password.text.strip()
        hashed_password = app.hash_password(password)
        app.cursor.execute("SELECT * FROM users WHERE username=? AND password=?", (username, hashed_password))
        user = app.cursor.fetchone()
        if user:
            app.current_user = user
            app.sm.current = 'manager'
            app.sm.get_screen('manager').load_passwords()
        else:
            self.show_popup("Error", "Invalid username or password")

    def register(self, instance):
        app = App.get_running_app()
        username = self.username.text.strip()
        password = self.password.text.strip()
        if len(password) < 8:
            self.show_popup("Error", "Password must be at least 8 characters long")
            return
        hashed_password = app.hash_password(password)
        try:
            app.cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
            app.conn.commit()
            self.show_popup("Success", "Registration successful")
        except sqlite3.IntegrityError:
            self.show_popup("Error", "Username already exists")

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        popup_label = Label(text=message)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.5))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

Window.size = (800, 600)  # Adjusted window size to fit more content

class ManagerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)

        # Title
        title = Label(text='Manage Your Passwords', font_size=24, size_hint_y=None, height=50)
        layout.add_widget(title)

        # Top section for adding new passwords
        top_section = BoxLayout(orientation='vertical', padding=10, spacing=10, size_hint_y=None, height=250)
        
        form_layout = GridLayout(cols=2, spacing=10, size_hint_y=None, height=150)
        
        form_layout.add_widget(Label(text='Account:'))
        self.account_input = TextInput(multiline=False, size_hint_y=None, height=30)
        form_layout.add_widget(self.account_input)
        
        form_layout.add_widget(Label(text='Username:'))
        self.username_input = TextInput(multiline=False, size_hint_y=None, height=30)
        form_layout.add_widget(self.username_input)
        
        form_layout.add_widget(Label(text='Password:'))
        self.password_input = TextInput(multiline=False, size_hint_y=None, height=30)
        form_layout.add_widget(self.password_input)
        
        form_layout.add_widget(Label(text='Length:'))
        self.length_input = TextInput(text='16', multiline=False, size_hint_y=None, height=30)
        form_layout.add_widget(self.length_input)
        
        top_section.add_widget(form_layout)
        
        # Checkboxes for password options
        options_layout = GridLayout(cols=4, spacing=10, size_hint_y=None, height=40)
        
        self.uppercase_check = CheckBox(active=True)
        self.lowercase_check = CheckBox(active=True)
        self.numbers_check = CheckBox(active=True)
        self.special_check = CheckBox(active=True)
        
        options_layout.add_widget(CheckBoxWrapper(self.uppercase_check, 'Uppercase'))
        options_layout.add_widget(CheckBoxWrapper(self.lowercase_check, 'Lowercase'))
        options_layout.add_widget(CheckBoxWrapper(self.numbers_check, 'Numbers'))
        options_layout.add_widget(CheckBoxWrapper(self.special_check, 'Special'))
        
        top_section.add_widget(options_layout)
        
        # Buttons
        buttons_layout = BoxLayout(spacing=10, size_hint_y=None, height=40)
        generate_button = Button(text='Generate', background_color=get_color_from_hex('#FFA500'))
        add_button = Button(text='Add', background_color=get_color_from_hex('#4CAF50'))
        buttons_layout.add_widget(generate_button)
        buttons_layout.add_widget(add_button)
        
        top_section.add_widget(buttons_layout)
        layout.add_widget(top_section)
        
        # Scrollable list of saved passwords
        self.passwords_list = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.passwords_list.bind(minimum_height=self.passwords_list.setter('height'))
        scroll = ScrollView(size_hint=(1, 1))
        scroll.add_widget(self.passwords_list)
        layout.add_widget(scroll)
        
        # Logout button
        logout_button = Button(text='Logout', size_hint_y=None, height=40, background_color=get_color_from_hex('#FF0000'))
        layout.add_widget(logout_button)
        
        self.add_widget(layout)
        
        # Bind button actions
        generate_button.bind(on_press=self.generate_password)
        add_button.bind(on_press=self.add_password)
        logout_button.bind(on_press=self.logout)

    def generate_password(self, instance):
        try:
            length = int(self.length_input.text)
        except ValueError:
            self.show_popup("Error", "Password length must be a number")
            return
        if length < 8 or length > 32:
            self.show_popup("Error", "Password length must be between 8 and 32 characters")
            return
        
        chars = ""
        if self.uppercase_check.active:
            chars += string.ascii_uppercase
        if self.lowercase_check.active:
            chars += string.ascii_lowercase
        if self.numbers_check.active:
            chars += string.digits
        if self.special_check.active:
            chars += string.punctuation
        
        if not chars:
            self.show_popup("Error", "Select at least one character type")
            return
        
        password = ''.join(secrets.choice(chars) for _ in range(length))
        self.password_input.text = password

    def add_password(self, instance):
        app = App.get_running_app()
        account = self.account_input.text.strip()
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        if not account or not username or not password:
            self.show_popup("Error", "All fields are required")
            return
        encrypted_password = app.fernet.encrypt(password.encode()).decode()
        app.cursor.execute("INSERT INTO passwords (user_id, account, username, password) VALUES (?, ?, ?, ?)",
                            (app.current_user[0], account, username, encrypted_password))
        app.conn.commit()
        self.load_passwords()
        self.account_input.text = ""
        self.username_input.text = ""
        self.password_input.text = ""
        self.length_input.text = "16"
        self.uppercase_check.active = True
        self.lowercase_check.active = True
        self.numbers_check.active = True
        self.special_check.active = True

    def load_passwords(self):
        app = App.get_running_app()
        self.passwords_list.clear_widgets()

        app.cursor.execute("SELECT * FROM passwords WHERE user_id=?", (app.current_user[0],))
        passwords = app.cursor.fetchall()

        if not passwords:
            self.passwords_list.add_widget(Label(text="No saved passwords", size_hint_y=None, height=30))
            return
        
        for row in passwords:
            row_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=None, height=40)
            account_label = Label(text=row[2], size_hint_x=None, width=130, height=30, halign='left', valign='middle')
            account_label.bind(size=account_label.setter('text_size'))
            username_label = Label(text=row[3], size_hint_x=None, width=200, height=30, halign='left', valign='middle')
            username_label.bind(size=username_label.setter('text_size'))

            options_layout = BoxLayout(spacing=10, size_hint_x=None, width=200, height=30)
            view_button = Button(text='View', size_hint_x=None, width=60, on_press=lambda x, pwd=row[4]: self.view_password(pwd))
            copy_button = Button(text='Copy', size_hint_x=None, width=60, on_press=lambda x, pwd=row[4]: self.copy_password(pwd))
            delete_button = Button(text='Delete', size_hint_x=None, width=60, on_press=lambda x, acc=row[2], usr=row[3]: self.delete_password(acc, usr))

            options_layout.add_widget(view_button)
            options_layout.add_widget(copy_button)
            options_layout.add_widget(delete_button)
            
            row_layout.add_widget(account_label)
            row_layout.add_widget(username_label)
            row_layout.add_widget(options_layout)
            
            self.passwords_list.add_widget(row_layout)

    def view_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        self.show_popup("Password", f"Password: {password}")

    def copy_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        Clipboard.copy(password)
        self.show_popup("Info", "Password copied to clipboard")

    def delete_password(self, account, username):
        app = App.get_running_app()
        app.cursor.execute("DELETE FROM passwords WHERE user_id=? AND account=? AND username=?", (app.current_user[0], account, username))
        app.conn.commit()
        self.load_passwords()

    def logout(self, instance):
        self.show_logout_confirmation()

    def show_logout_confirmation(self):
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        content.add_widget(Label(text="Are you sure you want to logout?"))
        
        buttons = BoxLayout(spacing=10)
        yes_button = Button(text='Yes', size_hint_y=None, height=40)
        no_button = Button(text='No', size_hint_y=None, height=40)
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)
        
        popup = Popup(title="Logout Confirmation", content=content, size_hint=(0.8, 0.5))
        
        yes_button.bind(on_press=lambda x: self.confirm_logout(popup))
        no_button.bind(on_press=popup.dismiss)
        popup.open()

    def confirm_logout(self, popup):
        popup.dismiss()
        app = App.get_running_app()
        app.current_user = None
        app.sm.current = 'login'
        
    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        popup_label = Label(text=message)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.5))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class CheckBoxWrapper(BoxLayout):
    def __init__(self, checkbox, label_text, **kwargs):
        super().__init__(orientation='horizontal', spacing=5, **kwargs)
        self.add_widget(checkbox)
        self.add_widget(Label(text=label_text))

    def generate_password(self, instance):
        try:
            length = int(self.length_input.text)
        except ValueError:
            self.show_popup("Error", "Password length must be a number")
            return
        if length < 8 or length > 32:
            self.show_popup("Error", "Password length must be between 8 and 32 characters")
            return
        
        chars = ""
        if self.uppercase_check.active:
            chars += string.ascii_uppercase
        if self.lowercase_check.active:
            chars += string.ascii_lowercase
        if self.numbers_check.active:
            chars += string.digits
        if self.special_check.active:
            chars += string.punctuation
        
        if not chars:
            self.show_popup("Error", "Select at least one character type")
            return
        
        password = ''.join(secrets.choice(chars) for _ in range(length))
        self.password_input.text = password

    def add_password(self, instance):
        app = App.get_running_app()
        account = self.account_input.text.strip()
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()
        if not account or not username or not password:
            self.show_popup("Error", "All fields are required")
            return
        encrypted_password = app.fernet.encrypt(password.encode()).decode()
        app.cursor.execute("INSERT INTO passwords (user_id, account, username, password) VALUES (?, ?, ?, ?)",
                            (app.current_user[0], account, username, encrypted_password))
        app.conn.commit()
        self.load_passwords()
        self.account_input.text = ""
        self.username_input.text = ""
        self.password_input.text = ""
        self.length_input.text = "16"
        self.uppercase_check.active = True
        self.lowercase_check.active = True
        self.numbers_check.active = True
        self.special_check.active = True

    def load_passwords(self):
        app = App.get_running_app()
        self.passwords_list.clear_widgets()
        
        app.cursor.execute("SELECT * FROM passwords WHERE user_id=?", (app.current_user[0],))
        passwords = app.cursor.fetchall()
        if not passwords:
            self.passwords_list.add_widget(Label(text="No saved passwords", size_hint_y=None, height=30))
            return
        
        for row in passwords:
            account_label = Label(text=row[2], size_hint_y=None, height=30)
            username_label = Label(text=row[3], size_hint_y=None, height=30)
            options_layout = BoxLayout(spacing=10, size_hint_y=None, height=30)
            view_button = Button(text='View', size_hint_x=None, width=60, on_press=lambda x, pwd=row[4]: self.view_password(pwd))
            copy_button = Button(text='Copy', size_hint_x=None, width=60, on_press=lambda x, pwd=row[4]: self.copy_password(pwd))
            delete_button = Button(text='Delete', size_hint_x=None, width=60, on_press=lambda x, acc=row[2], usr=row[3]: self.delete_password(acc, usr))
            options_layout.add_widget(view_button)
            options_layout.add_widget(copy_button)
            options_layout.add_widget(delete_button)
            
            row_layout = BoxLayout(orientation='horizontal', spacing=10)
            row_layout.add_widget(account_label)
            row_layout.add_widget(username_label)
            row_layout.add_widget(options_layout)
            
            self.passwords_list.add_widget(row_layout)
    
    def view_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        self.show_popup("Password", password)
    
    def copy_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        Clipboard.copy(password)
        self.show_popup("Info", "Password copied to clipboard")
    
    def delete_password(self, account, username):
        app = App.get_running_app()
        app.cursor.execute("DELETE FROM passwords WHERE user_id=? AND account=? AND username=?", (app.current_user[0], account, username))
        app.conn.commit()
        self.load_passwords()

    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        popup_label = Label(text=message)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.5))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

    def view_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        self.show_popup("Password", f"Password: {password}")
    
    def copy_password(self, encrypted_password):
        app = App.get_running_app()
        password = app.fernet.decrypt(encrypted_password.encode()).decode()
        Clipboard.copy(password)
        self.show_popup("Info", "Password copied to clipboard")
    
    def delete_password(self, account, username):
        app = App.get_running_app()
        app.cursor.execute("DELETE FROM passwords WHERE user_id=? AND account=? AND username=?", (app.current_user[0], account, username))
        app.conn.commit()
        self.load_passwords()

    def logout(self, instance):
        self.show_logout_confirmation()

    def show_logout_confirmation(self):
        content = BoxLayout(orientation='vertical', padding=20, spacing=10)
        content.add_widget(Label(text="Are you sure you want to logout?"))
        
        buttons = BoxLayout(spacing=10)
        yes_button = Button(text='Yes', size_hint_y=None, height=40)
        no_button = Button(text='No', size_hint_y=None, height=40)
        buttons.add_widget(yes_button)
        buttons.add_widget(no_button)
        content.add_widget(buttons)
        
        popup = Popup(title="Logout Confirmation", content=content, size_hint=(0.8, 0.5))
        
        yes_button.bind(on_press=lambda x: self.confirm_logout(popup))
        no_button.bind(on_press=popup.dismiss)
        popup.open()

    def confirm_logout(self, popup):
        popup.dismiss()
        app = App.get_running_app()
        app.current_user = None
        app.sm.current = 'login'
        
    def show_popup(self, title, message):
        popup_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        popup_label = Label(text=message)
        close_button = Button(text='Close', size_hint_y=None, height=40)
        popup_layout.add_widget(popup_label)
        popup_layout.add_widget(close_button)
        
        popup = Popup(title=title, content=popup_layout, size_hint=(0.8, 0.5))
        close_button.bind(on_press=popup.dismiss)
        popup.open()

class PasswordManagerApp(App):
    def build(self):
        self.conn = sqlite3.connect('password_manager.db')
        self.cursor = self.conn.cursor()
        self.setup_database()
        self.setup_encryption()
        self.current_user = None
        
        self.sm = ScreenManager()
        self.sm.add_widget(LoginScreen(name='login'))
        self.sm.add_widget(ManagerScreen(name='manager'))
        return self.sm

    def setup_database(self):
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS users
                            (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT)''')
        self.cursor.execute('''CREATE TABLE IF NOT EXISTS passwords
                            (id INTEGER PRIMARY KEY, user_id INTEGER, account TEXT, username TEXT, password TEXT,
                            FOREIGN KEY (user_id) REFERENCES users(id))''')
        self.conn.commit()

    def setup_encryption(self):
        try:
            with open('encryption_key.key', 'rb') as key_file:
                key = key_file.read()
        except FileNotFoundError:
            key = Fernet.generate_key()
            with open('encryption_key.key', 'wb') as key_file:
                key_file.write(key)
        self.fernet = Fernet(key)

    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

if __name__ == '__main__':
    PasswordManagerApp().run()