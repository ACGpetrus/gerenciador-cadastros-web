# Versão final do script de migração, que lida com campos ausentes.
from app import app, db, Cadastro
import json

print("Lendo dados do dados.json...")
with open('dados.json', 'r', encoding='utf-8') as f:
    dados_json = json.load(f)
print(f"Encontrados {len(dados_json)} registros no arquivo JSON.")

with app.app_context():
    print("Iniciando a migração para o banco de dados...")
    registros_migrados = 0
    
    for i, cadastro_dict in enumerate(dados_json):
        # A única verificação agora é se o nome existe.
        if not cadastro_dict.get('nome'):
            print(f"AVISO: Pulando registro #{i+1} por não ter um nome: {cadastro_dict}")
            continue
        
        # Lógica inteligente: Pega o criador. Se não existir, usa 'MIGRADO' como padrão.
        criador_valor = cadastro_dict.get('criador', 'MIGRADO')
        # Se mesmo existindo, o valor for vazio, também usa 'MIGRADO'.
        if not criador_valor:
            criador_valor = 'MIGRADO'
            
        novo_cadastro = Cadastro(
            nome=cadastro_dict.get('nome'),
            email=cadastro_dict.get('email'),
            companhia=cadastro_dict.get('companhia'),
            localizador=cadastro_dict.get('localizador'),
            data_da_reserva=cadastro_dict.get('data_da_reserva', cadastro_dict.get('data_emissao')),
            deadline=cadastro_dict.get('deadline'),
            criador=criador_valor  # Usa o valor que definimos
        )
        db.session.add(novo_cadastro)
        registros_migrados += 1

    db.session.commit()

print(f"\nMigração concluída!")
print(f"{registros_migrados} de {len(dados_json)} registros foram inseridos com sucesso no database.db.")