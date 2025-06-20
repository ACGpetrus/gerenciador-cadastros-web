# app.py com todas as funcionalidades web
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import datetime

# --- Configuração ---
basedir = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config['SECRET_KEY'] = 'uma-chave-secreta-muito-dificil-de-adivinhar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor, faça o login para acessar esta página."

# --- Modelos de Dados ---
# ... (classes User e Cadastro sem alterações) ...
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True); username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
class Cadastro(db.Model):
    id = db.Column(db.Integer, primary_key=True); nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100)); companhia = db.Column(db.String(100))
    localizador = db.Column(db.String(50)); data_da_reserva = db.Column(db.String(20))
    deadline = db.Column(db.String(20)); criador = db.Column(db.String(100), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
@login_required
def pagina_inicial():
    # Lógica de busca e filtro
    termo_busca = request.args.get('termo', '')
    criterio_busca = request.args.get('criterio', 'nome')
    
    query_base = Cadastro.query

    if termo_busca:
        # Mapeia o critério do formulário para o campo do modelo do banco de dados
        mapa_criterios = {
            "nome": Cadastro.nome, "companhia": Cadastro.companhia, "email": Cadastro.email,
            "localizador": Cadastro.localizador, "criador": Cadastro.criador
        }
        campo_busca = mapa_criterios.get(criterio_busca)
        
        if campo_busca:
            # O .ilike() faz uma busca 'case-insensitive' que contém o termo
            query_base = query_base.filter(campo_busca.ilike(f'%{termo_busca}%'))

    lista_de_cadastros = query_base.all()
    
    return render_template('index.html', cadastros=lista_de_cadastros, termo_ativo=termo_busca, criterio_ativo=criterio_busca)

# ROTA PARA O RELATÓRIO DE DEADLINES
@app.route('/relatorio')
@login_required
def relatorio_deadlines():
    dias_str = request.args.get('dias', '7') # Pega o número de dias da URL, padrão é 7
    try:
        dias = int(dias_str)
    except ValueError:
        dias = 7

    hoje = datetime.date.today()
    proximos_cadastros = []
    cadastros = Cadastro.query.all()
    
    for cadastro in cadastros:
        try:
            deadline_date = datetime.datetime.strptime(cadastro.deadline, "%d/%m/%Y").date()
            diferenca_dias = (deadline_date - hoje).days
            if 0 <= diferenca_dias <= dias:
                proximos_cadastros.append((cadastro, diferenca_dias))
        except (ValueError, TypeError):
            continue
    
    proximos_cadastros.sort(key=lambda item: item[1])

    return render_template('relatorio.html', cadastros_encontrados=proximos_cadastros, dias=dias)


# --- ROTAS DE AUTENTICAÇÃO E CRUD (sem alterações) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    # ... (código da função sem alteração) ...
    if current_user.is_authenticated: return redirect(url_for('pagina_inicial'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password_hash, request.form.get('password')):
            login_user(user)
            return redirect(url_for('pagina_inicial'))
        else:
            flash('Usuário ou senha inválida. Tente novamente.', 'error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    # ... (código da função sem alteração) ...
    logout_user()
    return redirect(url_for('login'))

@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cadastro():
    # ... (código da função sem alteração) ...
    if request.method == 'POST':
        novo_cadastro = Cadastro(nome=request.form['nome'], email=request.form['email'], companhia=request.form['companhia'], localizador=request.form['localizador'], data_da_reserva=request.form['data_da_reserva'], deadline=request.form['deadline'], criador=request.form['criador'])
        db.session.add(novo_cadastro); db.session.commit()
        return redirect(url_for('pagina_inicial'))
    return render_template('adicionar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cadastro(id):
    # ... (código da função sem alteração) ...
    cadastro_para_editar = Cadastro.query.get_or_404(id)
    if request.method == 'POST':
        cadastro_para_editar.nome = request.form['nome']; cadastro_para_editar.email = request.form['email']
        cadastro_para_editar.companhia = request.form['companhia']; cadastro_para_editar.localizador = request.form['localizador']
        cadastro_para_editar.data_da_reserva = request.form['data_da_reserva']; cadastro_para_editar.deadline = request.form['deadline']
        cadastro_para_editar.criador = request.form['criador']
        db.session.commit()
        return redirect(url_for('pagina_inicial'))
    return render_template('editar.html', cadastro=cadastro_para_editar, id=id)

@app.route('/deletar/<int:id>')
@login_required
def deletar_cadastro(id):
    # ... (código da função sem alteração) ...
    cadastro_a_deletar = Cadastro.query.get_or_404(id)
    db.session.delete(cadastro_a_deletar); db.session.commit()
    return redirect(url_for('pagina_inicial'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)