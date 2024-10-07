import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime, timedelta
import logging
import asyncio

# Configuração do logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

# Função para buscar os resultados da API
def fetch_resultados():
    data_escolhida = datetime.now() - timedelta(days=1)  # Pegar o dia anterior
    data_formatada = data_escolhida.strftime('%Y-%m-%d')  # Formata para AAAA-MM-DD

    url = f'https://api-aviator-cb5db3cad4c0.herokuapp.com/history-filter-odd?date={data_formatada}&numberVelas=10000&betHouse=Aposta_ganha&filter=10'

    try:
        response = requests.get(url)
        response.raise_for_status()  # Verifica erros na requisição
        return response.json()  # Retorna o JSON da API
    except requests.exceptions.RequestException as e:
        logging.error(f'Erro ao buscar resultados: {e}')
        return []

# Função para responder ao comando /consultar
async def consultar_resultados(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    
    # Mensagem inicial de consulta
    await context.bot.send_message(chat_id=chat_id, text="Consultando resultados...")

    resultados = fetch_resultados()  # Busca os resultados
    logging.info(f'Resultados da API: {resultados}')  # Log dos resultados da API

    if not resultados:
        await context.bot.send_message(chat_id=chat_id, text="Nenhum resultado encontrado.")
        return

    agora = datetime.now()

    # Filtra resultados futuros em relação à hora atual
    resultados_futuros = [item for item in resultados if item['hour'] > agora.strftime('%H:%M:%S')]

    # Exibe os horários previstos se existirem
    if resultados_futuros:
        ultimo_resultado = resultados_futuros[-1]  # Último horário futuro
        horario_evento = datetime.strptime(ultimo_resultado['hour'], '%H:%M:%S')

        horarios_previstos = [
            horario_evento - timedelta(seconds=65),  # -1 min e 5 seg
            horario_evento,  # Horário original
            horario_evento + timedelta(seconds=63)  # +1 min e 3 seg
        ]

        # Formata e envia os horários previstos ao usuário
        mensagem = "Horários previstos de velas rosas:\n"
        mensagem += "\n".join(horario.strftime('%H:%M:%S') for horario in horarios_previstos)

        # Hora atual de Brasília
        hora_atual_brasilia = (agora + timedelta(hours=-3)).strftime('%H:%M:%S')  # Ajusta para Brasília
        mensagem += f"\n\nHorário atual de Brasília: {hora_atual_brasilia}"

        # Enviar mensagem com horários
        await context.bot.send_message(chat_id=chat_id, text=mensagem)
    else:
        await context.bot.send_message(chat_id=chat_id, text="Nenhum horário futuro encontrado.")

# Função para responder a mensagens de texto
async def respond_oi(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.message.chat_id
    # Responde ao usuário
    mensagem = "Como posso ajudar?"
    msg = await context.bot.send_message(chat_id=chat_id, text=mensagem)

    # Aguarda 5 segundos e apaga a mensagem
    await asyncio.sleep(5)
    await context.bot.delete_message(chat_id=chat_id, message_id=msg.message_id)

# Função principal para iniciar o bot
async def main(event, context):
    # Substitua pelo seu token do bot
    TOKEN = '7359248793:AAEOyPPaHPZvEICuHXtzlgViUO3VP-Ubv7U'

    application = Application.builder().token(TOKEN).build()

    # Handler para o comando /consultar
    application.add_handler(CommandHandler("consultar", consultar_resultados))

    # Handler para responder "oi"
    application.add_handler(MessageHandler(filters.TEXT & filters.regex(r'(?i)oi'), respond_oi))

    # Inicia o bot com polling
    await application.initialize()
    await application.start_polling()

    return "Bot está rodando!"

# Chamada para execução da função principal
if __name__ == '__main__':
    import os
    import sys
    import asyncio

    # Necessário para rodar no ambiente do Vercel
    asyncio.run(main(None, None))
