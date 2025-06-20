# app.py - Versão com SQLAlchemy
from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
import os

basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- Nosso Modelo de Dados ---
class Cadastro(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    companhia = db.Column(db.String(100))
    localizador = db.Column(db.String(50))
    data_da_reserva = db.Column(db.String(20))
    deadline = db.Column(db.String(20))
    criador = db.Column(db.String(100), nullable=False)

# --- ROTAS DA APLICAÇÃO ATUALIZADAS ---

@app.route('/')
def pagina_inicial():
    # Lê todos os cadastros do banco de dados
    lista_de_cadastros = Cadastro.query.all()
    return render_template('index.html', cadastros=lista_de_cadastros)

@app.route('/adicionar', methods=['GET', 'POST'])
def adicionar_cadastro():
    if request.method == 'POST':
        # Cria um novo "objeto" Cadastro com os dados do formulário
        novo_cadastro = Cadastro(
            nome=request.form['nome'],
            email=request.form['email'],
            companhia=request.form['companhia'],
            localizador=request.form['localizador'],
            data_da_reserva=request.form['data_da_reserva'],
            deadline=request.form['deadline'],
            criador=request.form['criador']
        )
        # Adiciona à sessão e salva no banco de dados
        db.session.add(novo_cadastro)
        db.session.commit()
        return redirect(url_for('pagina_inicial'))
    
    return render_template('adicionar.html')

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar_cadastro(id):
    # Encontra o cadastro pelo seu ID único. Se não encontrar, retorna erro 404.
    cadastro_para_editar = Cadastro.query.get_or_404(id)

    if request.method == 'POST':
        # Atualiza os campos do objeto com os dados do formulário
        cadastro_para_editar.nome = request.form['nome']
        cadastro_para_editar.email = request.form['email']
        cadastro_para_editar.companhia = request.form['companhia']
        cadastro_para_editar.localizador = request.form['localizador']
        cadastro_para_editar.data_da_reserva = request.form['data_da_reserva']
        cadastro_para_editar.deadline = request.form['deadline']
        cadastro_para_editar.criador = request.form['criador']
        
        # Salva as alterações no banco de dados
        db.session.commit()
        return redirect(url_for('pagina_inicial'))

    # Se for GET, mostra o formulário preenchido com os dados atuais
    return render_template('editar.html', cadastro=cadastro_para_editar)

@app.route('/deletar/<int:id>')
def deletar_cadastro(id):
    # Encontra o cadastro pelo ID
    cadastro_a_deletar = Cadastro.query.get_or_404(id)
    # Deleta e salva as alterações
    db.session.delete(cadastro_a_deletar)
    db.session.commit()
    return redirect(url_for('pagina_inicial'))

if __name__ == '__main__':
    app.run(debug=True)