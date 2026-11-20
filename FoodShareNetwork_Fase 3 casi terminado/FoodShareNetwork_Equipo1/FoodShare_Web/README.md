# FoodShare Network — versión web 2.2

Plataforma que conecta comercializadoras con fundaciones para aprovechar excedentes de comida (ODS 2 · Hambre Cero). La versión web utiliza Python + Flask y aplica Programación Orientada a Objetos.

## Tipos de cuenta

- **Comercializadora:** publica excedentes y consulta sus propias donaciones.
- **Fundación:** explora donaciones disponibles, reserva alimentos, confirma su recepción y consulta alertas.
- **Administradora:** revisa, aprueba o rechaza donaciones. El registro público de administradores está deshabilitado.

Desde «Regístrate» se pueden crear cuentas nuevas de Comercializadora o Fundación. Los perfiles tienen campos propios y una página «Mi cuenta» con sus datos y funciones.

## Ejecutar en Windows

Desde CMD abierto dentro de la carpeta `FoodShare_Web`, ejecutar la primera vez:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

Abrir `http://127.0.0.1:5000` en Chrome o Edge. Para detener el servidor, volver a CMD y presionar `CTRL + C`.

En siguientes ejecuciones, solo hace falta abrir CMD en `FoodShare_Web`, activar el entorno con `.venv\Scripts\activate` y ejecutar `python app.py`.

## Cuentas de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Comercializadora | contacto@elbuensabor.mx | claveComercializadora2024 |
| Fundación | recepcion@bancoesperanza.org | claveFundacion2024 |
| Administradora | admin@foodshare.org | rootAdminODS123 |

## Funciones incluidas

- Registro y acceso de cuentas de Comercializadora y Fundación. Las nuevas cuentas se guardan en `foodshare.sqlite3` y sus contraseñas se almacenan con hash PBKDF2.
- Publicación de donaciones por Comercializadora y validación por Administradora.
- Exploración, reserva y confirmación de recepción por Fundación.
- Información nutricional opcional en cada alimento. Se captura como texto libre y se muestra en la exploración y en el detalle; el sistema no calcula nutrientes.
- Alertas de Fundación: donaciones disponibles y reservas propias próximas a caducar. Se generan al consultar la página; todavía no hay historial de avisos leídos.
- Página «Mi cuenta» con datos y descripción de funciones según el rol.
- Fecha de caducidad obligatoria con al menos siete días de margen desde la fecha actual. No se aceptan alimentos con un plazo menor.
- Fechas de las donaciones demo calculadas tomando como referencia el día en que inicia la aplicación.

## Persistencia y limitaciones actuales

- Las cuentas nuevas de Comercializadora y Fundación sí se guardan en SQLite.
- Las donaciones, reservas y cambios de estado no se guardan automáticamente en SQLite. Se mantienen en memoria mientras el servidor está activo y se reinician al cerrar la aplicación.
- Las cuentas demo conservan contraseñas de ejemplo para facilitar la demostración académica. No se deben reutilizar estas credenciales fuera del entorno de prueba.
- Las alertas son dinámicas y no se marcan como leídas.

## Rutas principales

| Rol | Pantallas |
|---|---|
| Todos | `/login`, `/crear-cuenta`, `/mi-cuenta`, `/donacion/<id>` |
| Comercializadora | `/comercializadora/panel`, `/comercializadora/publicar`, `/comercializadora/mis-donaciones` |
| Fundación | `/fundacion/explorar`, `/fundacion/mis-reservas`, `/fundacion/alertas` |
| Administradora | `/admin/panel`, `/admin/validar`, `/admin/todas` |

## Pruebas

Desde `FoodShare_Web`:

```bat
python -m unittest discover -s tests -v
```

El proyecto incluye pruebas del modelo y de las rutas web. Las pruebas del modelo cubren roles, registro y persistencia de cuentas, datos nutricionales, fechas de caducidad, alertas, permisos, capacidad y el flujo de una donación. Las pruebas web cubren acceso por rol, registro, alertas, datos de cuenta y publicación.

## Estructura

- `app.py`: rutas Flask y control de sesiones.
- `logica.py`: clases POO, reglas de negocio y consultas.
- `datos_demo.py`: cuentas y donaciones de demostración.
- `templates/`: interfaz HTML.
- `tests/`: pruebas del modelo y de rutas.
