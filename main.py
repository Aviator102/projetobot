from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler
from fastapi import FastAPI, Request
import requests
import logging
from datetime import datetime, timedelta

app = FastAPI()

# Configuração do logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# Inicializando o Application
application = ApplicationBuilder().token("7359248793:AAEOyPPaHPZvEICuHXtzlgViUO3VP-Ubv7U").build()

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

# Função para consultar previsões de velas rosas e odds > 10
async def consultar_resultados(update: Update, context) -> None:
    chat_id = update.message.chat_id
    
    # Mensagem inicial de consulta
    await context.bot.send_message(chat_id=chat_id, text="*Consultando resultados...*")

    resultados = fetch_resultados()  # Busca os resultados

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
        mensagem = "*Horários previstos de velas rosas:*\n"
        mensagem += "\n".join(horario.strftime('%H:%M:%S') for horario in horarios_previstos)

        # Hora atual de Brasília
        hora_atual_brasilia = agora.strftime('%H:%M:%S')  # Ajusta para Brasília
        mensagem += f"\n\n *Horário atual de Brasília:* {hora_atual_brasilia}"

        # Enviar mensagem com horários
        await context.bot.send_message(chat_id=chat_id, text=mensagem, parse_mode='MarkdownV2')
    else:
        await context.bot.send_message(chat_id=chat_id, text="Nenhum horário futuro encontrado.")

# Função principal para iniciar o bot
@app.on_event("startup")
async def on_startup():
    # Handler para o comando /consultar
    application.add_handler(CommandHandler("consultar", consultar_resultados))

    # Definindo webhook
    url_webhook = "https://projetobot.vercel.app/webhook"  # URL do Vercel com endpoint
    await application.bot.set_webhook(url=url_webhook)

# Endpoint webhook
@app.post("/webhook")
async def webhook_handler(request: Request):
    update = await request.json()
    update = Update.de_json(update, application.bot)
    await application.update_queue.put(update)
    return {"status": "ok"}
