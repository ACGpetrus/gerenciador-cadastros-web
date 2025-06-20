# Importamos as bibliotecas json e a nova, datetime
import json
import datetime

# O resto das suas funções permanece igual...
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

def buscar_por_inicio_do_nome(termo_busca):
    encontrados = []
    for cadastro in cadastros:
        if cadastro['nome'].lower().startswith(termo_busca.lower()):
            encontrados.append(cadastro)
    return encontrados

def adicionar_cadastro():
    # Esta função não precisa de alterações
    print("\n--- Adicionar Novo Cadastro ---")
    termo_busca = input("Digite o início do nome para verificar se já existe: ")
    if not termo_busca:
        print("Busca cancelada.")
        return
    encontrados = buscar_por_inicio_do_nome(termo_busca)
    if encontrados:
        print("\n--- Encontramos os seguintes cadastros parecidos: ---")
        for cadastro in encontrados:
            print(f"  - Nome: {cadastro['nome']}, Localizador: {cadastro['localizador']}")
        print("-------------------------------------------------------")
        continuar = input("Você ainda deseja continuar e criar um NOVO cadastro? (s/n): ").lower()
        if continuar != 's':
            print("Operação de cadastro cancelada pelo usuário.")
            return
    print("\nOk, vamos prosseguir com o novo cadastro.")
    nome_completo = input(f"Digite o Nome COMPLETO (ou pressione Enter para usar '{termo_busca}'): ")
    if not nome_completo:
        nome_completo = termo_busca
    email = input("Email: ")
    companhia = input("Companhia: ")
    localizador = input("Localizador: ")
    data_emissao = input("Data de Emissão (ex: DD/MM/AAAA): ")
    deadline = input("Deadline (ex: DD/MM/AAAA): ")
    novo_cadastro = {"nome": nome_completo, "email": email, "companhia": companhia, "localizador": localizador, "data_emissao": data_emissao, "deadline": deadline}
    cadastros.append(novo_cadastro)
    salvar_dados(cadastros)
    print(f"\nCadastro para '{nome_completo}' adicionado e salvo com sucesso!")

def listar_cadastros():
    # Esta função não precisa de alterações
    print("\n--- Lista de Cadastros ---")
    if not cadastros:
        print("Nenhum cadastro encontrado.")
        return False
    for i, cadastro in enumerate(cadastros):
        print(f"--- Cadastro #{i + 1} ---")
        print(f"  Nome Completo:   {cadastro['nome']}")
        print(f"  Email:           {cadastro['email']}")
        print(f"  Companhia:       {cadastro['companhia']}")
        print(f"  Localizador:     {cadastro['localizador']}")
        print(f"  Data de Emissão: {cadastro['data_emissao']}")
        print(f"  Deadline:        {cadastro['deadline']}")
        print("-" * 25)
    return True

def deletar_cadastro():
    # Esta função não precisa de alterações
    print("\n--- Deletar Cadastro ---")
    if not listar_cadastros():
        return
    try:
        num_para_deletar = int(input("\nDigite o número do cadastro que você deseja deletar: "))
        if 1 <= num_para_deletar <= len(cadastros):
            indice = num_para_deletar - 1
            cadastro_a_deletar = cadastros[indice]
            print(f"\nVocê selecionou para deletar: '{cadastro_a_deletar['nome']}'")
            confirmacao = input("Tem certeza? Esta ação não pode ser desfeita. (s/n): ").lower()
            if confirmacao == 's':
                item_deletado = cadastros.pop(indice)
                salvar_dados(cadastros)
                print(f"Cadastro de '{item_deletado['nome']}' foi deletado com sucesso.")
            else:
                print("Deleção cancelada.")
        else:
            print("Número inválido. Nenhum cadastro com este número.")
    except ValueError:
        print("Entrada inválida. Por favor, digite apenas o número.")

def atualizar_cadastro():
    # Esta função não precisa de alterações
    print("\n--- Atualizar/Editar Cadastro ---")
    if not listar_cadastros():
        return
    try:
        num_para_editar = int(input("\nDigite o número do cadastro que você deseja editar: "))
        if 1 <= num_para_editar <= len(cadastros):
            indice = num_para_editar - 1
            cadastro_a_editar = cadastros[indice]
            print("\nEditando o cadastro de:", cadastro_a_editar['nome'])
            print("Deixe o campo em branco e pressione Enter para manter o valor atual.")
            nome_novo = input(f"Nome Completo (atual: {cadastro_a_editar['nome']}): ")
            email_novo = input(f"Email (atual: {cadastro_a_editar['email']}): ")
            companhia_nova = input(f"Companhia (atual: {cadastro_a_editar['companhia']}): ")
            localizador_novo = input(f"Localizador (atual: {cadastro_a_editar['localizador']}): ")
            data_emissao_nova = input(f"Data de Emissão (atual: {cadastro_a_editar['data_emissao']}): ")
            deadline_novo = input(f"Deadline (atual: {cadastro_a_editar['deadline']}): ")
            if nome_novo: cadastro_a_editar['nome'] = nome_novo
            if email_novo: cadastro_a_editar['email'] = email_novo
            if companhia_nova: cadastro_a_editar['companhia'] = companhia_nova
            if localizador_novo: cadastro_a_editar['localizador'] = localizador_novo
            if data_emissao_nova: cadastro_a_editar['data_emissao'] = data_emissao_nova
            if deadline_novo: cadastro_a_editar['deadline'] = deadline_novo
            salvar_dados(cadastros)
            print("\nCadastro atualizado com sucesso!")
        else:
            print("Número inválido. Nenhum cadastro com este número.")
    except ValueError:
        print("Entrada inválida. Por favor, digite apenas o número.")

# --- NOSSA NOVA FUNÇÃO DE RELATÓRIO ---
def relatorio_proximos_deadlines():
    """Mostra um relatório de cadastros cujo deadline está nos próximos 7 dias."""
    print("\n--- Relatório: Deadlines dos Próximos 7 Dias ---")
    
    # Pega a data de hoje, sem as horas.
    hoje = datetime.date.today()
    
    # Uma lista para guardar os cadastros que correspondem ao critério.
    proximos_cadastros = []
    
    for cadastro in cadastros:
        try:
            # Converte a string do deadline em um objeto de data do Python.
            # %d = dia, %m = mês, %Y = ano com 4 dígitos.
            deadline_date = datetime.datetime.strptime(cadastro['deadline'], "%d/%m/%Y").date()
            
            # Calcula a diferença em dias entre o deadline e hoje.
            diferenca_dias = (deadline_date - hoje).days
            
            # Se a diferença for entre 0 (hoje) e 7 (próxima semana), é um resultado!
            if 0 <= diferenca_dias <= 7:
                # Adiciona o cadastro e a quantidade de dias restantes à nossa lista de resultados.
                proximos_cadastros.append((cadastro, diferenca_dias))
                
        except (ValueError, TypeError):
            # Se o campo 'deadline' estiver vazio ou em um formato incorreto, ignora e continua.
            continue
            
    if not proximos_cadastros:
        print("Nenhum cadastro com deadline nos próximos 7 dias.")
    else:
        # Ordena a lista pela quantidade de dias restantes (do menor para o maior).
        proximos_cadastros.sort(key=lambda item: item[1])
        
        for cadastro, dias_restantes in proximos_cadastros:
            print(f"\nFaltam {dias_restantes} dias - Deadline: {cadastro['deadline']}")
            print(f"  Nome: {cadastro['nome']}")
            print(f"  Localizador: {cadastro['localizador']}")
            print("-" * 30)

# --- Loop Principal ATUALIZADO ---
cadastros = carregar_dados()
print(f"Bem-vindo! {len(cadastros)} cadastro(s) carregado(s).")

while True:
    print("\nO que você deseja fazer?")
    print("1. Adicionar novo cadastro")
    print("2. Listar todos os cadastros")
    print("3. Atualizar/Editar cadastro") # Reordenei para agrupar CRUD
    print("4. Deletar cadastro")
    print("5. Relatório de Próximos Deadlines") # Nova opção
    print("6. Sair") # 'Sair' agora é o número 6
    
    escolha = input("Digite o número da sua escolha: ")
    
    if escolha == '1':
        adicionar_cadastro()
    elif escolha == '2':
        listar_cadastros()
    elif escolha == '3':
        atualizar_cadastro()
    elif escolha == '4':
        deletar_cadastro()
    elif escolha == '5':
        relatorio_proximos_deadlines() # Chama a nova função
    elif escolha == '6':
        print("Até logo!")
        break
    else:
        print("Opção inválida. Por favor, tente novamente.")