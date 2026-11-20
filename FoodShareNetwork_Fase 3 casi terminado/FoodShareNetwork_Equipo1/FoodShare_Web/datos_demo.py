"""Datos de demostración de FoodShare Network.

Las fechas de ejemplo se calculan tomando como referencia el día en que se
inicia la aplicación, para que las donaciones disponibles no aparezcan
vencidas cuando el proyecto se ejecute en otra fecha.
"""

from datetime import date, timedelta

# None hace que el sistema utilice la fecha real del equipo.
FECHA_DEMO = None
_HOY = date.today()


def _fecha(dias):
    return (_HOY + timedelta(days=dias)).strftime("%d/%m/%Y")


USUARIOS_DEMO = [
    {
        "id_usuario": "U01", "rol": "comercializadora", "nombre": "Comercializadora El Buen Sabor",
        "correo": "contacto@elbuensabor.mx", "contrasena": "claveComercializadora2024",
        "ubicacion": "Centro, CDMX", "razon_social": "Comercializadora El Buen Sabor S.A. de C.V.",
    },
    {
        "id_usuario": "U02", "rol": "fundacion", "nombre": "Banco Esperanza",
        "correo": "recepcion@bancoesperanza.org", "contrasena": "claveFundacion2024",
        "ubicacion": "Sur, CDMX", "capacidad_kg": 500.0,
    },
    {
        "id_usuario": "U03", "rol": "admin", "nombre": "Lic. Ana Ruiz",
        "correo": "admin@foodshare.org", "contrasena": "rootAdminODS123",
        "ubicacion": "Sede Central",
    },
    {
        "id_usuario": "U04", "rol": "comercializadora", "nombre": "Comercializadora Frutería Central",
        "correo": "contacto@fruteriacentral.mx", "contrasena": "clave2024",
        "ubicacion": "Norte, CDMX", "razon_social": "Frutas del Norte S.A. de C.V.",
    },
    {
        "id_usuario": "U05", "rol": "comercializadora", "nombre": "Comercializadora La Esquina",
        "correo": "contacto@comedorlaesquina.mx", "contrasena": "clave2024",
        "ubicacion": "Oriente, CDMX", "razon_social": "Abastecedora La Esquina S.A. de C.V.",
    },
    {
        "id_usuario": "U06", "rol": "comercializadora", "nombre": "Comercializadora San José",
        "correo": "contacto@panaderiasanjose.mx", "contrasena": "clave2024",
        "ubicacion": "Poniente, CDMX", "razon_social": "Distribuidora San José S.A. de C.V.",
    },
]

DONACIONES_DEMO = [
    {
        "id_donacion": "DON028", "descripcion": "Frutas de temporada", "fecha_creacion": _fecha(-1),
        "estado": "Reservada", "donante_id": "U04", "reservado_por_id": "U02",
        "alimentos": [{"nombre": "Caja de frutas mixtas", "peso_kg": 25.0,
                       "fecha_vencimiento": _fecha(14), "nutrientes": "Fibra, vitamina C y potasio"}],
    },
    {
        "id_donacion": "DON027", "descripcion": "Guisado de lentejas con verduras", "fecha_creacion": _fecha(-1),
        "estado": "Disponible", "donante_id": "U05", "reservado_por_id": None,
        "alimentos": [{"nombre": "Lentejas preparadas", "peso_kg": 20.0,
                       "fecha_vencimiento": _fecha(12), "nutrientes": "Proteína vegetal, hierro y fibra"}],
    },
    {
        "id_donacion": "DON026", "descripcion": "Pan integral horneado", "fecha_creacion": _fecha(-1),
        "estado": "Disponible", "donante_id": "U06", "reservado_por_id": None,
        "alimentos": [{"nombre": "Pan integral", "peso_kg": 12.0,
                       "fecha_vencimiento": _fecha(10), "nutrientes": "Carbohidratos, fibra y vitaminas B"}],
    },
    {
        "id_donacion": "DON025", "descripcion": "Arroz con verduras cocido", "fecha_creacion": _fecha(-1),
        "estado": "Pendiente de validación", "donante_id": "U01", "reservado_por_id": None,
        "alimentos": [{"nombre": "Arroz preparado", "peso_kg": 15.0,
                       "fecha_vencimiento": _fecha(13), "nutrientes": "Carbohidratos y fibra"}],
    },
    {
        "id_donacion": "DON024", "descripcion": "Verduras variadas", "fecha_creacion": _fecha(-2),
        "estado": "Disponible", "donante_id": "U01", "reservado_por_id": None,
        "alimentos": [{"nombre": "Caja de verduras", "peso_kg": 32.0,
                       "fecha_vencimiento": _fecha(9), "nutrientes": "Fibra, vitamina A y vitamina C"}],
    },
    {
        "id_donacion": "DON023", "descripcion": "Arroz cocido al vapor", "fecha_creacion": _fecha(-2),
        "estado": "Reservada", "donante_id": "U01", "reservado_por_id": "U02",
        "alimentos": [{"nombre": "Arroz al vapor", "peso_kg": 18.5,
                       "fecha_vencimiento": _fecha(11), "nutrientes": "Carbohidratos"}],
    },
    {
        "id_donacion": "DON022", "descripcion": "Pan de caja integral", "fecha_creacion": _fecha(-4),
        "estado": "Recibida", "donante_id": "U01", "reservado_por_id": "U02",
        "alimentos": [{"nombre": "Pan de caja", "peso_kg": 15.0,
                       "fecha_vencimiento": _fecha(8), "nutrientes": "Fibra y carbohidratos"}],
    },
    {
        "id_donacion": "DON021", "descripcion": "Pollo guisado en salsa", "fecha_creacion": _fecha(-6),
        "estado": "Vencida", "donante_id": "U01", "reservado_por_id": None,
        "alimentos": [{"nombre": "Pollo guisado", "peso_kg": 20.0,
                       "fecha_vencimiento": _fecha(-2), "nutrientes": "Proteína"}],
    },
]
