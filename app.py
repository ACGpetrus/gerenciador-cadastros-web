# app.py com todas as funcionalidades web
import os
from flask import Flask, render_template, request, redirect, url_for, flash, Response
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
import datetime
from functools import wraps
from sqlalchemy import extract
from weasyprint import HTML

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
    # ... (código existente, sem alterações)
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=True)
    companhia = db.Column(db.String(100), nullable=True)
    localizador = db.Column(db.String(50), nullable=True)
    data_da_reserva = db.Column(db.String(20), nullable=True)
    deadline = db.Column(db.String(20), nullable=True)
    criador = db.Column(db.String(100), nullable=False)

class RegistroPonto(db.Model):
    # ... (código existente, sem alterações)
    id = db.Column(db.Integer, primary_key=True)
    data = db.Column(db.Date, nullable=False)
    hora_entrada = db.Column(db.Time, nullable=True)
    hora_inicio_almoco = db.Column(db.Time, nullable=True)
    hora_fim_almoco = db.Column(db.Time, nullable=True)
    hora_saida = db.Column(db.Time, nullable=True)
    observacao = db.Column(db.String(200), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('registros_ponto', lazy=True))
    @property
    def total_horas(self):
        if not self.hora_entrada or not self.hora_saida: return "N/A"
        try:
            hoje = datetime.date.min
            entrada_dt = datetime.datetime.combine(hoje, self.hora_entrada)
            saida_dt = datetime.datetime.combine(hoje, self.hora_saida)
            duracao_total_segundos = (saida_dt - entrada_dt).total_seconds()
            duracao_almoco_segundos = 0
            if self.hora_inicio_almoco and self.hora_fim_almoco:
                inicio_almoco_dt = datetime.datetime.combine(hoje, self.hora_inicio_almoco)
                fim_almoco_dt = datetime.datetime.combine(hoje, self.hora_fim_almoco)
                if fim_almoco_dt > inicio_almoco_dt: duracao_almoco_segundos = (fim_almoco_dt - inicio_almoco_dt).total_seconds()
            total_trabalhado_segundos = duracao_total_segundos - duracao_almoco_segundos
            if total_trabalhado_segundos < 0: total_trabalhado_segundos = 0
            hours = int(total_trabalhado_segundos // 3600)
            minutes = int((total_trabalhado_segundos % 3600) // 60)
            return f"{hours}h {minutes:02d}m"
        except Exception: return "Erro"

class Contato(db.Model):
    # ... (código existente, sem alterações)
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    telefone = db.Column(db.String(20), nullable=True)
    email = db.Column(db.String(100), nullable=True)
    observacoes = db.Column(db.String(300), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('contatos', lazy=True))

# --- MODELOS ATUALIZADOS: AJUDA ---

# NOVO MODELO para as "Áreas" ou Categorias
class CategoriaAjuda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    # A relação permite-nos aceder a `categoria.artigos` para ver todas as perguntas.
    # A opção 'cascade' apaga todos os artigos de uma categoria se a categoria for apagada.
    artigos = db.relationship('ArtigoAjuda', backref='categoria', lazy=True, cascade="all, delete-orphan")

# MODELO ATUALIZADO para os artigos, agora com uma ligação à sua categoria
class ArtigoAjuda(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    pergunta = db.Column(db.String(200), nullable=False)
    resposta = db.Column(db.Text, nullable=False)
    # A chave estrangeira que liga o artigo à sua categoria
    categoria_id = db.Column(db.Integer, db.ForeignKey('categoria_ajuda.id'), nullable=False)


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

# --- ROTAS DE PONTO E CONTATOS (Sem alterações) ---
# ... (Todo o código das outras funcionalidades permanece igual)
@app.route('/ponto', methods=['GET', 'POST'])
@login_required
def registro_ponto():
    if request.method == 'POST':
        data_str = request.form.get('data')
        hora_entrada_str = request.form.get('hora_entrada')
        hora_inicio_almoco_str = request.form.get('hora_inicio_almoco')
        hora_fim_almoco_str = request.form.get('hora_fim_almoco')
        hora_saida_str = request.form.get('hora_saida')
        observacao = request.form.get('observacao')
        registro_id = request.form.get('registro_id')
        try:
            data = datetime.datetime.strptime(data_str, '%Y-%m-%d').date()
            hora_entrada = datetime.datetime.strptime(hora_entrada_str, '%H:%M').time() if hora_entrada_str else None
            hora_inicio_almoco = datetime.datetime.strptime(hora_inicio_almoco_str, '%H:%M').time() if hora_inicio_almoco_str else None
            hora_fim_almoco = datetime.datetime.strptime(hora_fim_almoco_str, '%H:%M').time() if hora_fim_almoco_str else None
            hora_saida = datetime.datetime.strptime(hora_saida_str, '%H:%M').time() if hora_saida_str else None
            if registro_id:
                registro_a_editar = RegistroPonto.query.get_or_404(registro_id)
                if registro_a_editar.user_id != current_user.id:
                    flash('Não tem permissão para editar este registo.', 'danger')
                    return redirect(url_for('registro_ponto'))
                registro_a_editar.data = data
                registro_a_editar.hora_entrada = hora_entrada
                registro_a_editar.hora_inicio_almoco = hora_inicio_almoco
                registro_a_editar.hora_fim_almoco = hora_fim_almoco
                registro_a_editar.hora_saida = hora_saida
                registro_a_editar.observacao = observacao
                flash('Registo de ponto atualizado com sucesso!', 'success')
            else:
                ja_existe = RegistroPonto.query.filter_by(user_id=current_user.id, data=data).first()
                if ja_existe:
                    flash(f'Já existe um registo para o dia {data.strftime("%d/%m/%Y")}. Edite o registo existente na lista.', 'warning')
                else:
                    novo_registro = RegistroPonto(data=data, hora_entrada=hora_entrada, hora_inicio_almoco=hora_inicio_almoco, hora_fim_almoco=hora_fim_almoco, hora_saida=hora_saida, observacao=observacao, user_id=current_user.id)
                    db.session.add(novo_registro)
                    flash('Novo registo de ponto adicionado com sucesso!', 'success')
            db.session.commit()
        except (ValueError, TypeError) as e:
            flash(f'Erro no formato dos dados. Verifique a data e as horas. Detalhe: {e}', 'danger')
        return redirect(url_for('registro_ponto'))
    hoje = datetime.date.today()
    registros_do_utilizador = RegistroPonto.query.filter_by(user_id=current_user.id).order_by(RegistroPonto.data.desc()).all()
    return render_template('ponto.html', registros=registros_do_utilizador, hoje=hoje)

@app.route('/relatorio/ponto')
@login_required
def relatorio_ponto():
    try:
        mes = int(request.args.get('mes'))
        ano = int(request.args.get('ano'))
    except (TypeError, ValueError):
        flash('Mês e ano inválidos.', 'danger')
        return redirect(url_for('registro_ponto'))
    registros_do_mes = RegistroPonto.query.filter(RegistroPonto.user_id == current_user.id, extract('year', RegistroPonto.data) == ano, extract('month', RegistroPonto.data) == mes).order_by(RegistroPonto.data.asc()).all()
    if not registros_do_mes:
        flash(f'Nenhum registro encontrado para {mes:02d}/{ano}.', 'warning')
        return redirect(url_for('registro_ponto'))
    total_segundos_mes = 0
    for registro in registros_do_mes:
        if not registro.hora_entrada or not registro.hora_saida: continue
        hoje = datetime.date.min
        entrada_dt = datetime.datetime.combine(hoje, registro.hora_entrada)
        saida_dt = datetime.datetime.combine(hoje, registro.hora_saida)
        duracao_total_segundos = (saida_dt - entrada_dt).total_seconds()
        duracao_almoco_segundos = 0
        if registro.hora_inicio_almoco and registro.hora_fim_almoco:
            inicio_almoco_dt = datetime.datetime.combine(hoje, registro.hora_inicio_almoco)
            fim_almoco_dt = datetime.datetime.combine(hoje, registro.hora_fim_almoco)
            if fim_almoco_dt > inicio_almoco_dt: duracao_almoco_segundos = (fim_almoco_dt - inicio_almoco_dt).total_seconds()
        total_trabalhado_segundos = duracao_total_segundos - duracao_almoco_segundos
        if total_trabalhado_segundos > 0: total_segundos_mes += total_trabalhado_segundos
    h = int(total_segundos_mes // 3600)
    m = int((total_segundos_mes % 3600) // 60)
    total_geral_formatado = f"{h}h {m:02d}m"
    html_renderizado = render_template('relatorio_ponto_pdf.html', registros=registros_do_mes, mes=mes, ano=ano, usuario=current_user, total_geral=total_geral_formatado)
    pdf = HTML(string=html_renderizado).write_pdf()
    return Response(pdf, mimetype='application/pdf', headers={'Content-Disposition': 'inline; filename=relatorio_ponto.pdf'})

@app.route('/contatos', methods=['GET', 'POST'])
@login_required
def contatos():
    if request.method == 'POST':
        contato_id = request.form.get('contato_id')
        nome = request.form.get('nome')
        telefone = request.form.get('telefone')
        email = request.form.get('email')
        observacoes = request.form.get('observacoes')
        if not nome:
            flash('O campo "Nome" é obrigatório.', 'danger')
            return redirect(url_for('contatos'))
        if contato_id:
            contato_a_editar = Contato.query.get_or_404(contato_id)
            if contato_a_editar.user_id != current_user.id:
                flash('Você não tem permissão para editar este contato.', 'danger')
                return redirect(url_for('contatos'))
            contato_a_editar.nome = nome
            contato_a_editar.telefone = telefone
            contato_a_editar.email = email
            contato_a_editar.observacoes = observacoes
            flash('Contato atualizado com sucesso!', 'success')
        else:
            novo_contato = Contato(nome=nome, telefone=telefone, email=email, observacoes=observacoes, user_id=current_user.id)
            db.session.add(novo_contato)
            flash('Novo contato adicionado com sucesso!', 'success')
        db.session.commit()
        return redirect(url_for('contatos'))
    termo_busca = request.args.get('termo', '')
    criterio_busca = request.args.get('criterio', 'nome')
    query_base = Contato.query
    if termo_busca:
        mapa_criterios = {"nome": Contato.nome, "telefone": Contato.telefone, "email": Contato.email}
        campo_busca = mapa_criterios.get(criterio_busca)
        if campo_busca: query_base = query_base.filter(campo_busca.ilike(f'%{termo_busca}%'))
    contatos_filtrados = query_base.order_by(Contato.nome.asc()).all()
    return render_template('contatos.html', contatos=contatos_filtrados, termo_ativo=termo_busca, criterio_ativo=criterio_busca)

@app.route('/contato/deletar/<int:id>', methods=['POST'])
@login_required
def deletar_contato(id):
    contato_a_deletar = Contato.query.get_or_404(id)
    if contato_a_deletar.user_id != current_user.id:
        flash('Você não tem permissão para apagar este contato.', 'danger')
    else:
        db.session.delete(contato_a_deletar)
        db.session.commit()
        flash('Contato apagado com sucesso.', 'warning')
    return redirect(url_for('contatos'))

# --- ROTAS ATUALIZADAS: CENTRAL DE AJUDA ---

@app.route('/ajuda', methods=['GET', 'POST'])
@login_required
def ajuda():
    # A lógica POST é para administradores adicionarem/editarem artigos
    if request.method == 'POST':
        if not current_user.is_admin:
            flash('Você não tem permissão para realizar esta ação.', 'danger')
            return redirect(url_for('ajuda'))
        
        artigo_id = request.form.get('artigo_id')
        pergunta = request.form.get('pergunta')
        resposta = request.form.get('resposta')
        categoria_id = request.form.get('categoria_id')

        if not pergunta or not resposta or not categoria_id:
            flash('Todos os campos (Pergunta, Resposta e Área) são obrigatórios.', 'danger')
            return redirect(url_for('ajuda'))

        if artigo_id: # A editar
            artigo_a_editar = ArtigoAjuda.query.get_or_404(artigo_id)
            artigo_a_editar.pergunta = pergunta
            artigo_a_editar.resposta = resposta
            artigo_a_editar.categoria_id = categoria_id
            flash('Artigo de ajuda atualizado com sucesso!', 'success')
        else: # A criar
            novo_artigo = ArtigoAjuda(pergunta=pergunta, resposta=resposta, categoria_id=categoria_id)
            db.session.add(novo_artigo)
            flash('Novo artigo de ajuda adicionado com sucesso!', 'success')
        
        db.session.commit()
        return redirect(url_for('ajuda'))

    # A lógica GET busca todas as categorias para as passar para a página
    categorias = CategoriaAjuda.query.order_by(CategoriaAjuda.nome.asc()).all()
    return render_template('ajuda.html', categorias=categorias)


# NOVAS ROTAS para um admin gerir as categorias
@app.route('/ajuda/categoria/adicionar', methods=['POST'])
@login_required
@admin_required
def adicionar_categoria_ajuda():
    nome_categoria = request.form.get('nome_categoria')
    if nome_categoria:
        existente = CategoriaAjuda.query.filter_by(nome=nome_categoria).first()
        if not existente:
            nova_categoria = CategoriaAjuda(nome=nome_categoria)
            db.session.add(nova_categoria)
            db.session.commit()
            flash(f'Área "{nome_categoria}" criada com sucesso!', 'success')
        else:
            flash('Uma área com esse nome já existe.', 'warning')
    else:
        flash('O nome da área não pode estar vazio.', 'danger')
    return redirect(url_for('ajuda'))


@app.route('/ajuda/categoria/deletar/<int:id>', methods=['POST'])
@login_required
@admin_required
def deletar_categoria_ajuda(id):
    categoria_a_deletar = CategoriaAjuda.query.get_or_404(id)
    db.session.delete(categoria_a_deletar)
    db.session.commit()
    flash(f'Área "{categoria_a_deletar.nome}" e todas as suas perguntas foram apagadas.', 'warning')
    return redirect(url_for('ajuda'))


@app.route('/ajuda/artigo/deletar/<int:id>', methods=['POST'])
@login_required
@admin_required
def deletar_artigo_ajuda(id):
    artigo_a_deletar = ArtigoAjuda.query.get_or_404(id)
    db.session.delete(artigo_a_deletar)
    db.session.commit()
    flash('Artigo de ajuda apagado com sucesso.', 'warning')
    return redirect(url_for('ajuda'))

# --- ROTAS PRINCIPAIS, DE AUTENTICAÇÃO, ETC (Sem alterações) ---
# ... (Todo o resto do código permanece igual)
@app.route('/')
@login_required
def pagina_inicial():
    termo_busca = request.args.get('termo', '')
    criterio_busca = request.args.get('criterio', 'nome')
    query_base = Cadastro.query
    if termo_busca:
        mapa_criterios = { "nome": Cadastro.nome, "companhia": Cadastro.companhia, "email": Cadastro.email, "localizador": Cadastro.localizador, "criador": Cadastro.criador }
        campo_busca = mapa_criterios.get(criterio_busca)
        if campo_busca: query_base = query_base.filter(campo_busca.ilike(f'%{termo_busca}%'))
    lista_de_cadastros = query_base.order_by(Cadastro.id.desc()).all()
    return render_template('index.html', cadastros=lista_de_cadastros, termo_ativo=termo_busca, criterio_ativo=criterio_busca)

@app.route('/relatorio')
@login_required
def relatorio_deadlines():
    dias_str = request.args.get('dias', '7')
    try: dias = int(dias_str)
    except ValueError: dias = 7
    hoje = datetime.date.today()
    proximos_cadastros = []
    cadastros = Cadastro.query.all()
    for cadastro in cadastros:
        try:
            deadline_date = datetime.datetime.strptime(cadastro.deadline, "%d/%m/%Y").date()
            diferenca_dias = (deadline_date - hoje).days
            if 0 <= diferenca_dias <= dias: proximos_cadastros.append((cadastro, diferenca_dias))
        except (ValueError, TypeError): continue
    proximos_cadastros.sort(key=lambda item: item[1])
    return render_template('relatorio.html', cadastros_encontrados=proximos_cadastros, dias=dias)

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
    with app.app_context():
        db.create_all()
    app.run(debug=True)
