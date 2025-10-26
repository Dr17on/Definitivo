
## 2. `main.py`

```python
import os
import logging
import json
import asyncio
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, ConversationHandler, MessageHandler, filters

# Configuración para Replit
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Estados para conversaciones
SET_WITHDRAWAL, CONFIRM_DEPOSIT, BET_AMOUNT, BET_SELECTION, ADMIN_ACTION, DEPOSIT_VERIFICATION = range(6)

# Rutas para Replit
DATA_FILE = "betting_data.json"
CONFIG_FILE = "config.json"

# Obtener configuración
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return {
        "token": os.environ.get('TELEGRAM_BOT_TOKEN', 'TU_TOKEN_AQUI'),
        "admin_ids": [int(x.strip()) for x in os.environ.get('ADMIN_IDS', '123456789').split(',')],
        "min_deposit": 1,
        "min_withdrawal": 10,
        "required_bets": 5
    }

config = load_config()
TOKEN = config["8399620837:AAHtlB4mbWeAs0APLQnqG8ABQ0OX3_0now8"]
ADMIN_IDS = config["6757087193"]

# Información de depósitos
DEPOSIT_INFO = """
💳 *MÉTODOS DE DEPÓSITO*

*USDT (BEP20):*
`0x7a227a8915fccfab81d03dd3be44f14128294567`

*TON:*
`UQBvywnihfCNxZJMKYAhmWRRQ-fwGvDJc460wU20PejIMCgZ`

*Transferencia CUP (MiTransfer):*
`51602199`

*Mínimo de depósito:* 1 USD

⚠️ *Después de depositar, envía el comprobante con /verify_deposit*
"""

# Comisiones de retiro
WITHDRAWAL_FEES = {
    'usdt': 0.05,
    'ton': 0.03,
    'mitransfer': 0.02
}

# Servidor web para mantener activo el Replit
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>Bot de Apuestas Deportivas</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { color: green; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Bot de Apuestas Deportivas</h1>
                <p class="status">✅ Bot activo y funcionando</p>
                <p>Este bot está ejecutándose en Replit y gestiona apuestas deportivas.</p>
                <h3>Características:</h3>
                <ul>
                    <li>Sistema completo de apuestas</li>
                    <li>Múltiples métodos de pago</li>
                    <li>Panel de administración</li>
                    <li>Verificación de transacciones</li>
                </ul>
                <p><strong>👑 Admins configurados:</strong> {}</p>
                <p><strong>📊 Usuarios registrados:</strong> {}</p>
                <p><strong>🏈 Eventos activos:</strong> {}</p>
            </div>
        </body>
    </html>
    """.format(
        len(ADMIN_IDS),
        len(data.get('users', {})),
        len([e for e in data.get('events', {}).values() if e.get('status') == 'active'])
    )

def run_flask():
    app.run(host='0.0.0.0', port=8080)

def load_data():
    """Carga los datos del archivo JSON"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error cargando datos: {e}")
    
    # Datos iniciales
    datos_iniciales = {
        'users': {},
        'events': {
            '1': {
                'team1': 'Real Madrid',
                'team2': 'Barcelona',
                'league': 'La Liga',
                'date': '2024-12-15 20:00',
                'odds': {'team1': 1.85, 'draw': 3.20, 'team2': 4.00},
                'status': 'active',
                'created_by': ADMIN_IDS[0] if ADMIN_IDS else 123456789,
                'created_at': datetime.now().isoformat()
            },
            '2': {
                'team1': 'Bayern Munich',
                'team2': 'Borussia Dortmund',
                'league': 'Bundesliga',
                'date': '2024-12-16 18:30',
                'odds': {'team1': 1.70, 'draw': 3.50, 'team2': 4.50},
                'status': 'active',
                'created_by': ADMIN_IDS[0] if ADMIN_IDS else 123456789,
                'created_at': datetime.now().isoformat()
            }
        },
        'bets': {},
        'deposits': {},
        'withdrawals': {},
        'next_event_id': 3,
        'next_bet_id': 1,
        'next_deposit_id': 1
    }
    
    save_data(datos_iniciales)
    return datos_iniciales

def save_data(data_dict):
    """Guarda los datos en el archivo JSON"""
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data_dict, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error guardando datos: {e}")
        return False

# Cargar datos iniciales
data = load_data()

def is_admin(user_id):
    return user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if str(user_id) not in data['users']:
        data['users'][str(user_id)] = {
            'balance': 0.0,
            'valid_bets': 0,
            'total_bets': 0.0,
            'withdrawal_addresses': {},
            'pending_deposits': [],
            'username': update.effective_user.username or f"user_{user_id}"
        }
        save_data(data)
    
    keyboard = [
        [InlineKeyboardButton("💰 Depositar", callback_data='deposit')],
        [InlineKeyboardButton("💸 Retirar", callback_data='withdraw')],
        [InlineKeyboardButton("🏆 Eventos Deportivos", callback_data='events')],
        [InlineKeyboardButton("📊 Mis Estadísticas", callback_data='stats')],
        [InlineKeyboardButton("🔧 Configurar Retiro", callback_data='set_withdrawal')]
    ]
    
    if is_admin(user_id):
        keyboard.append([InlineKeyboardButton("👑 Panel Admin", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🏟️ *Bienvenido al Bot de Apuestas Deportivas* 🏆\n\n"
        "Usa los botones para interactuar:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

# ... (el resto del código del bot se mantiene igual que en la versión anterior)
# [Aquí iría todo el resto del código que ya tenemos para los handlers]

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data_dict = data
    user_data = data_dict['users'].get(str(user_id), {})
    data_key = query.data
    
    if data_key == 'deposit':
        await query.edit_message_text(
            DEPOSIT_INFO,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Verificar Depósito", callback_data='verify_deposit')],
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
    
    elif data_key == 'verify_deposit':
        await query.edit_message_text(
            "📤 *Verificación de Depósito*\n\n"
            "Envía los datos en este formato:\n"
            "`USDT, 50, 0x123abc..., 2024-01-01 14:30`\n\n"
            "Donde:\n"
            "- USDT: método (USDT/TON/MiTransfer)\n"
            "- 50: monto\n"
            "- 0x123abc...: hash/ID de transacción\n"
            "- 2024-01-01 14:30: fecha y hora",
            parse_mode='Markdown'
        )
        return DEPOSIT_VERIFICATION
    
    # ... (continuar con todos los demás handlers)

def main():
    # Verificar token
    if TOKEN == 'TU_TOKEN_AQUI':
        print("❌ ERROR: Configura el token del bot")
        print("En Replit: Ve a Secrets y agrega TELEGRAM_BOT_TOKEN")
        print("En local: Edita config.json o usa variables de entorno")
        return
    
    # Iniciar servidor web
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Crear aplicación de Telegram
    application = Application.builder().token(TOKEN).build()
    
    # Configurar handlers (igual que antes)
    # [Aquí iría la configuración de todos los handlers]
    
    # Iniciar bot
    print("🤖 Bot de Apuestas Deportivas iniciado")
    print(f"👑 Admins: {ADMIN_IDS}")
    print("🌐 Servidor web: http://0.0.0.0:8080")
    print("✅ Listo para recibir mensajes...")
    
    application.run_polling()

if __name__ == '__main__':
    main()
