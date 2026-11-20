# tests/test_logica.py
"""Pruebas del modelo POO (logica.py). Ejecutar desde FoodShare_Web:

    python -m unittest discover -s tests -v
"""

import os
import sys
import tempfile
import unittest
from datetime import date, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logica import (Administrador, Alimento, Donacion, ErrorFoodShare, Estado,  # noqa: E402
                    Fundacion, Comercializadora, Sistema, Usuario)

HOY = date.today()


def fecha_en(dias):
    return (HOY + timedelta(days=dias)).strftime("%d/%m/%Y")


def nuevo_sistema():
    """Cada prueba usa un sistema nuevo para no afectar a las demás."""
    return Sistema(fecha_actual=HOY)


class PruebasUsuarios(unittest.TestCase):
    def test_usuario_es_abstracto(self):
        with self.assertRaises(TypeError):
            Usuario("U99", "X", "x@x.mx", "123456", "CDMX")

    def test_polimorfismo_de_roles(self):
        s = nuevo_sistema()
        r, f, a = s.obtener_usuario("U01"), s.obtener_usuario("U02"), s.obtener_usuario("U03")
        self.assertIsInstance(r, Comercializadora)
        self.assertIsInstance(f, Fundacion)
        self.assertIsInstance(a, Administrador)
        self.assertEqual([u.rol for u in (r, f, a)], ["comercializadora", "fundacion", "admin"])
        self.assertEqual(f.pantalla_inicio(), "fundacion_explorar")

    def test_autenticar(self):
        s = nuevo_sistema()
        self.assertIsNotNone(s.autenticar("contacto@elbuensabor.mx", "claveComercializadora2024"))
        self.assertIsNotNone(s.autenticar("  CONTACTO@ElBuenSabor.mx ", "claveComercializadora2024"))
        self.assertIsNone(s.autenticar("contacto@elbuensabor.mx", "incorrecta"))
        self.assertIsNone(s.autenticar("nadie@x.mx", "claveComercializadora2024"))

    def test_registrar_fundacion(self):
        s = nuevo_sistema()
        u = s.registrar_usuario("fundacion", "Comedor Vida", "vida@comedor.org", "secreto1",
                                "secreto1", "Iztapalapa", capacidad_kg="120")
        self.assertIsInstance(u, Fundacion)
        self.assertEqual(u.capacidad_kg, 120.0)
        self.assertIs(s.autenticar("vida@comedor.org", "secreto1"), u)
        self.assertNotEqual(u._contrasena, "secreto1")

    def test_registrar_comercializadora(self):
        s = nuevo_sistema()
        u = s.registrar_usuario("comercializadora", "Cocina Nueva", "cocina@nueva.mx", "clave123",
                                "clave123", "Coyoacán", razon_social="Cocina Nueva S.A.")
        self.assertIsInstance(u, Comercializadora)
        self.assertEqual(u.razon_social, "Cocina Nueva S.A.")
        self.assertIs(s.autenticar("cocina@nueva.mx", "clave123"), u)

    def test_cuentas_registradas_se_conservan_en_sqlite(self):
        with tempfile.TemporaryDirectory() as carpeta:
            db = os.path.join(carpeta, "foodshare.sqlite3")
            primero = Sistema(fecha_actual=HOY, db_path=db)
            creada = primero.registrar_usuario(
                "fundacion", "Comedor Persistente", "persistente@comedor.org",
                "clave123", "clave123", "Iztapalapa", capacidad_kg="80"
            )
            creada_com = primero.registrar_usuario(
                "comercializadora", "Distribuidora Persistente", "ventas@distribuidora.mx",
                "clave456", "clave456", "Azcapotzalco", razon_social="Distribuidora Persistente S.A. de C.V."
            )
            segundo = Sistema(fecha_actual=HOY, db_path=db)
            recuperada = segundo.buscar_por_correo("PERSISTENTE@COMEDOR.ORG")
            recuperada_com = segundo.buscar_por_correo("VENTAS@DISTRIBUIDORA.MX")
            self.assertIsNotNone(recuperada)
            self.assertEqual(recuperada.id_usuario, creada.id_usuario)
            self.assertEqual(recuperada.rol, "fundacion")
            self.assertIsNotNone(segundo.autenticar("persistente@comedor.org", "clave123"))
            self.assertIsNotNone(recuperada_com)
            self.assertEqual(recuperada_com.id_usuario, creada_com.id_usuario)
            self.assertEqual(recuperada_com.rol, "comercializadora")
            self.assertIsNotNone(segundo.autenticar("ventas@distribuidora.mx", "clave456"))

    def test_registro_valida_datos(self):
        s = nuevo_sistema()
        casos = [
            ("comercializadora", "contacto@elbuensabor.mx", "secreto1", "secreto1", "Razón"),  # correo repetido
            ("comercializadora", "nuevo@r.mx", "secreto1", "otra-cosa", "Razón"),             # no coinciden
            ("comercializadora", "nuevo@r.mx", "123", "123", "Razón"),                        # muy corta
            ("comercializadora", "nuevo@r.mx", "secreto1", "secreto1", ""),                   # sin razón social
            ("admin", "nuevo@r.mx", "secreto1", "secreto1", "Razón"),                    # tipo no permitido
        ]
        for tipo, correo, c1, c2, razon in casos:
            with self.subTest(tipo=tipo, correo=correo):
                with self.assertRaises(ErrorFoodShare):
                    s.registrar_usuario(tipo, "Nuevo", correo, c1, c2, "CDMX", razon_social=razon)


class PruebasDonacion(unittest.TestCase):
    def test_alimento_valida_datos(self):
        with self.assertRaises(ErrorFoodShare):
            Alimento("", 5, "25/10/2026")
        with self.assertRaises(ErrorFoodShare):
            Alimento("Pan", 0, "25/10/2026")
        with self.assertRaises(ErrorFoodShare):
            Alimento("Pan", "abc", "25/10/2026")
        with self.assertRaises(ErrorFoodShare):
            Alimento("Pan", 5, "2026-10-25")

    def test_informacion_nutricional_se_conserva_en_el_alimento(self):
        alimento = Alimento("Avena", 2, fecha_en(8), "150 kcal, proteína 5 g, fibra 4 g")
        self.assertEqual(alimento.nutrientes, "150 kcal, proteína 5 g, fibra 4 g")

    def test_calculos_de_donacion(self):
        s = nuevo_sistema()
        d = Donacion("DON900", [Alimento("Sopa", 12, fecha_en(9)),
                                Alimento("Ensalada", 8.5, fecha_en(8))],
                     s.obtener_usuario("U01"), HOY)
        self.assertEqual(d.peso_total, 20.5)
        self.assertEqual(d.str_vencimiento, fecha_en(8))
        self.assertEqual(d.descripcion, "Sopa y Ensalada")
        self.assertEqual(d.estado, Estado.PENDIENTE)

    def test_transicion_invalida(self):
        s = nuevo_sistema()
        recibida = s.obtener_donacion("DON022")
        with self.assertRaises(ErrorFoodShare):
            recibida.cambiar_estado(Estado.DISPONIBLE)


class PruebasFlujoCompleto(unittest.TestCase):
    def setUp(self):
        self.s = nuevo_sistema()
        self.comercializadora = self.s.obtener_usuario("U01")
        self.fundacion = self.s.obtener_usuario("U02")
        self.admin = self.s.obtener_usuario("U03")

    def test_datos_demo(self):
        r = self.s.resumen_general()
        self.assertEqual((r["pendientes"], r["disponibles"], r["reservadas"], r["recibidas"]), (1, 3, 2, 1))
        self.assertEqual(r["kg_disponibles"], 64.0)
        self.assertEqual(self.s.resumen_fundacion(self.fundacion), {"activas": 2, "kg_por_recibir": 43.5})

    def test_publicar_validar_reservar_recibir(self):
        d = self.s.publicar_donacion(self.comercializadora, [Alimento("Ensalada de frutas", 8.5, fecha_en(8)),
                                                         Alimento("Sopa de verduras", 12, fecha_en(9))])
        self.assertEqual(d.id_donacion, "DON029")
        self.assertEqual(d.estado, Estado.PENDIENTE)

        self.s.aprobar_donacion(self.admin, "DON029")
        self.assertEqual(d.estado, Estado.DISPONIBLE)

        self.s.reservar_donacion(self.fundacion, "DON029")
        self.assertEqual(d.estado, Estado.RESERVADA)
        self.assertIs(d.reservado_por, self.fundacion)

        self.s.marcar_recibida(self.fundacion, "DON029")
        self.assertEqual(d.estado, Estado.RECIBIDA)
        self.assertEqual(d.fecha_recepcion, HOY)
        self.assertEqual(self.s.siguiente_id(), "DON030")

    def test_rechazar(self):
        self.s.rechazar_donacion(self.admin, "DON025")
        self.assertEqual(self.s.obtener_donacion("DON025").estado, Estado.RECHAZADA)
        with self.assertRaises(ErrorFoodShare):
            self.s.aprobar_donacion(self.admin, "DON025")

    def test_permisos_por_rol(self):
        with self.assertRaises(ErrorFoodShare):
            self.s.aprobar_donacion(self.comercializadora, "DON025")
        with self.assertRaises(ErrorFoodShare):
            self.s.reservar_donacion(self.admin, "DON027")
        with self.assertRaises(ErrorFoodShare):
            self.s.publicar_donacion(self.fundacion, [Alimento("Pan", 1, fecha_en(8))])

    def test_no_se_reserva_lo_no_disponible(self):
        for id_donacion in ("DON025", "DON028", "DON022", "DON021"):
            with self.subTest(id_donacion=id_donacion):
                with self.assertRaises(ErrorFoodShare):
                    self.s.reservar_donacion(self.fundacion, id_donacion)

    def test_solo_quien_reservo_marca_recibida(self):
        otra = self.s.registrar_usuario("fundacion", "Otra", "otra@f.org", "secreto1", "secreto1",
                                        "CDMX", capacidad_kg=100)
        with self.assertRaises(ErrorFoodShare):
            self.s.marcar_recibida(otra, "DON028")

    def test_capacidad_de_la_fundacion(self):
        chica = self.s.registrar_usuario("fundacion", "Chica", "chica@f.org", "secreto1", "secreto1",
                                         "CDMX", capacidad_kg=25)
        self.s.reservar_donacion(chica, "DON027")          # 20 kg: cabe
        with self.assertRaises(ErrorFoodShare):
            self.s.reservar_donacion(chica, "DON026")      # 20 + 12 > 25

    def test_no_se_publica_comida_caducada(self):
        with self.assertRaises(ErrorFoodShare):
            self.s.publicar_donacion(self.comercializadora, [Alimento("Pan", 2, fecha_en(-1))])
        with self.assertRaises(ErrorFoodShare):
            self.s.publicar_donacion(self.comercializadora, [])

    def test_fecha_caducidad_debe_tener_al_menos_siete_dias(self):
        alimento_valido = Alimento("Frijol", 4, fecha_en(7))
        self.assertTrue(self.s.validar_fecha_caducidad(alimento_valido))
        alimento_corto = Alimento("Leche", 4, fecha_en(6))
        with self.assertRaises(ErrorFoodShare):
            self.s.validar_fecha_caducidad(alimento_corto)

    def test_alertas_para_fundacion(self):
        alertas = self.s.alertas_fundacion(self.fundacion)
        self.assertTrue(any(a["tipo"] == "disponible" for a in alertas))
        with self.assertRaises(ErrorFoodShare):
            self.s.alertas_fundacion(self.comercializadora)

    def test_alerta_de_reserva_proxima_a_caducar(self):
        donacion = self.s.publicar_donacion(
            self.comercializadora, [Alimento("Sopa", 1, fecha_en(7))])
        self.s.aprobar_donacion(self.admin, donacion.id_donacion)
        self.s.reservar_donacion(self.fundacion, donacion.id_donacion)
        donacion.alimentos[0].fecha_vencimiento = HOY + timedelta(days=2)
        alertas = self.s.alertas_fundacion(self.fundacion)
        self.assertTrue(any(a["tipo"] == "aviso" and a["donacion"] is donacion for a in alertas))

    def test_vencimiento_automatico(self):
        s = Sistema(fecha_actual=HOY + timedelta(days=11))
        # DON024 y DON026 ya superaron su fecha; DON025 todavía no ha caducado.
        self.assertEqual(s.obtener_donacion("DON024").estado, Estado.VENCIDA)
        self.assertEqual(s.obtener_donacion("DON026").estado, Estado.VENCIDA)
        self.assertEqual(s.obtener_donacion("DON025").estado, Estado.PENDIENTE)
        # Lo reservado no vence automáticamente: ya tiene quién lo recoja.
        self.assertEqual(s.obtener_donacion("DON028").estado, Estado.RESERVADA)

    def test_filtrar(self):
        todas = self.s.todas_las_donaciones()
        self.assertEqual([d.id_donacion for d in self.s.filtrar(todas, "pan")], ["DON026", "DON022"])
        self.assertEqual(len(self.s.filtrar(todas, "", Estado.DISPONIBLE)), 3)
        self.assertEqual(len(self.s.filtrar(todas, "buen sabor", Estado.RESERVADA)), 1)


if __name__ == "__main__":
    unittest.main()
