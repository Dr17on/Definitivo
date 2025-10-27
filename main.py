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
SET_WITHDRAWAL, CONFIRM_DEPOSIT, BET_AMOUNT, BET_SELECTION, ADMIN_ACTION, DEPOSIT_VERIFICATION, BROADCAST_MESSAGE = range(7)

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
        "min_deposit": 50,
        "min_withdrawal": 1000,
        "required_bets": 5
    }

config = load_config()
TOKEN = config["8413502528:AAGQxu5jQicp4eEXcjQ5N_C8sbEIVVKuzhY"]
ADMIN_IDS = config["6757087193"]

# Información de canales (opcionales)
CHANNELS_INFO = {
    "main": {
        "name": "❌️Drks Bets❌️",
        "link": "https://t.me/+sKoCBrdA4KwyYmIx"
    },
    "transactions": {
        "name": "💳Depósitos y Retiros", 
        "link": "https://t.me/+I45ugeNK7lk1Zjlh"
    },
    "bets": {
        "name": "📊Apuestas Creadas",
        "link": "https://t.me/+xbixQ7wLCQ04NjYx"
    }
}

# Información de depósitos
DEPOSIT_INFO = """
💳 *MÉTODOS DE DEPÓSITO*

*Bolsa MiTransfer:*
🔢 **Número:** `51602199`

*Mínimo de depósito:* 50 CUP

⚠️ *Después de depositar, envía captura del mensaje de pago donde se vea la fecha y hora realizada*
"""

# Comisiones de retiro
WITHDRAWAL_FEES = {
    'bank': 0.02,      # 2% para transferencia bancaria
    'mitransfer': 0.0  # 0% para MiTransfer
}

# Términos y condiciones actualizados
TERMS_AND_CONDITIONS = """
📄 *TÉRMINOS Y CONDICIONES DE USO - Drks Bets*

1. *ACEPTACIÓN DE TÉRMINOS*
Al usar ❌️Drks Bets❌️, aceptas cumplir con estos términos y condiciones.

2. *ELEGIBILIDAD*
- Debes ser mayor de 18 años
- Debes residir en Cuba

3. *DEPÓSITOS Y RETIROS*
- Depósito mínimo: 50 CUP
- Retiro mínimo: 1000 CUP
- Debes completar 5 apuestas válidas antes de retirar
- Las transacciones se procesan manualmente en 24-48 horas

4. *APUESTAS*
- Las apuestas son irrevocables
- Las cuotas pueden cambiar sin previo aviso
- Drks Bets se reserva el derecho de cancelar apuestas sospechosas

5. *PRIVACIDAD*
- Tus datos personales se protegen conforme a la ley
- No compartimos información con terceros
- Las transacciones se registran para seguridad

6. *PROHIBICIONES*
- Cuentas múltiples
- Apuestas fraudulentas
- Uso de bots o automatizaciones

7. *LIMITACIÓN DE RESPONSABILIDAD*
Drks Bets no se responsabiliza por:
- Pérdidas derivadas de apuestas
- Fallos técnicos momentáneos
- Decisiones de los usuarios

8. *CANALES OFICIALES*
Te invitamos a unirte a nuestros canales oficiales para:
- Noticias y actualizaciones
- Estado de transacciones
- Apuestas creadas por usuarios

9. *CONTACTO*
Correo: darksbets@gmail.com
Soporte 24/7

*Al usar nuestros servicios, confirmas que comprendes y aceptas estos términos.*
"""

# Servidor web para mantener activo el Replit
app = Flask(__name__)

@app.route('/')
def home():
    return """
    <html>
        <head>
            <title>❌️Drks Bets❌️ - Apuestas Deportivas Cuba</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; background: #1a1a1a; color: white; }
                .container { max-width: 800px; margin: 0 auto; }
                .status { color: #00ff00; font-weight: bold; }
                .header { color: #ff0000; text-align: center; }
                .info { background: #2a2a2a; padding: 20px; border-radius: 10px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1 class="header">❌️Drks Bets❌️</h1>
                <p class="status">✅ Bot activo y funcionando</p>
                <div class="info">
                    <h3>Servicio de Apuestas Deportivas en Cuba 🇨🇺</h3>
                    <p><strong>Operaciones manuales para evitar errores</strong></p>
                    <p><strong>Soporte 24/7:</strong> darksbets@gmail.com</p>
                    <p><strong>👑 Admins:</strong> {}</p>
                    <p><strong>👥 Usuarios:</strong> {}</p>
                    <p><strong>🏈 Eventos activos:</strong> {}</p>
                </div>
            </div>
        </body>
    </html>
    """.format(
        len(ADMIN_IDS),
        len(data.get('users', {})),
        len([e for e in data.get('events', {}).values() if e.get('status') == 'active'])
    )

@app.route('/ping')
def ping():
    print('Ping recibido:', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    return 'pong'

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

async def show_terms(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los términos y condiciones"""
    await update.message.reply_text(
        TERMS_AND_CONDITIONS,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Volver al Inicio", callback_data='start')]
        ])
    )

async def show_channels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Muestra los canales oficiales"""
    channels_text = "\n".join([
        f"• [{channel_info['name']}]({channel_info['link']})"
        for channel_info in CHANNELS_INFO.values()
    ])
    
    await update.message.reply_text(
        f"📢 *CANALES OFICIALES - ❌️Drks Bets❌️*\n\n"
        f"Te invitamos a unirte a nuestros canales oficiales:\n\n"
        f"{channels_text}\n\n"
        f"✨ *Beneficios:*\n"
        f"• Noticias y actualizaciones\n"
        f"• Estado de tus transacciones\n"
        f"• Apuestas creadas por usuarios\n"
        f"• Soporte y ayuda inmediata",
        parse_mode='Markdown',
        disable_web_page_preview=True
    )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    # Registrar usuario si no existe
    if str(user_id) not in data['users']:
        data['users'][str(user_id)] = {
            'balance': 0.0,
            'valid_bets': 0,
            'total_bets': 0.0,
            'withdrawal_addresses': {},
            'pending_deposits': [],
            'username': update.effective_user.username or f"user_{user_id}",
            'joined_date': datetime.now().isoformat(),
            'first_name': update.effective_user.first_name or '',
            'last_name': update.effective_user.last_name or ''
        }
        save_data(data)
    
    await show_main_menu(update, context)

async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("💰 Depositar", callback_data='deposit')],
        [InlineKeyboardButton("💸 Retirar", callback_data='withdraw')],
        [InlineKeyboardButton("🏆 Eventos en Tiempo Real", callback_data='live_events')],
        [InlineKeyboardButton("📊 Mis Estadísticas", callback_data='stats')],
        [InlineKeyboardButton("🔧 Configurar Retiro", callback_data='set_withdrawal')],
        [InlineKeyboardButton("📢 Nuestros Canales", callback_data='our_channels')],
        [InlineKeyboardButton("📄 Términos y Condiciones", callback_data='show_terms')]
    ]
    
    if is_admin(update.effective_user.id):
        keyboard.append([InlineKeyboardButton("👑 Panel Admin", callback_data='admin_panel')])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Mensaje de bienvenida mejorado
    welcome_message = (
        "👋 *Bienvenido a ❌️Drks Bets ❌️*\n\n"
        "🏆 *Servicio de apuestas de fútbol en Cuba* 🇨🇺\n\n"
        "✨ *Características:*\n"
        "• Operaciones manuales para evitar errores\n"
        "• Atención al cliente 24/7\n"
        "• Eventos en tiempo real\n"
        "• Múltiples métodos de retiro\n\n"
        "📧 *Soporte:* darksbets@gmail.com\n\n"
        "Selecciona una opción del menú:"
    )
    
    if update.callback_query:
        await update.callback_query.edit_message_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = update.effective_user.id
    data_dict = data
    user_data = data_dict['users'].get(str(user_id), {})
    data_key = query.data
    
    if data_key == 'show_terms':
        await query.edit_message_text(
            TERMS_AND_CONDITIONS,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Volver al Inicio", callback_data='start')]
            ])
        )
        return
    
    elif data_key == 'our_channels':
        channels_text = "\n".join([
            f"• [{channel_info['name']}]({channel_info['link']})"
            for channel_info in CHANNELS_INFO.values()
        ])
        
        await query.edit_message_text(
            f"📢 *CANALES OFICIALES - ❌️Drks Bets❌️*\n\n"
            f"Te invitamos a unirte a nuestros canales oficiales:\n\n"
            f"{channels_text}\n\n"
            f"✨ *Beneficios:*\n"
            f"• Noticias y actualizaciones\n"
            f"• Estado de tus transacciones\n"
            f"• Apuestas creadas por usuarios\n"
            f"• Soporte y ayuda inmediata",
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
        return
    
    elif data_key == 'deposit':
        await query.edit_message_text(
            DEPOSIT_INFO,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📸 Enviar Comprobante", callback_data='send_receipt')],
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
    
    elif data_key == 'send_receipt':
        await query.edit_message_text(
            "📸 *Envío de Comprobante de Depósito*\n\n"
            "Por favor envía la captura de pantalla del mensaje de MiTransfer donde se vea:\n\n"
            "✅ Número de teléfono destino\n"
            "✅ Monto transferido\n"
            "✅ Fecha y hora de la transacción\n"
            "✅ Mensaje de confirmación\n\n"
            "La imagen debe ser clara y legible.",
            parse_mode='Markdown'
        )
        return DEPOSIT_VERIFICATION
    
    elif data_key == 'withdraw':
        if user_data.get('valid_bets', 0) < 5:
            await query.edit_message_text(
                f"❌ *Necesitas 5 apuestas válidas para retirar*\n"
                f"Apuestas actuales: {user_data.get('valid_bets', 0)}/5\n\n"
                f"Realiza más apuestas en eventos deportivos para cumplir con el requisito.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🏆 Eventos", callback_data='live_events')],
                    [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
                ])
            )
            return
        
        await query.edit_message_text(
            "💸 *Selecciona método de retiro:*\n\n"
            "💰 *Mínimo de retiro: 1,000 CUP*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 Transferencia Bancaria (2% fee)", callback_data='withdraw_bank')],
                [InlineKeyboardButton("📱 Bolsa MiTransfer", callback_data='withdraw_mitransfer')],
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
    
    elif data_key.startswith('withdraw_'):
        method = data_key.split('_')[1]
        context.user_data['withdraw_method'] = method
        
        if method == 'bank' and not user_data.get('withdrawal_addresses', {}).get('bank'):
            await query.edit_message_text(
                "🏦 *Configurar Transferencia Bancaria*\n\n"
                "Por favor envía tu número de tarjeta CUP:",
                parse_mode='Markdown'
            )
            return CONFIRM_DEPOSIT
        elif method == 'mitransfer' and not user_data.get('withdrawal_addresses', {}).get('mitransfer'):
            await query.edit_message_text(
                "📱 *Configurar Bolsa MiTransfer*\n\n"
                "Por favor envía tu número de teléfono cubano:",
                parse_mode='Markdown'
            )
            return CONFIRM_DEPOSIT
        
        # Si ya tiene dirección configurada
        address = user_data['withdrawal_addresses'][method]
        await query.edit_message_text(
            f"💸 *Retiro vía {'Transferencia Bancaria' if method == 'bank' else 'MiTransfer'}*\n"
            f"📍 Destino: `{address}`\n"
            f"💵 Balance disponible: ${user_data.get('balance', 0):.2f} CUP\n"
            f"📉 Comisión: {WITHDRAWAL_FEES[method]*100}%\n"
            f"💰 Mínimo: 1,000 CUP\n\n"
            "Ingresa el monto a retirar:",
            parse_mode='Markdown'
        )
        return SET_WITHDRAWAL
    
    elif data_key == 'live_events':
        # Simular eventos en tiempo real (en producción conectar con API)
        active_events = {k: v for k, v in data_dict['events'].items() if v['status'] == 'active'}
        
        # Agregar eventos en tiempo real simulados
        current_time = datetime.now()
        live_events = {}
        
        for event_id, event in active_events.items():
            event_time = datetime.strptime(event['date'], '%Y-%m-%d %H:%M')
            time_diff = (event_time - current_time).total_seconds() / 3600  # Horas hasta el evento
            
            if -2 <= time_diff <= 2:  # Eventos que están en vivo o próximos
                event_status = "🟢 EN VIVO" if time_diff <= 0 else "🟡 PRÓXIMAMENTE"
                live_events[event_id] = {**event, 'status_display': event_status}
        
        if not live_events:
            await query.edit_message_text(
                "⏳ *No hay eventos en vivo en este momento*\n\n"
                "Vuelve más tarde para ver eventos en tiempo real.",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("🔄 Actualizar", callback_data='live_events')],
                    [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
                ])
            )
            return
        
        keyboard = []
        for event_id, event in list(live_events.items())[:8]:
            keyboard.append([InlineKeyboardButton(
                f"{event['status_display']} | {event['team1']} vs {event['team2']}", 
                callback_data=f'event_{event_id}'
            )])
        keyboard.append([InlineKeyboardButton("🔄 Actualizar", callback_data='live_events')])
        keyboard.append([InlineKeyboardButton("🏠 Inicio", callback_data='start')])
        
        await query.edit_message_text(
            "⚽ *EVENTOS EN TIEMPO REAL* ⚽\n\n"
            "Selecciona un evento para apostar:",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif data_key.startswith('event_'):
        event_id = data_key.split('_')[1]
        event = data_dict['events'].get(event_id)
        if event and event['status'] == 'active':
            context.user_data['current_event'] = event_id
            
            # Determinar estado del evento
            event_time = datetime.strptime(event['date'], '%Y-%m-%d %H:%M')
            current_time = datetime.now()
            time_diff = (event_time - current_time).total_seconds() / 3600
            
            if time_diff <= 0:
                status_text = "🟢 PARTIDO EN VIVO"
            elif time_diff <= 1:
                status_text = f"🟡 COMIENZA EN {int(time_diff*60)} MIN"
            else:
                status_text = f"⏰ {event['date']}"
            
            await query.edit_message_text(
                f"{status_text}\n"
                f"🏈 *{event['team1']} vs {event['team2']}*\n"
                f"🏆 {event['league']}\n\n"
                f"*Cuotas actuales:*\n"
                f"1. {event['team1']}: {event['odds']['team1']:.2f}\n"
                f"2. Empate: {event['odds']['draw']:.2f}\n"
                f"3. {event['team2']}: {event['odds']['team2']:.2f}\n\n"
                "Selecciona tu apuesta:",
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton(f"✅ {event['team1']}", callback_data='bet_1')],
                    [InlineKeyboardButton("🤝 Empate", callback_data='bet_draw')],
                    [InlineKeyboardButton(f"✅ {event['team2']}", callback_data='bet_2')],
                    [InlineKeyboardButton("🔙 Volver", callback_data='live_events')]
                ])
            )
    
    elif data_key.startswith('bet_'):
        selection = data_key.split('_')[1]
        context.user_data['bet_selection'] = selection
        event_id = context.user_data.get('current_event')
        event = data_dict['events'].get(event_id)
        
        if selection == '1':
            odds = event['odds']['team1']
            selection_name = event['team1']
        elif selection == '2':
            odds = event['odds']['team2']
            selection_name = event['team2']
        else:
            odds = event['odds']['draw']
            selection_name = "Empate"
        
        context.user_data['current_odds'] = odds
        context.user_data['selection_name'] = selection_name
        
        await query.edit_message_text(
            f"🎯 *Apuesta Seleccionada:* {selection_name}\n"
            f"📈 *Cuotas:* {odds:.2f}\n"
            f"💰 *Balance disponible:* ${user_data.get('balance', 0):.2f} CUP\n"
            f"🏆 *Ganancia potencial:* ${user_data.get('balance', 0) * odds:.2f} CUP\n\n"
            "Ingresa el monto a apostar (mínimo 50 CUP):",
            parse_mode='Markdown'
        )
        return BET_AMOUNT
    
    elif data_key == 'stats':
        user_stats = data_dict['users'].get(str(user_id), {})
        await query.edit_message_text(
            f"📊 *Tus Estadísticas - ❌️Drks Bets❌️*\n\n"
            f"👤 Usuario: @{user_stats.get('username', 'N/A')}\n"
            f"💵 Balance: ${user_stats.get('balance', 0):.2f} CUP\n"
            f"🎯 Apuestas válidas: {user_stats.get('valid_bets', 0)}/5\n"
            f"📈 Total apostado: ${user_stats.get('total_bets', 0):.2f} CUP\n\n"
            f"🔔 *Métodos de retiro configurados:*\n"
            f"🏦 Bancario: {'✅' if user_stats.get('withdrawal_addresses', {}).get('bank') else '❌'}\n"
            f"📱 MiTransfer: {'✅' if user_stats.get('withdrawal_addresses', {}).get('mitransfer') else '❌'}",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🏠 Inicio", callback_data='start')]])
        )
    
    elif data_key == 'set_withdrawal':
        await query.edit_message_text(
            "🔧 *Configurar Método de Retiro*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("🏦 Transferencia Bancaria", callback_data='set_bank')],
                [InlineKeyboardButton("📱 Bolsa MiTransfer", callback_data='set_mitransfer')],
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
    
    elif data_key.startswith('set_'):
        method = data_key.split('_')[1]
        context.user_data['set_method'] = method
        
        method_info = {
            'bank': 'número de tarjeta CUP',
            'mitransfer': 'número de teléfono cubano'
        }
        
        await query.edit_message_text(
            f"📍 *Configurar {method.upper()}*\n\n"
            f"Envía tu {method_info[method]} para recibir retiros:",
            parse_mode='Markdown'
        )
        return CONFIRM_DEPOSIT
    
    elif data_key == 'admin_panel':
        if not is_admin(user_id):
            await query.answer("❌ No tienes permisos de administrador")
            return
        
        total_usuarios = len(data_dict['users'])
        total_balance = sum(user.get('balance', 0) for user in data_dict['users'].values())
        eventos_activos = sum(1 for event in data_dict['events'].values() if event['status'] == 'active')
        
        await query.edit_message_text(
            f"👑 *Panel de Administración - ❌️Drks Bets❌️*\n\n"
            f"📊 Estadísticas:\n"
            f"• Usuarios totales: {total_usuarios}\n"
            f"• Balance total: ${total_balance:.2f} CUP\n"
            f"• Eventos activos: {eventos_activos}\n"
            f"• Apuestas totales: {len(data_dict['bets'])}\n\n"
            f"⚙️ *Herramientas de administración:*",
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Crear Evento", callback_data='admin_create_event')],
                [InlineKeyboardButton("📋 Eventos Activos", callback_data='admin_events')],
                [InlineKeyboardButton("✅ Verificar Depósitos", callback_data='admin_verify_deposits')],
                [InlineKeyboardButton("📢 Mensaje Global", callback_data='admin_broadcast')],
                [InlineKeyboardButton("📊 Estadísticas Detalladas", callback_data='admin_stats')],
                [InlineKeyboardButton("🏠 Inicio", callback_data='start')]
            ])
        )
    
    elif data_key == 'admin_broadcast':
        if not is_admin(user_id):
            return
        
        await query.edit_message_text(
            "📢 *Enviar Mensaje Global*\n\n"
            "Envía el mensaje que quieres enviar a todos los usuarios:",
            parse_mode='Markdown'
        )
        return BROADCAST_MESSAGE

async def establecer_direccion_retiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    method = context.user_data['set_method']
    address = update.message.text.strip()
    
    if user_id in data['users']:
        if 'withdrawal_addresses' not in data['users'][user_id]:
            data['users'][user_id]['withdrawal_addresses'] = {}
        data['users'][user_id]['withdrawal_addresses'][method] = address
        save_data(data)
    
    method_name = "Transferencia Bancaria" if method == 'bank' else "MiTransfer"
    
    await update.message.reply_text(
        f"✅ *{method_name} configurado correctamente*\n\n"
        f"`{address}`\n\n"
        f"Ahora puedes realizar retiros usando este método.",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def procesar_retiro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    method = context.user_data['withdraw_method']
    
    try:
        amount = float(update.message.text)
        fee = WITHDRAWAL_FEES[method]
        net_amount = amount * (1 - fee)
        
        if amount < 1000:
            await update.message.reply_text("❌ El monto mínimo de retiro es 1,000 CUP")
            return SET_WITHDRAWAL
        
        user_data = data['users'].get(user_id, {})
        if amount > user_data.get('balance', 0):
            await update.message.reply_text("❌ Fondos insuficientes")
            return SET_WITHDRAWAL
        
        # Procesar retiro
        data['users'][user_id]['balance'] -= amount
        withdrawal_id = len(data['withdrawals']) + 1
        data['withdrawals'][str(withdrawal_id)] = {
            'user_id': user_id,
            'amount': amount,
            'net_amount': net_amount,
            'method': method,
            'address': user_data['withdrawal_addresses'][method],
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        save_data(data)
        
        # Enviar notificación al canal de transacciones (si está configurado)
        method_name = "Transferencia Bancaria" if method == 'bank' else "MiTransfer"
        
        await update.message.reply_text(
            f"✅ *Solicitud de retiro procesada*\n\n"
            f"📋 ID: #{withdrawal_id}\n"
            f"💸 Método: {method_name}\n"
            f"📤 Monto: ${amount:.2f} CUP\n"
            f"📉 Comisión: ${amount*fee:.2f} CUP\n"
            f"💰 Neto: ${net_amount:.2f} CUP\n"
            f"📍 Destino: `{user_data['withdrawal_addresses'][method]}`\n\n"
            f"El retiro será procesado manualmente en 24-48 horas.",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Formato inválido. Ingresa solo números (ej: 1500.00)")
        return SET_WITHDRAWAL

async def procesar_monto_apuesta(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    try:
        amount = float(update.message.text)
        user_data = data['users'].get(user_id, {})
        
        if amount < 50:
            await update.message.reply_text("❌ El monto mínimo de apuesta es 50 CUP")
            return BET_AMOUNT
        
        if amount > user_data.get('balance', 0):
            await update.message.reply_text("❌ Fondos insuficientes para esta apuesta")
            return BET_AMOUNT
        
        # Procesar apuesta
        event_id = context.user_data.get('current_event')
        selection = context.user_data.get('bet_selection')
        odds = context.user_data.get('current_odds')
        selection_name = context.user_data.get('selection_name')
        event = data['events'].get(event_id)
        
        # Crear apuesta
        bet_id = str(data['next_bet_id'])
        data['next_bet_id'] += 1
        
        data['bets'][bet_id] = {
            'user_id': user_id,
            'event_id': event_id,
            'event_name': f"{event['team1']} vs {event['team2']}",
            'selection': selection,
            'selection_name': selection_name,
            'amount': amount,
            'odds': odds,
            'potential_win': amount * odds,
            'timestamp': datetime.now().isoformat(),
            'status': 'active'
        }
        
        # Actualizar usuario
        data['users'][user_id]['balance'] -= amount
        data['users'][user_id]['total_bets'] = data['users'][user_id].get('total_bets', 0) + amount
        data['users'][user_id]['valid_bets'] = data['users'][user_id].get('valid_bets', 0) + 1
        
        save_data(data)
        
        await update.message.reply_text(
            f"✅ *Apuesta Confirmada*\n\n"
            f"📋 ID: #{bet_id}\n"
            f"🏈 Evento: {event['team1']} vs {event['team2']}\n"
            f"🎯 Selección: {selection_name}\n"
            f"💰 Monto: ${amount:.2f} CUP\n"
            f"📈 Cuotas: {odds:.2f}\n"
            f"🏆 Ganancia potencial: ${amount * odds:.2f} CUP\n\n"
            f"¡Buena suerte!",
            parse_mode='Markdown'
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("❌ Formato inválido. Ingresa solo números (ej: 100.50)")
        return BET_AMOUNT

async def verificar_deposito(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    
    # Verificar si es una foto
    if update.message.photo:
        # Es una captura de pantalla
        photo = update.message.photo[-1]
        file_id = photo.file_id
        
        # Guardar información del depósito
        deposit_data = {
            'method': 'MiTransfer',
            'amount': 0,  # El admin verificará el monto
            'file_id': file_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'pending'
        }
        
        # Agregar a depósitos pendientes
        if user_id in data['users']:
            if 'pending_deposits' not in data['users'][user_id]:
                data['users'][user_id]['pending_deposits'] = []
            data['users'][user_id]['pending_deposits'].append(deposit_data)
            save_data(data)
        
        await update.message.reply_text(
            f"✅ *Comprobante recibido correctamente*\n\n"
            f"📸 Hemos recibido tu captura de pantalla\n"
            f"⏰ Tu depósito será verificado manualmente\n"
            f"📞 Puede tomar hasta 24 horas\n\n"
            f"Recibirás una notificación cuando sea aprobado.",
            parse_mode='Markdown'
        )
    else:
        await update.message.reply_text(
            "❌ Por favor envía una captura de pantalla del comprobante de MiTransfer.\n"
            "La imagen debe mostrar claramente la fecha, hora y monto de la transacción."
        )
        return DEPOSIT_VERIFICATION
    
    return ConversationHandler.END

async def admin_broadcast_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("❌ No tienes permisos de administrador")
        return ConversationHandler.END
    
    message = update.message.text
    users = data['users'].keys()
    
    sent = 0
    failed = 0
    
    for user_id_str in users:
        try:
            await context.bot.send_message(
                chat_id=int(user_id_str), 
                text=f"📢 *MENSAJE IMPORTANTE - ❌️Drks Bets❌️*\n\n{message}",
                parse_mode='Markdown'
            )
            sent += 1
        except Exception as e:
            logger.error(f"Error enviando mensaje a {user_id_str}: {e}")
            failed += 1
    
    await update.message.reply_text(
        f"✅ *Mensaje global enviado*\n\n"
        f"📤 Entregados: {sent} usuarios\n"
        f"❌ Fallados: {failed} usuarios\n"
        f"📊 Total: {len(users)} usuarios en la base de datos",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def cancelar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Operación cancelada")
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Maneja errores"""
    logger.error(f"Error: {context.error}", exc_info=context.error)

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
    
    # Manejar errores
    application.add_error_handler(error_handler)
    
    # Comandos adicionales
    application.add_handler(CommandHandler("terminos", show_terms))
    application.add_handler(CommandHandler("canales", show_channels))
    
    # Conversación para retiros
    retiro_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^withdraw_')],
        states={
            SET_WITHDRAWAL: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_retiro)]
        },
        fallbacks=[CommandHandler('cancel', cancelar)]
    )
    
    # Conversación para direcciones
    direccion_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^set_')],
        states={
            CONFIRM_DEPOSIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, establecer_direccion_retiro)]
        },
        fallbacks=[CommandHandler('cancel', cancelar)]
    )
    
    # Conversación para apuestas
    apuesta_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^bet_')],
        states={
            BET_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, procesar_monto_apuesta)]
        },
        fallbacks=[CommandHandler('cancel', cancelar)]
    )
    
    # Conversación para depósitos
    deposito_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^send_receipt$')],
        states={
            DEPOSIT_VERIFICATION: [MessageHandler(filters.PHOTO | filters.TEXT, verificar_deposito)]
        },
        fallbacks=[CommandHandler('cancel', cancelar)]
    )
    
    # Conversación para broadcast
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(button_handler, pattern='^admin_broadcast$')],
        states={
            BROADCAST_MESSAGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_broadcast_handler)]
        },
        fallbacks=[CommandHandler('cancel', cancelar)]
    )
    
    # Agregar handlers principales
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(retiro_conv)
    application.add_handler(direccion_conv)
    application.add_handler(apuesta_conv)
    application.add_handler(deposito_conv)
    application.add_handler(broadcast_conv)
    
    # Iniciar bot
    print("🤖 ❌️Drks Bets❌️ - Bot de Apuestas Deportivas iniciado")
    print(f"👑 Admins configurados: {ADMIN_IDS}")
    print(f"📊 Usuarios: {len(data['users'])} | Eventos: {len(data['events'])}")
    print("🌐 Servidor web: http://0.0.0.0:8080")
    print("✅ Bot listo para recibir mensajes...")
    
    application.run_polling()

if __name__ == '__main__':
    main()
