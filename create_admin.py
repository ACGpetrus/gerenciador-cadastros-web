# Ficheiro: create_admin.py
from app import app, db, bcrypt, User
import getpass

def create_first_admin():
    with app.app_context():
        if User.query.first() is not None:
            print("ERRO: Já existem utilizadores na base de dados.")
            return

        print("--- A criar o primeiro utilizador Administrador ---")
        username = input("Digite o nome de utilizador para o admin: ")
        password = getpass.getpass("Digite a palavra-passe para o admin: ")

        if not username or not password:
            print("Nome de utilizador e palavra-passe não podem ser vazios.")
            return

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        admin_user = User(username=username, password=hashed_password, is_admin=True)

        db.session.add(admin_user)
        db.session.commit()

        print(f"\nSucesso! Utilizador administrador '{username}' foi criado.")

if __name__ == '__main__':
    create_first_admin()