# app.py com todas as funcionalidades web
import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import datetime
from functools import wraps

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
login_manager.login_message_category = "info"

# --- Modelos de Dados ---

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, nullable=False, default=False)

class Cadastro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    companhia = db.Column(db.String(100), nullable=True)
    localizador = db.Column(db.String(50), nullable=True)
    data_da_reserva = db.Column(db.String(20), nullable=True)
    deadline = db.Column(db.String(20), nullable=True)
    criador = db.Column(db.String(100), nullable=False)

class RegistroPonto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=True)
    hora_saida = db.Column(db.Time, nullable=True)
    observacao = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('registros_ponto', lazy=True))

    @property
    def total_horas(self):
        if self.hora_entrada and self.hora_saida:
            try:
                entrada_dt = datetime.datetime.combine(datetime.date.min, self.hora_entrada)
                saida_dt = datetime.datetime.combine(datetime.date.min, self.hora_saida)
                if saida_dt > entrada_dt:
                    delta = saida_dt - entrada_dt
                    total_seconds = int(delta.total_seconds())
                    hours = total_seconds // 3600
                    minutes = (total_seconds % 3600) // 60
                    return f"{hours}h {minutes:02d}m"
            except:
                return "Erro"
        return "N/A"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_admin', False):
            flash('Acesso negado. Você precisa ser um administrador para ver esta página.', 'danger')
            return redirect(url_for('pagina_inicial'))
        return f(*args, **kwargs)
    return decorated_function


# --- ROTAS DE REGISTRO DE PONTO ---

@app.route('/ponto', methods=['GET', 'POST'])
@login_required
def registro_ponto():
    if request.method == 'POST':
        data_str = request.form.get('data')
        hora_entrada_str = request.form.get('hora_entrada')
        hora_saida_str = request.form.get('hora_saida')
        observacao = request.form.get('observacao')
        registro_id = request.form.get('registro_id')

        try:
            data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
            hora_entrada = datetime.datetime.strptime(hora_entrada_str, '%H:%M').time() if hora_entrada_str else None
            hora_saida = datetime.datetime.strptime(hora_saida_str, '%H:%M').time() if hora_saida_str else None

            if registro_id:
                registro_a_editar = RegistroPonto.query.get_or_404(registro_id)
                if registro_a_editar.user_id != current_user.id:
                    flash('Não tem permissão para editar este registo.', 'danger')
                    return redirect(url_for('registro_ponto'))
                
                registro_a_editar.data = data
                registro_a_editar.hora_entrada = hora_entrada
                registro_a_editar.hora_saida = hora_saida
                registro_a_editar.observacao = observacao
                flash('Registo de ponto atualizado com sucesso!', 'success')
            else:
                ja_existe = RegistroPonto.query.filter_by(user_id=current_user.id, data=data).first()
                if ja_existe:
                    flash(f'Já existe um registo para o dia {data.strftime("%d/%m/%Y")}. Edite o registo existente na lista.', 'warning')
                else:
                    novo_registro = RegistroPonto(data=data, hora_entrada=hora_entrada, hora_saida=hora_saida, observacao=observacao, user_id=current_user.id)
                    db.session.add(novo_registro)
                    flash('Novo registo de ponto adicionado com sucesso!', 'success')
            
            db.session.commit()
        except (ValueError, TypeError) as e:
            flash(f'Erro no formato dos dados. Verifique a data e as horas. Detalhe: {e}', 'danger')

        return redirect(url_for('registro_ponto'))

    hoje = datetime.date.today()
    registros_do_utilizador = RegistroPonto.query.filter_by(user_id=current_user.id).order_by(RegistroPonto.data.desc()).all()
    
    return render_template('ponto.html', registros=registros_do_utilizador, hoje=hoje)


# --- ROTAS DA APLICAÇÃO PRINCIPAL ---

@app.route('/')
@login_required
def pagina_inicial():
    termo_busca = request.args.get('termo', '')
    criterio_busca = request.args.get('criterio', 'nome')
    query_base = Cadastro.query
    if termo_busca:
        mapa_criterios = {
            "nome": Cadastro.nome, "companhia": Cadastro.companhia, "email": Cadastro.email,
            "localizador": Cadastro.localizador, "criador": Cadastro.criador
        }
        campo_busca = mapa_criterios.get(criterio_busca)
        if campo_busca:
            query_base = query_base.filter(campo_busca.ilike(f'%{termo_busca}%'))
    lista_de_cadastros = query_base.order_by(Cadastro.id.desc()).all()
    return render_template('index.html', cadastros=lista_de_cadastros, termo_ativo=termo_busca, criterio_ativo=criterio_busca)

# <<< A FUNÇÃO QUE FALTAVA FOI REINSERIDA AQUI >>>
@app.route('/relatorio')
@login_required
def relatorio_deadlines():
    dias_str = request.args.get('dias', '7')
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


# --- ROTAS CRUD (Adicionar, Editar, Deletar) ---
@app.route('/adicionar', methods=['GET', 'POST'])
@login_required
def adicionar_cadastro():
    if request.method == 'POST':
        novo_cadastro = Cadastro(nome=request.form['nome'], email=request.form['email'], companhia=request.form['companhia'], localizador=request.form['localizador'], data_da_reserva=request.form['data_da_reserva'], deadline=request.form['deadline'], criador=current_user.username)
        db.session.add(novo_cadastro)
        db.session.commit()
        flash('Cadastro adicionado com sucesso!', 'success')
        return redirect(url_for('pagina_inicial'))
    return render_template('adicionar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
@login_required
def editar_cadastro(id):
    cadastro_para_editar = Cadastro.query.get_or_404(id)
    if request.method == 'POST':
        cadastro_para_editar.nome = request.form['nome']
        cadastro_para_editar.email = request.form['email']
        cadastro_para_editar.companhia = request.form['companhia']
        cadastro_para_editar.localizador = request.form['localizador']
        cadastro_para_editar.data_da_reserva = request.form['data_da_reserva']
        cadastro_para_editar.deadline = request.form['deadline']
        db.session.commit()
        flash('Cadastro atualizado com sucesso!', 'success')
        return redirect(url_for('pagina_inicial'))
    return render_template('editar.html', cadastro=cadastro_para_editar, id=id)

@app.route('/deletar/<int:id>')
@login_required
def deletar_cadastro(id):
    cadastro_a_deletar = Cadastro.query.get_or_404(id)
    db.session.delete(cadastro_a_deletar)
    db.session.commit()
    flash('Cadastro deletado com sucesso!', 'warning')
    return redirect(url_for('pagina_inicial'))

# --- ROTAS DE ADMINISTRAÇÃO ---
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_users():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Este nome de usuário já existe. Por favor, escolha outro.', 'danger')
        elif not password:
            flash('O campo de senha não pode estar vazio.', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
            new_user = User(username=username, password=hashed_password, is_admin=False)
            db.session.add(new_user)
            db.session.commit()
            flash(f'Usuário "{username}" criado com sucesso!', 'success')
        return redirect(url_for('manage_users'))
    all_users = User.query.order_by(User.id).all()
    return render_template('admin_users.html', users=all_users)

# --- ROTAS DE AUTENTICAÇÃO ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('pagina_inicial'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and bcrypt.check_password_hash(user.password, request.form.get('password')):
            login_user(user)
            return redirect(url_for('pagina_inicial'))
        else:
            flash('Usuário ou senha inválida. Tente novamente.', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Você foi desconectado com sucesso.', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    # Bloco para criar a base de dados se não existir.
    # Para uma aplicação em produção, isto seria gerido por migrations.
    with app.app_context():
        db.create_all()
    app.run(debug=True)
