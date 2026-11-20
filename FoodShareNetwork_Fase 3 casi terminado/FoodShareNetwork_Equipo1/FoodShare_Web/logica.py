# logica.py
"""Modelo de FoodShare Network (Programación Orientada a Objetos).

Este archivo no sabe nada de páginas web: solo contiene las clases y
las reglas del negocio. app.py (Flask) las usa para mostrar pantallas.

Conceptos de POO que se aplican aquí:
- Abstracción: Usuario es una clase abstracta (no se puede instanciar).
- Herencia: Comercializadora, Fundacion y Administrador heredan de Usuario.
- Polimorfismo: cada subclase responde distinto a `rol`, `etiqueta_rol`
  y `pantalla_inicio`.
- Encapsulamiento: la contraseña se guarda en un atributo "privado"
  (_contrasena) y solo se compara con verificar_contrasena().
- Composición: una Donacion está formada por varios objetos Alimento.
"""

from abc import ABC, abstractmethod
from datetime import date, datetime, timedelta
import hashlib
import hmac
import os
import secrets
import sqlite3

from datos_demo import DONACIONES_DEMO, FECHA_DEMO, USUARIOS_DEMO

FORMATO_FECHA = "%d/%m/%Y"


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
class ErrorFoodShare(Exception):
    """Error de una regla del negocio. Su mensaje se le muestra al usuario."""


def convertir_fecha(valor):
    """Convierte 'dd/mm/aaaa' (o un objeto date) a datetime.date."""
    if isinstance(valor, date):
        return valor
    try:
        return datetime.strptime(str(valor).strip(), FORMATO_FECHA).date()
    except ValueError:
        raise ErrorFoodShare("La fecha debe tener el formato dd/mm/aaaa.")


def formatear_fecha(fecha):
    """Convierte un datetime.date a texto 'dd/mm/aaaa'."""
    return fecha.strftime(FORMATO_FECHA) if fecha else ""


class Estado:
    """Nombres de los estados posibles de una donación."""

    PENDIENTE = "Pendiente de validación"
    DISPONIBLE = "Disponible"
    RESERVADA = "Reservada"
    RECIBIDA = "Recibida"
    VENCIDA = "Vencida"
    RECHAZADA = "Rechazada"

    TODOS = [PENDIENTE, DISPONIBLE, RESERVADA, RECIBIDA, VENCIDA, RECHAZADA]

    # Desde qué estado se puede pasar a cuál (máquina de estados).
    TRANSICIONES = {
        PENDIENTE: [DISPONIBLE, RECHAZADA, VENCIDA],
        DISPONIBLE: [RESERVADA, VENCIDA],
        RESERVADA: [RECIBIDA],
        RECIBIDA: [],
        VENCIDA: [],
        RECHAZADA: [],
    }


# ---------------------------------------------------------------------------
# Usuarios (herencia + clase abstracta)
# ---------------------------------------------------------------------------
class Usuario(ABC):
    """Clase base abstracta para todos los usuarios del sistema."""

    def __init__(self, id_usuario, nombre, correo, contrasena, ubicacion):
        self.id_usuario = id_usuario
        self.nombre = nombre
        self.correo = correo.strip().lower()
        self._contrasena = contrasena
        self.ubicacion = ubicacion

    def verificar_contrasena(self, contrasena):
        """Verifica contraseñas nuevas con PBKDF2 y conserva compatibilidad demo."""
        guardada = self._contrasena or ""
        if guardada.startswith("pbkdf2_sha256$"):
            try:
                _, iteraciones, sal_hex, hash_hex = guardada.split("$", 3)
                calculado = hashlib.pbkdf2_hmac(
                    "sha256", str(contrasena).encode("utf-8"),
                    bytes.fromhex(sal_hex), int(iteraciones)
                ).hex()
                return hmac.compare_digest(calculado, hash_hex)
            except (ValueError, TypeError):
                return False
        # Las cuentas de demostración preexistentes conservan su clave de ejemplo.
        return hmac.compare_digest(guardada, str(contrasena))

    @property
    @abstractmethod
    def rol(self):
        """Identificador interno del rol: 'comercializadora', 'fundacion' o 'admin'."""

    @property
    @abstractmethod
    def etiqueta_rol(self):
        """Texto que se muestra en la interfaz junto al nombre."""

    @abstractmethod
    def pantalla_inicio(self):
        """Nombre de la ruta de Flask a la que entra después de iniciar sesión."""

    def __repr__(self):
        return "{}({}, {})".format(type(self).__name__, self.id_usuario, self.nombre)


class Comercializadora(Usuario):
    """Donante: publica excedentes de comida."""

    def __init__(self, id_usuario, nombre, correo, contrasena, ubicacion, razon_social):
        super().__init__(id_usuario, nombre, correo, contrasena, ubicacion)
        self.razon_social = razon_social

    @property
    def rol(self):
        return "comercializadora"

    @property
    def etiqueta_rol(self):
        return "Comercializadora"

    def pantalla_inicio(self):
        return "comercializadora_panel"


class Fundacion(Usuario):
    """Receptor: reserva donaciones disponibles y confirma que las recibió."""

    def __init__(self, id_usuario, nombre, correo, contrasena, ubicacion, capacidad_kg):
        super().__init__(id_usuario, nombre, correo, contrasena, ubicacion)
        self.capacidad_kg = float(capacidad_kg)

    @property
    def rol(self):
        return "fundacion"

    @property
    def etiqueta_rol(self):
        return "Fundación"

    def pantalla_inicio(self):
        return "fundacion_explorar"


class Administrador(Usuario):
    """Valida (aprueba o rechaza) las donaciones antes de publicarlas."""

    @property
    def rol(self):
        return "admin"

    @property
    def etiqueta_rol(self):
        return "Administradora"

    def pantalla_inicio(self):
        return "admin_panel"


# ---------------------------------------------------------------------------
# Alimentos y donaciones (composición)
# ---------------------------------------------------------------------------
class Alimento:
    """Un alimento dentro de una donación."""

    def __init__(self, nombre, peso_kg, fecha_vencimiento, nutrientes=""):
        nombre = (nombre or "").strip()
        if not nombre:
            raise ErrorFoodShare("El nombre del alimento es obligatorio.")
        try:
            peso_kg = float(peso_kg)
        except (TypeError, ValueError):
            raise ErrorFoodShare("La cantidad debe ser un número.")
        if peso_kg <= 0:
            raise ErrorFoodShare("La cantidad debe ser mayor que 0 kg.")

        self.nombre = nombre
        self.peso_kg = round(peso_kg, 2)
        self.fecha_vencimiento = convertir_fecha(fecha_vencimiento)
        self.nutrientes = (nutrientes or "").strip()

    @property
    def str_vencimiento(self):
        return formatear_fecha(self.fecha_vencimiento)


class Donacion:
    """Conjunto de alimentos que una comercializadora ofrece a las fundaciones."""

    def __init__(self, id_donacion, alimentos, donante, fecha_creacion,
                 estado=Estado.PENDIENTE, reservado_por=None, descripcion=None):
        if not alimentos:
            raise ErrorFoodShare("Una donación debe tener al menos un alimento.")
        if estado not in Estado.TODOS:
            raise ErrorFoodShare("Estado desconocido: {}".format(estado))
        self.id_donacion = id_donacion
        self.alimentos = list(alimentos)
        self.donante = donante
        self.fecha_creacion = convertir_fecha(fecha_creacion)
        self.estado = estado
        self.reservado_por = reservado_por
        self.fecha_recepcion = None
        self._descripcion = descripcion

    # --- Datos calculados -------------------------------------------------
    @property
    def descripcion(self):
        """Usa la descripción dada o, si no hay, los nombres de los alimentos."""
        if self._descripcion:
            return self._descripcion
        nombres = [a.nombre for a in self.alimentos]
        if len(nombres) <= 2:
            return " y ".join(nombres)
        return "{} y {} más".format(", ".join(nombres[:2]), len(nombres) - 2)

    @property
    def peso_total(self):
        return round(sum(a.peso_kg for a in self.alimentos), 2)

    @property
    def vencimiento_proximo(self):
        return min(a.fecha_vencimiento for a in self.alimentos)

    @property
    def str_vencimiento(self):
        return formatear_fecha(self.vencimiento_proximo)

    # --- Comportamiento ---------------------------------------------------
    def puede_cambiar_a(self, nuevo_estado):
        return nuevo_estado in Estado.TRANSICIONES[self.estado]

    def cambiar_estado(self, nuevo_estado):
        if not self.puede_cambiar_a(nuevo_estado):
            raise ErrorFoodShare(
                "La donación {} está {} y no puede pasar a {}.".format(
                    self.id_donacion, self.estado.lower(), nuevo_estado.lower()))
        self.estado = nuevo_estado

    def esta_vencida(self, hoy):
        return self.vencimiento_proximo < hoy

    def coincide_con(self, texto):
        """True si el texto aparece en el ID, la descripción, el donante o un alimento."""
        texto = (texto or "").strip().lower()
        if not texto:
            return True
        partes = [self.id_donacion, self.descripcion, self.donante.nombre]
        partes += [a.nombre for a in self.alimentos]
        return any(texto in parte.lower() for parte in partes)


# ---------------------------------------------------------------------------
# Sistema: aplica las reglas y persiste las cuentas nuevas
# ---------------------------------------------------------------------------
class Sistema:
    """Controlador de la aplicación; permite persistir cuentas nuevas en SQLite."""

    def __init__(self, fecha_actual=None, cargar_demo=True, db_path=None):
        self._fecha_fija = fecha_actual
        self.usuarios = []
        self.donaciones = []
        self.db_path = os.path.abspath(db_path) if db_path else None
        if self.db_path:
            self._inicializar_base_datos()
        if cargar_demo:
            self._cargar_datos()
        if self.db_path:
            self._cargar_usuarios_registrados()
        self.actualizar_vencidas()

    def _inicializar_base_datos(self):
        """Crea la tabla de cuentas; la base se mantiene local al proyecto."""
        carpeta = os.path.dirname(self.db_path)
        if carpeta:
            os.makedirs(carpeta, exist_ok=True)
        with sqlite3.connect(self.db_path) as conexion:
            conexion.execute("""
                CREATE TABLE IF NOT EXISTS usuarios_registrados (
                    id_usuario TEXT PRIMARY KEY,
                    rol TEXT NOT NULL,
                    nombre TEXT NOT NULL,
                    correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    contrasena_hash TEXT NOT NULL,
                    ubicacion TEXT NOT NULL,
                    razon_social TEXT,
                    capacidad_kg REAL
                )
            """)

    def _cargar_usuarios_registrados(self):
        """Recupera cuentas creadas desde el formulario de registro."""
        with sqlite3.connect(self.db_path) as conexion:
            filas = conexion.execute("""
                SELECT id_usuario, rol, nombre, correo, contrasena_hash,
                       ubicacion, razon_social, capacidad_kg
                FROM usuarios_registrados ORDER BY id_usuario
            """).fetchall()
        for (id_usuario, rol, nombre, correo, contrasena_hash,
             ubicacion, razon_social, capacidad_kg) in filas:
            if self.buscar_por_correo(correo):
                continue
            if rol == "comercializadora":
                usuario = Comercializadora(id_usuario, nombre, correo, contrasena_hash,
                                           ubicacion, razon_social or "")
            elif rol == "fundacion":
                usuario = Fundacion(id_usuario, nombre, correo, contrasena_hash,
                                    ubicacion, capacidad_kg or 0)
            else:
                continue
            self.usuarios.append(usuario)

    def _guardar_usuario_registrado(self, usuario):
        """Guarda solamente cuentas públicas; nunca se registra un administrador."""
        if not self.db_path:
            return
        if usuario.rol == "comercializadora":
            razon_social = usuario.razon_social
            capacidad = None
        elif usuario.rol == "fundacion":
            razon_social = None
            capacidad = usuario.capacidad_kg
        else:
            raise ErrorFoodShare("Este tipo de cuenta no puede registrarse públicamente.")
        with sqlite3.connect(self.db_path) as conexion:
            conexion.execute("""
                INSERT INTO usuarios_registrados
                (id_usuario, rol, nombre, correo, contrasena_hash, ubicacion,
                 razon_social, capacidad_kg)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (usuario.id_usuario, usuario.rol, usuario.nombre, usuario.correo,
                  usuario._contrasena, usuario.ubicacion, razon_social, capacidad))

    @property
    def hoy(self):
        return self._fecha_fija or date.today()

    # --- Carga inicial ----------------------------------------------------
    def _cargar_datos(self):
        for u in USUARIOS_DEMO:
            self.usuarios.append(self._crear_usuario_desde_dict(u))

        for d in DONACIONES_DEMO:
            alimentos = [Alimento(a["nombre"], a["peso_kg"], a["fecha_vencimiento"],
                                  a.get("nutrientes", "")) for a in d["alimentos"]]
            donacion = Donacion(
                d["id_donacion"], alimentos,
                donante=self.obtener_usuario(d["donante_id"]),
                fecha_creacion=d["fecha_creacion"],
                estado=d["estado"],
                reservado_por=self.obtener_usuario(d["reservado_por_id"]),
                descripcion=d.get("descripcion"),
            )
            self.donaciones.append(donacion)

    @staticmethod
    def _crear_usuario_desde_dict(u):
        if u["rol"] == "comercializadora":
            return Comercializadora(u["id_usuario"], u["nombre"], u["correo"], u["contrasena"],
                               u["ubicacion"], u["razon_social"])
        if u["rol"] == "fundacion":
            return Fundacion(u["id_usuario"], u["nombre"], u["correo"], u["contrasena"],
                             u["ubicacion"], u["capacidad_kg"])
        return Administrador(u["id_usuario"], u["nombre"], u["correo"], u["contrasena"],
                             u["ubicacion"])

    # --- Usuarios ---------------------------------------------------------
    def obtener_usuario(self, id_usuario):
        for u in self.usuarios:
            if u.id_usuario == id_usuario:
                return u
        return None

    def buscar_por_correo(self, correo):
        correo = (correo or "").strip().lower()
        for u in self.usuarios:
            if u.correo == correo:
                return u
        return None

    def autenticar(self, correo, contrasena):
        usuario = self.buscar_por_correo(correo)
        if usuario and usuario.verificar_contrasena(contrasena):
            return usuario
        return None

    def registrar_usuario(self, tipo, nombre, correo, contrasena, confirmacion,
                          ubicacion, razon_social="", capacidad_kg=""):

        """Crea una cuenta de Comercializadora o Fundación (nunca de Administrador)."""
        nombre = (nombre or "").strip()
        correo = (correo or "").strip().lower()
        ubicacion = (ubicacion or "").strip()
        razon_social = (razon_social or "").strip()

        if tipo not in ("comercializadora", "fundacion"):
            raise ErrorFoodShare("Selecciona Comercializadora o Fundación.")
        if not nombre or not correo or not ubicacion or not contrasena:
            raise ErrorFoodShare("Completa todos los campos obligatorios.")
        if "@" not in correo or "." not in correo.split("@")[-1]:
            raise ErrorFoodShare("Escribe un correo electrónico válido.")
        if self.buscar_por_correo(correo):
            raise ErrorFoodShare("Ya existe una cuenta con ese correo.")
        if len(contrasena) < 6:
            raise ErrorFoodShare("La contraseña debe tener al menos 6 caracteres.")
        if contrasena != confirmacion:
            raise ErrorFoodShare("Las contraseñas no coinciden.")

        numeros = [int(u.id_usuario[1:]) for u in self.usuarios
                   if u.id_usuario.startswith("U") and u.id_usuario[1:].isdigit()]
        nuevo_id = "U{:02d}".format(max(numeros, default=0) + 1)
        sal = secrets.token_bytes(16)
        iteraciones = 260000
        hash_contrasena = hashlib.pbkdf2_hmac(
            "sha256", contrasena.encode("utf-8"), sal, iteraciones
        ).hex()
        contrasena_segura = "pbkdf2_sha256${}${}${}".format(
            iteraciones, sal.hex(), hash_contrasena
        )

        if tipo == "comercializadora":
            if not razon_social:
                raise ErrorFoodShare("La razón social de la comercializadora es obligatoria.")
            usuario = Comercializadora(nuevo_id, nombre, correo, contrasena_segura, ubicacion, razon_social)
        else:
            try:
                capacidad = float(capacidad_kg)
            except (TypeError, ValueError):
                raise ErrorFoodShare("Escribe la capacidad de recepción en kg.")
            if capacidad <= 0:
                raise ErrorFoodShare("La capacidad de recepción debe ser mayor que 0 kg.")
            usuario = Fundacion(nuevo_id, nombre, correo, contrasena_segura, ubicacion, capacidad)

        self.usuarios.append(usuario)
        try:
            self._guardar_usuario_registrado(usuario)
        except sqlite3.IntegrityError:
            self.usuarios.remove(usuario)
            raise ErrorFoodShare("Ya existe una cuenta con ese correo.")
        except sqlite3.Error as error:
            self.usuarios.remove(usuario)
            raise ErrorFoodShare("No se pudo guardar la cuenta. Inténtalo de nuevo.") from error
        return usuario

    def comercializadoras(self):
        return [u for u in self.usuarios if isinstance(u, Comercializadora)]

    # --- Consultas de donaciones -----------------------------------------
    def obtener_donacion(self, id_donacion):
        for d in self.donaciones:
            if d.id_donacion == id_donacion:
                return d
        return None

    def _exigir_donacion(self, id_donacion):
        donacion = self.obtener_donacion(id_donacion)
        if donacion is None:
            raise ErrorFoodShare("No existe la donación {}.".format(id_donacion))
        return donacion

    def todas_las_donaciones(self):
        """Más recientes primero (por ID)."""
        return sorted(self.donaciones, key=lambda d: d.id_donacion, reverse=True)

    def donaciones_por_estado(self, *estados):
        return [d for d in self.todas_las_donaciones() if d.estado in estados]

    def donaciones_de_comercializadora(self, comercializadora):
        return [d for d in self.todas_las_donaciones() if d.donante is comercializadora]

    def reservas_de_fundacion(self, fundacion):
        return [d for d in self.todas_las_donaciones() if d.reservado_por is fundacion]

    @staticmethod
    def filtrar(donaciones, texto="", estado=""):
        """Filtra una lista por texto de búsqueda y por estado ('' = todos)."""
        resultado = [d for d in donaciones if d.coincide_con(texto)]
        if estado:
            resultado = [d for d in resultado if d.estado == estado]
        return resultado

    @staticmethod
    def peso_de(donaciones):
        return round(sum(d.peso_total for d in donaciones), 2)

    def siguiente_id(self):
        numeros = [int(d.id_donacion[3:]) for d in self.donaciones
                   if d.id_donacion[3:].isdigit()]
        return "DON{:03d}".format(max(numeros, default=0) + 1)

    def actualizar_vencidas(self):
        """Marca como Vencida lo que caducó antes de ser reservado."""
        cambiadas = []
        for d in self.donaciones:
            if d.estado in (Estado.PENDIENTE, Estado.DISPONIBLE) and d.esta_vencida(self.hoy):
                d.cambiar_estado(Estado.VENCIDA)
                cambiadas.append(d)
        return cambiadas

    # --- Acciones (cada una valida quién la hace) -------------------------
    def validar_fecha_caducidad(self, alimento, dias_minimos=7):
        """Exige que el alimento siga vigente al menos los días establecidos."""
        fecha_minima = self.hoy + timedelta(days=dias_minimos)
        if alimento.fecha_vencimiento < fecha_minima:
            raise ErrorFoodShare(
                "La fecha de caducidad de «{}» debe ser al menos {} días después de hoy (desde {}).".format(
                    alimento.nombre, dias_minimos, formatear_fecha(fecha_minima)))
        return True

    def alertas_fundacion(self, fundacion):
        """Genera avisos de donaciones disponibles y reservas próximas a caducar."""
        if not isinstance(fundacion, Fundacion):
            raise ErrorFoodShare("Las alertas de esta sección son para cuentas de Fundación.")
        alertas = []
        for donacion in self.todas_las_donaciones():
            if donacion.estado == Estado.DISPONIBLE:
                alertas.append({
                    "tipo": "disponible",
                    "titulo": "Hay una donación disponible",
                    "mensaje": "{} ofrece {} kg. Revisa si puedes aprovecharla.".format(
                        donacion.donante.nombre, donacion.peso_total),
                    "donacion": donacion,
                })
            elif donacion.estado == Estado.RESERVADA and donacion.reservado_por is fundacion:
                dias = (donacion.vencimiento_proximo - self.hoy).days
                if dias <= 3:
                    alertas.append({
                        "tipo": "urgente" if dias <= 1 else "aviso",
                        "titulo": "Tu reserva está próxima a caducar" if dias >= 0 else "Revisa una reserva vencida",
                        "mensaje": ("La donación {} vence {}.".format(
                            donacion.id_donacion,
                            "hoy" if dias == 0 else ("mañana" if dias == 1 else "en {} días".format(dias)))
                            if dias >= 0 else "La fecha de caducidad de {} ya pasó. Contacta a la comercializadora.".format(donacion.id_donacion)),
                        "donacion": donacion,
                    })
        return alertas

    def publicar_donacion(self, comercializadora, alimentos):
        if not isinstance(comercializadora, Comercializadora):
            raise ErrorFoodShare("Solo una comercializadora puede publicar donaciones.")
        if not alimentos:
            raise ErrorFoodShare("Agrega al menos un alimento a la donación.")
        for a in alimentos:
            self.validar_fecha_caducidad(a)
        donacion = Donacion(self.siguiente_id(), alimentos, comercializadora, self.hoy)
        self.donaciones.append(donacion)
        return donacion

    def aprobar_donacion(self, administrador, id_donacion):
        self._exigir_admin(administrador)
        donacion = self._exigir_donacion(id_donacion)
        if donacion.estado == Estado.PENDIENTE and donacion.esta_vencida(self.hoy):
            donacion.cambiar_estado(Estado.VENCIDA)
            raise ErrorFoodShare("La donación {} ya caducó; se marcó como vencida.".format(id_donacion))
        donacion.cambiar_estado(Estado.DISPONIBLE)
        return donacion

    def rechazar_donacion(self, administrador, id_donacion):
        self._exigir_admin(administrador)
        donacion = self._exigir_donacion(id_donacion)
        donacion.cambiar_estado(Estado.RECHAZADA)
        return donacion

    def reservar_donacion(self, fundacion, id_donacion):
        if not isinstance(fundacion, Fundacion):
            raise ErrorFoodShare("Solo una fundación puede reservar donaciones.")
        donacion = self._exigir_donacion(id_donacion)
        if donacion.estado == Estado.DISPONIBLE and donacion.esta_vencida(self.hoy):
            donacion.cambiar_estado(Estado.VENCIDA)
            raise ErrorFoodShare("La donación {} ya caducó y no se puede reservar.".format(id_donacion))

        por_recibir = self.peso_de([d for d in self.reservas_de_fundacion(fundacion)
                                    if d.estado == Estado.RESERVADA])
        if por_recibir + donacion.peso_total > fundacion.capacidad_kg:
            raise ErrorFoodShare(
                "Supera tu capacidad de recepción ({:.1f} kg). Tienes {:.1f} kg por recibir.".format(
                    fundacion.capacidad_kg, por_recibir))

        donacion.cambiar_estado(Estado.RESERVADA)
        donacion.reservado_por = fundacion
        return donacion

    def marcar_recibida(self, fundacion, id_donacion):
        donacion = self._exigir_donacion(id_donacion)
        if donacion.reservado_por is not fundacion:
            raise ErrorFoodShare("Solo la fundación que reservó la donación puede marcarla como recibida.")
        donacion.cambiar_estado(Estado.RECIBIDA)
        donacion.fecha_recepcion = self.hoy
        return donacion

    @staticmethod
    def _exigir_admin(usuario):
        if not isinstance(usuario, Administrador):
            raise ErrorFoodShare("Solo un administrador puede validar donaciones.")

    # --- Resúmenes para los paneles ---------------------------------------
    def resumen_general(self):
        disponibles = self.donaciones_por_estado(Estado.DISPONIBLE)
        return {
            "pendientes": len(self.donaciones_por_estado(Estado.PENDIENTE)),
            "disponibles": len(disponibles),
            "kg_disponibles": self.peso_de(disponibles),
            "reservadas": len(self.donaciones_por_estado(Estado.RESERVADA)),
            "recibidas": len(self.donaciones_por_estado(Estado.RECIBIDA)),
            "comercializadoras": len(self.comercializadoras()),
            "total": len(self.donaciones),
        }

    def resumen_comercializadora(self, comercializadora):
        propias = self.donaciones_de_comercializadora(comercializadora)
        disponibles = [d for d in propias if d.estado == Estado.DISPONIBLE]
        reservadas = [d for d in propias if d.estado == Estado.RESERVADA]
        return {
            "publicadas": len(propias),
            "pendientes": len([d for d in propias if d.estado == Estado.PENDIENTE]),
            "disponibles": len(disponibles),
            "kg_disponibles": self.peso_de(disponibles),
            "reservadas": len(reservadas),
            "kg_reservadas": self.peso_de(reservadas),
        }

    def resumen_fundacion(self, fundacion):
        activas = [d for d in self.reservas_de_fundacion(fundacion) if d.estado == Estado.RESERVADA]
        return {"activas": len(activas), "kg_por_recibir": self.peso_de(activas)}


# Instancia única de la aplicación web. Las cuentas nuevas quedan en SQLite local.
_RUTA_BASE = os.path.dirname(os.path.abspath(__file__))
sistema = Sistema(fecha_actual=FECHA_DEMO,
                  db_path=os.path.join(_RUTA_BASE, "foodshare.sqlite3"))
