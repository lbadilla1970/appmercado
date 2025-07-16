import os
import json
import base64
import hashlib
import secrets
import pandas as pd
from nicegui import ui, Client

# almacenamiento de usuarios en archivo JSON con contraseñas cifradas
USERS_FILE = 'users.json'
usuarios = {}
usuario_autenticado = {'valor': False, 'email': None}


def load_users() -> None:
    """Cargar usuarios desde archivo"""
    global usuarios
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            usuarios = json.load(f)
    else:
        usuarios = {}


def save_users() -> None:
    """Guardar usuarios en archivo"""
    with open(USERS_FILE, 'w') as f:
        json.dump(usuarios, f)


def hash_password(password: str, *, salt: str | None = None) -> str:
    """Genera un hash SHA-256 con sal"""
    if salt is None:
        salt = base64.urlsafe_b64encode(os.urandom(16)).decode()
    hashed = hashlib.sha256((salt + password).encode()).hexdigest()
    return f'{salt}${hashed}'


def verify_password(password: str, hashed: str) -> bool:
    """Verificar que la clave coincida con el hash almacenado"""
    salt, hashed_val = hashed.split('$')
    return hashlib.sha256((salt + password).encode()).hexdigest() == hashed_val


load_users()


def login() -> None:
    """Página de inicio de sesión"""
    with ui.card().classes('absolute-center'):
        ui.label('Inicio de sesión').classes('text-h5')
        correo = ui.input('Correo')
        password = ui.input('Contraseña', password=True)

        def verificar() -> None:
            if (
                correo.value in usuarios
                and verify_password(password.value, usuarios[correo.value]['password'])
            ):
                usuario_autenticado['valor'] = True
                usuario_autenticado['email'] = correo.value
                ui.open('/dashboard')
            else:
                ui.notify('Credenciales inválidas', type='negative')

        ui.button('Ingresar', on_click=verificar)
        ui.button('Iniciar con Google', on_click=lambda: ui.open('/google-login')).classes('mt-2')
        ui.link('Registrarse', '/signup').classes('block mt-4')
        ui.link('¿Olvidaste tu contraseña?', '/reset').classes('block')

@ui.page('/')
def index():
    login()


@ui.page('/signup')
def signup() -> None:
    """Registro de nuevo usuario"""
    with ui.card().classes('absolute-center'):
        ui.label('Registro').classes('text-h5')
        correo = ui.input('Correo')
        password = ui.input('Contraseña', password=True)

        def registrar() -> None:
            if correo.value in usuarios:
                ui.notify('El correo ya está registrado', type='negative')
                return
            usuarios[correo.value] = {'password': hash_password(password.value)}
            save_users()
            ui.notify('Registro exitoso', type='positive')
            ui.open('/')

        ui.button('Crear cuenta', on_click=registrar)
        ui.link('Volver', '/').classes('block mt-4')


@ui.page('/reset')
def reset_request() -> None:
    """Solicitud de restablecimiento"""
    with ui.card().classes('absolute-center'):
        ui.label('Recuperar contraseña').classes('text-h5')
        correo = ui.input('Correo')

        def enviar() -> None:
            if correo.value not in usuarios:
                ui.notify('Correo no registrado', type='negative')
                return
            token = secrets.token_urlsafe(16)
            usuarios[correo.value]['reset'] = token
            save_users()
            ui.notify(f'Token de recuperación: {token}', type='info')
            ui.link('Ir a restablecer', f'/reset_confirm?token={token}', new_tab=True)

        ui.button('Enviar enlace', on_click=enviar)
        ui.link('Volver', '/').classes('block mt-4')


@ui.page('/reset_confirm')
def reset_confirm(client: Client) -> None:
    """Restablecer contraseña mediante token"""
    token = client.request.query_params.get('token', '')
    with ui.card().classes('absolute-center'):
        ui.label('Restablecer contraseña').classes('text-h5')
        nueva = ui.input('Nueva contraseña', password=True)

        def cambiar() -> None:
            for correo, info in usuarios.items():
                if info.get('reset') == token:
                    info['password'] = hash_password(nueva.value)
                    info.pop('reset', None)
                    save_users()
                    ui.notify('Contraseña actualizada', type='positive')
                    ui.open('/')
                    return
            ui.notify('Token inválido', type='negative')

        ui.button('Cambiar', on_click=cambiar)
        ui.link('Volver', '/').classes('block mt-4')


@ui.page('/google-login')
def google_login() -> None:
    """Punto de entrada para autenticación con Google (no implementado)"""
    with ui.card().classes('absolute-center'):
        ui.label('Autenticación con Google').classes('text-h5')
        ui.notify('Google login no configurado en este ejemplo', type='warning')
        ui.link('Volver', '/').classes('block mt-4')

@ui.page('/dashboard')
def dashboard():
    if not usuario_autenticado['valor']:
        ui.notify('Debe iniciar sesión primero', type='warning')
        ui.open('/')
        return

    df = pd.read_csv('data.csv')
    categorias = sorted(df['Categoria'].unique())
    filtro_categoria = ui.select(categorias, label='Filtrar por categoría', value=categorias[0])

    tabla_container = ui.element('div')
    grafico_container = ui.element('div')

    def render():
        tabla_container.clear()
        grafico_container.clear()
        df_filtrado = df[df['Categoria'] == filtro_categoria.value]

        with tabla_container:
            ui.label(f'Registros para categoría: {filtro_categoria.value}').classes('text-h6')
            ui.table(columns=[{'name': c, 'label': c, 'field': c} for c in df.columns],
                     rows=df_filtrado.to_dict('records'),
                     row_key='Producto')

        with grafico_container:
            ui.echart({
                'xAxis': {'type': 'category', 'data': df_filtrado['Producto'].tolist()},
                'yAxis': {'type': 'value'},
                'series': [{
                    'data': df_filtrado['Ventas'].tolist(),
                    'type': 'bar'
                }]
            }).classes('w-full h-64')

    filtro_categoria.on('update:model-value', lambda e: render())

    with ui.card().classes('m-auto'):
        ui.label('Dashboard Privado').classes('text-h5')
        render()
        def logout() -> None:
            usuario_autenticado['valor'] = False
            usuario_autenticado['email'] = None
            ui.open('/')

        ui.button('Cerrar sesión', on_click=logout)

ui.run(title='Demo Protegido con Login', port=8080, reload=False)
