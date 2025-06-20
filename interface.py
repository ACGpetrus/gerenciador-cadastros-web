# Código final completo com todas as colunas na Treeview
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import simpledialog
import json
import datetime

# --- Lógica do Programa ---
NOME_ARQUIVO = "dados.json"

def carregar_dados():
    try:
        with open(NOME_ARQUIVO, 'r', encoding='utf-8') as arquivo:
            return json.load(arquivo)
    except FileNotFoundError:
        return []

def salvar_dados(cadastros):
    with open(NOME_ARQUIVO, 'w', encoding='utf-8') as arquivo:
        json.dump(cadastros, arquivo, indent=4)

# --- Funções de Evento (Handlers) ---

def popular_lista(dados_para_mostrar=None):
    for item in tree.get_children():
        tree.delete(item)
    
    cadastros = dados_para_mostrar if dados_para_mostrar is not None else carregar_dados()
    cadastros_originais = carregar_dados()
    
    for cadastro in cadastros:
        try:
            indice_original = cadastros_originais.index(cadastro)
            # AGORA PEGAMOS TODOS OS DADOS PARA MOSTRAR NA TABELA
            valores_para_inserir = (
                cadastro.get('nome', ''),
                cadastro.get('email', ''),
                cadastro.get('companhia', ''),
                cadastro.get('localizador', ''),
                cadastro.get('data_da_reserva', cadastro.get('data_emissao', '')),
                cadastro.get('deadline', ''),
                cadastro.get('criador', 'N/D')
            )
            tree.insert("", tk.END, iid=indice_original, values=valores_para_inserir)
        except ValueError:
            continue

def adicionar_cadastro():
    # ... (código sem alteração)
    nome = entry_nome.get(); criador = entry_criador.get()
    if not nome or not criador:
        messagebox.showwarning("Atenção", "Os campos 'Nome Completo' e 'Criador' são obrigatórios.")
        return
    cadastros = carregar_dados()
    novo_cadastro = {"nome": nome, "email": entry_email.get(), "companhia": entry_companhia.get(), "localizador": entry_localizador.get(), "data_da_reserva": entry_data_reserva.get(), "deadline": entry_deadline.get(), "criador": criador}
    cadastros.append(novo_cadastro)
    salvar_dados(cadastros)
    messagebox.showinfo("Sucesso", "Cadastro adicionado com sucesso!")
    limpar_formulario()
    popular_lista()

def deletar_cadastro():
    # ... (código sem alteração)
    selecionado = tree.selection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Por favor, selecione um cadastro para deletar.")
        return
    if messagebox.askyesno("Confirmar Deleção", "Tem certeza que deseja deletar o cadastro selecionado?"):
        indice_selecionado = int(selecionado[0])
        cadastros = carregar_dados()
        cadastros.pop(indice_selecionado)
        salvar_dados(cadastros)
        popular_lista()
        messagebox.showinfo("Sucesso", "Cadastro deletado.")

def carregar_para_edicao():
    # ... (código sem alteração)
    selecionado = tree.selection()
    if not selecionado:
        messagebox.showwarning("Atenção", "Por favor, selecione um cadastro para editar.")
        return
    limpar_formulario()
    indice_selecionado = int(selecionado[0])
    cadastros = carregar_dados()
    cadastro = cadastros[indice_selecionado]
    entry_nome.insert(0, cadastro.get('nome', '')); entry_email.insert(0, cadastro.get('email', ''))
    entry_companhia.insert(0, cadastro.get('companhia', '')); entry_localizador.insert(0, cadastro.get('localizador', ''))
    entry_data_reserva.insert(0, cadastro.get('data_da_reserva', cadastro.get('data_emissao', '')))
    entry_deadline.insert(0, cadastro.get('deadline', '')); entry_criador.insert(0, cadastro.get('criador', ''))
    global indice_em_edicao
    indice_em_edicao = indice_selecionado

def salvar_edicao():
    # ... (código sem alteração)
    global indice_em_edicao
    if indice_em_edicao is None: return
    cadastros = carregar_dados()
    cadastro_editado = {"nome": entry_nome.get(), "email": entry_email.get(), "companhia": entry_companhia.get(), "localizador": entry_localizador.get(), "data_da_reserva": entry_data_reserva.get(), "deadline": entry_deadline.get(), "criador": entry_criador.get()}
    cadastros[indice_em_edicao] = cadastro_editado
    salvar_dados(cadastros)
    messagebox.showinfo("Sucesso", "Cadastro atualizado com sucesso!")
    limpar_formulario()
    popular_lista()
    indice_em_edicao = None

def limpar_formulario():
    # ... (código sem alteração)
    entry_nome.delete(0, tk.END); entry_email.delete(0, tk.END)
    entry_companhia.delete(0, tk.END); entry_localizador.delete(0, tk.END)
    entry_data_reserva.delete(0, tk.END); entry_deadline.delete(0, tk.END)
    entry_criador.delete(0, tk.END)
    global indice_em_edicao
    indice_em_edicao = None
    entry_nome.focus()
    
def abrir_janela_relatorio():
    # ... (código sem alteração)
    dias_a_verificar = simpledialog.askinteger("Relatório de Deadlines", "Quantos dias para frente você quer verificar?", parent=janela, minvalue=1, maxvalue=365)
    if dias_a_verificar is None: return
    janela_relatorio = tk.Toplevel(janela)
    janela_relatorio.title(f"Relatório: Deadlines dos Próximos {dias_a_verificar} Dias")
    janela_relatorio.geometry("500x400")
    texto_relatorio = tk.Text(janela_relatorio, wrap='word')
    texto_relatorio.pack(fill="both", expand=True, padx=10, pady=10)
    hoje = datetime.date.today()
    proximos_cadastros = []
    cadastros = carregar_dados()
    for cadastro in cadastros:
        try:
            deadline_date = datetime.datetime.strptime(cadastro['deadline'], "%d/%m/%Y").date()
            diferenca_dias = (deadline_date - hoje).days
            if 0 <= diferenca_dias <= dias_a_verificar:
                proximos_cadastros.append((cadastro, diferenca_dias))
        except (ValueError, TypeError): continue
    if not proximos_cadastros: texto_relatorio.insert("1.0", f"Nenhum cadastro com deadline nos próximos {dias_a_verificar} dias.")
    else:
        proximos_cadastros.sort(key=lambda item: item[1])
        report_string = f"--- Deadlines para os Próximos {dias_a_verificar} Dias ---\n\n"
        for cadastro, dias_restantes in proximos_cadastros:
            report_string += f"Faltam {dias_restantes} dias - Deadline: {cadastro['deadline']}\n"; report_string += f"  Nome: {cadastro['nome']}\n"
            report_string += f"  Localizador: {cadastro['localizador']}\n"; report_string += "--------------------------------------\n\n"
        texto_relatorio.insert("1.0", report_string)
    texto_relatorio.config(state="disabled")

def filtrar_lista(event=None):
    # ... (código sem alteração)
    termo_busca = entry_busca.get()
    criterio_selecionado_label = combo_busca.get()
    mapa_criterios = {"Nome Completo": "nome", "Companhia": "companhia", "Email": "email", "Localizador": "localizador", "Criador": "criador"}
    chave_busca = mapa_criterios.get(criterio_selecionado_label)
    if not chave_busca: return
    cadastros = carregar_dados()
    if not termo_busca: popular_lista(cadastros)
    else:
        encontrados = []
        for cadastro in cadastros:
            valor_do_campo = str(cadastro.get(chave_busca, ''))
            if termo_busca.lower() in valor_do_campo.lower():
                encontrados.append(cadastro)
        popular_lista(encontrados)

# --- Configuração da Interface Gráfica ---
janela = tk.Tk()
janela.title("Meu Gerenciador de Cadastros")
janela.geometry("1024x768") # Aumentei o tamanho da janela para caber tudo

indice_em_edicao = None

frame_formulario = ttk.LabelFrame(janela, text="Adicionar / Editar Cadastro")
frame_formulario.pack(fill="x", padx=10, pady=10)
#...(código do formulário sem alterações)...
labels_text = ["Nome Completo:", "Email:", "Companhia:", "Localizador:", "Data da Reserva:", "Deadline:", "Criador:"]
for i, text in enumerate(labels_text):
    ttk.Label(frame_formulario, text=text).grid(row=i, column=0, padx=5, pady=5, sticky="w")
entry_nome = ttk.Entry(frame_formulario, width=50); entry_email = ttk.Entry(frame_formulario, width=50)
entry_companhia = ttk.Entry(frame_formulario, width=50); entry_localizador = ttk.Entry(frame_formulario, width=50)
entry_data_reserva = ttk.Entry(frame_formulario, width=50); entry_deadline = ttk.Entry(frame_formulario, width=50)
entry_criador = ttk.Entry(frame_formulario, width=50)
entry_nome.grid(row=0, column=1, padx=5, pady=5, sticky="w"); entry_email.grid(row=1, column=1, padx=5, pady=5, sticky="w")
entry_companhia.grid(row=2, column=1, padx=5, pady=5, sticky="w"); entry_localizador.grid(row=3, column=1, padx=5, pady=5, sticky="w")
entry_data_reserva.grid(row=4, column=1, padx=5, pady=5, sticky="w"); entry_deadline.grid(row=5, column=1, padx=5, pady=5, sticky="w")
entry_criador.grid(row=6, column=1, padx=5, pady=5, sticky="w")
frame_botoes_form = ttk.Frame(frame_formulario)
frame_botoes_form.grid(row=7, column=0, columnspan=2, pady=10)
ttk.Button(frame_botoes_form, text="Adicionar Novo", command=adicionar_cadastro).pack(side="left", padx=5)
ttk.Button(frame_botoes_form, text="Salvar Edição", command=salvar_edicao).pack(side="left", padx=5)
ttk.Button(frame_botoes_form, text="Limpar Formulário", command=limpar_formulario).pack(side="left", padx=5)

frame_lista = ttk.LabelFrame(janela, text="Cadastros Salvos")
frame_lista.pack(fill="both", expand=True, padx=10, pady=10)
frame_busca = ttk.Frame(frame_lista)
frame_busca.pack(pady=5, padx=5, fill='x')
#...(código da busca sem alterações)...
ttk.Label(frame_busca, text="Buscar por:").pack(side="left", padx=5)
criterios_busca = ["Nome Completo", "Companhia", "Email", "Localizador", "Criador"]
combo_busca = ttk.Combobox(frame_busca, values=criterios_busca, state="readonly")
combo_busca.pack(side="left", padx=5)
combo_busca.set("Nome Completo")
entry_busca = ttk.Entry(frame_busca, width=40)
entry_busca.pack(side="left", padx=5, fill='x', expand=True)
entry_busca.bind("<KeyRelease>", filtrar_lista)
combo_busca.bind("<<ComboboxSelected>>", filtrar_lista)

# --- AQUI ESTÃO AS PRINCIPAIS MUDANÇAS ---

# 1. Definição das Colunas ATUALIZADA
colunas = ('nome', 'email', 'companhia', 'localizador', 'data_reserva', 'deadline', 'criador')
tree = ttk.Treeview(frame_lista, columns=colunas, show='headings')

# 2. Criação dos Cabeçalhos ATUALIZADA
tree.heading('nome', text='Nome Completo')
tree.heading('email', text='Email')
tree.heading('companhia', text='Companhia')
tree.heading('localizador', text='Localizador')
tree.heading('data_reserva', text='Data da Reserva')
tree.heading('deadline', text='Deadline')
tree.heading('criador', text='Criador')

# 3. Ajuste de Largura das Colunas ATUALIZADO
tree.column('nome', width=180, stretch=tk.YES)
tree.column('email', width=150, stretch=tk.YES)
tree.column('companhia', width=120, stretch=tk.YES)
tree.column('localizador', width=80, stretch=tk.NO)
tree.column('data_reserva', width=100, stretch=tk.NO)
tree.column('deadline', width=100, stretch=tk.NO)
tree.column('criador', width=100, stretch=tk.NO)

# -----------------------------------------------

tree.pack(side="left", fill="both", expand=True)
scrollbar = ttk.Scrollbar(frame_lista, orient="vertical", command=tree.yview)
scrollbar.pack(side="right", fill="y")
tree.configure(yscrollcommand=scrollbar.set)

frame_botoes_lista = ttk.Frame(janela)
frame_botoes_lista.pack(pady=10)
#...(código dos botões sem alterações)...
ttk.Button(frame_botoes_lista, text="Carregar para Editar", command=carregar_para_edicao).pack(side="left", padx=10)
ttk.Button(frame_botoes_lista, text="Deletar Selecionado", command=deletar_cadastro).pack(side="left", padx=10)
ttk.Button(frame_botoes_lista, text="Relatório de Deadlines", command=abrir_janela_relatorio).pack(side="left", padx=10)

popular_lista()
janela.mainloop()