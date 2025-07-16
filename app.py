import pandas as pd
from nicegui import ui

# Autenticación básica
usuarios = {'admin': '1234'}  # puedes cambiar o cargar desde archivo seguro
usuario_autenticado = {'valor': False}

def login():
    with ui.card().classes('absolute-center'):
        ui.label('Inicio de sesión').classes('text-h5')
        user = ui.input('Usuario')
        password = ui.input('Contraseña', password=True)
        def verificar():
            if user.value in usuarios and usuarios[user.value] == password.value:
                usuario_autenticado['valor'] = True
                ui.open('/dashboard')
            else:
                ui.notify('Credenciales inválidas', type='negative')
        ui.button('Ingresar', on_click=verificar)

@ui.page('/')
def index():
    login()

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
        ui.button('Cerrar sesión', on_click=lambda: ui.open('/'))

ui.run(title='Demo Protegido con Login', port=8080, reload=False)
