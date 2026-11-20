# FoodShare Network

Sistema de Gestión de Recursos Alimentarios (ODS 2 — Hambre Cero), proyecto integrador de Programación Orientada a Objetos.

La versión web principal está en `FoodShare_Web` y utiliza Python + Flask. La carpeta `fase2_tkinter` conserva el prototipo de escritorio de una fase anterior.

## Tipos de usuario

- **Comercializadora:** registra excedentes y publica donaciones.
- **Fundación:** consulta donaciones disponibles y reserva alimentos según su capacidad.
- **Administrador:** valida o rechaza donaciones. Esta cuenta se crea y administra de forma controlada; no existe registro público de administradores.

Cada tipo de cuenta tiene una pantalla «Mi cuenta» que muestra sus datos y las funciones disponibles para su rol. La Fundación también cuenta con una sección de alertas.

Desde el enlace **Regístrate** se pueden crear nuevas cuentas de Comercializadora y Fundación. Cada tipo muestra los campos que necesita. Las cuentas nuevas se guardan en SQLite (`FoodShare_Web/foodshare.sqlite3`) y se conservan al reiniciar la aplicación. Las contraseñas de las cuentas creadas se almacenan con hash PBKDF2.

## Ejecutar la aplicación web en Windows

Abre CMD dentro de `FoodShare_Web` y ejecuta estos comandos (la primera vez):

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python app.py
```

En las siguientes ocasiones, basta con activar `.venv` y ejecutar `python app.py`.

Después abre `http://127.0.0.1:5000` en el navegador.

## Ejecutar las pruebas

Desde `FoodShare_Web`:

```bat
python -m unittest discover -s tests -v
```

## Cuentas de demostración

| Rol | Correo | Contraseña |
|---|---|---|
| Comercializadora | contacto@elbuensabor.mx | claveComercializadora2024 |
| Fundación | recepcion@bancoesperanza.org | claveFundacion2024 |
| Administradora | admin@foodshare.org | rootAdminODS123 |

Las cuentas de demostración se cargan desde `FoodShare_Web/datos_demo.py`. Los registros que hagan los usuarios desde la página no sustituyen ni modifican estas cuentas.

## Funciones actuales y persistencia

- Las cuentas nuevas de Comercializadora y Fundación se guardan en SQLite y conservan su contraseña con hash PBKDF2.
- Las donaciones, reservas y cambios de estado funcionan mientras el servidor está abierto. No se guardan automáticamente en SQLite; al cerrar el servidor, las donaciones creadas durante esa sesión se reinician.
- La Fundación tiene una pantalla de Alertas para ver donaciones disponibles y avisos de sus reservas próximas a caducar. Los avisos se generan a partir del estado actual; todavía no existe historial de lectura.
- Cada rol tiene la pantalla «Mi cuenta», que muestra sus datos y permisos.
- La fecha de caducidad de los alimentos nuevos debe ser al menos siete días posterior a la fecha actual.
- La información nutricional es opcional, se captura como texto y se muestra al consultar la donación. El sistema no calcula esos valores.
- Las fechas de los datos de demostración se calculan con base en el día en que se inicia la aplicación.
