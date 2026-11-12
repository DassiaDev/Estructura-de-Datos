"""Pruebas unitarias del sistema de biblioteca (unittest)."""
import random
import unittest

from biblioteca import ArbolAVL, Biblioteca, DATOS_DEMO, ErrorBiblioteca, Libro, Trie


class PruebasAVL(unittest.TestCase):
    def test_insercion_ascendente_mantiene_balance(self):
        """Peor caso de un BST normal (datos ordenados): el AVL debe seguir balanceado."""
        t = ArbolAVL()
        for i in range(1, 1024):
            t.insertar(i, i)
        self.assertTrue(t.es_valido())
        self.assertEqual(t.altura, 10)            # 2^10 - 1 = 1023 nodos -> árbol perfecto

    def test_rotaciones_cuatro_casos(self):
        for secuencia in ([3, 2, 1], [1, 2, 3], [3, 1, 2], [1, 3, 2]):  # II, DD, ID, DI
            t = ArbolAVL()
            for k in secuencia:
                t.insertar(k, k)
            self.assertEqual(t.raiz.clave, 2, secuencia)
            self.assertTrue(t.es_valido())

    def test_insercion_y_eliminacion_aleatoria(self):
        random.seed(7)
        t, vivos = ArbolAVL(), set()
        for _ in range(5000):
            k = random.randint(0, 2000)
            if k in vivos and random.random() < 0.5:
                t.eliminar(k, k)
                vivos.discard(k)
            else:
                t.insertar(k, k)
                vivos.add(k)
        self.assertTrue(t.es_valido())
        self.assertEqual(len(t), len(vivos))
        self.assertEqual([k for k, _ in t.inorden()], sorted(vivos))

    def test_claves_repetidas_agrupan_valores(self):
        t = ArbolAVL()
        t.insertar(1967, "a")
        t.insertar(1967, "b")
        self.assertEqual(len(t), 1)
        self.assertEqual(t.buscar(1967), {"a", "b"})
        t.eliminar(1967, "a")
        self.assertEqual(t.buscar(1967), {"b"})

    def test_rango(self):
        t = ArbolAVL()
        for k in range(0, 100, 5):
            t.insertar(k, k)
        self.assertEqual([k for k, _ in t.rango(12, 31)], [15, 20, 25, 30])
        self.assertEqual(t.rango(200, 300), [])

    def test_buscar_inexistente(self):
        t = ArbolAVL()
        self.assertEqual(t.buscar(5), set())
        t.insertar(1, 1)
        self.assertEqual(t.buscar(5), set())


class PruebasTrie(unittest.TestCase):
    def setUp(self):
        self.t = Trie()
        self.t.insertar("El llano en llamas", "1")
        self.t.insertar("El laberinto de la soledad", "2")
        self.t.insertar("Pedro Páramo", "3")

    def test_prefijo(self):
        self.assertEqual(self.t.con_prefijo("el l"), {"1", "2"})
        self.assertEqual(self.t.con_prefijo("el la"), {"2"})

    def test_insensible_a_mayusculas_y_acentos(self):
        self.assertEqual(self.t.con_prefijo("PEDRO PARA"), {"3"})
        self.assertEqual(self.t.con_prefijo("pedro pára"), {"3"})

    def test_sin_coincidencias(self):
        self.assertEqual(self.t.con_prefijo("zzz"), set())

    def test_eliminar_poda_ramas(self):
        self.t.eliminar("Pedro Páramo", "3")
        self.assertEqual(self.t.con_prefijo("p"), set())
        self.assertNotIn("p", self.t.raiz.hijos)


class PruebasBiblioteca(unittest.TestCase):
    def setUp(self):
        self.b = Biblioteca()
        for libro in DATOS_DEMO:
            self.b.agregar(libro)

    def test_busqueda_hash(self):
        self.assertEqual(self.b.buscar_isbn("978-0451524935").titulo, "1984")
        self.assertIsNone(self.b.buscar_isbn("000"))

    def test_isbn_duplicado(self):
        with self.assertRaises(ErrorBiblioteca):
            self.b.agregar(DATOS_DEMO[0])

    def test_rango_anios_ordenado(self):
        res = self.b.buscar_rango_anios(1950, 1970)
        self.assertEqual([l.anio for l in res], [1950, 1953, 1955, 1967])

    def test_prefijo(self):
        titulos = [l.titulo for l in self.b.buscar_prefijo("el")]
        self.assertEqual(titulos, ["El amor en los tiempos del cólera",
                                   "El laberinto de la soledad", "El llano en llamas"])

    def test_interseccion_generos(self):
        res = {l.titulo for l in self.b.buscar_avanzada(generos=["novela", "realismo mágico"])}
        self.assertEqual(res, {"Cien años de soledad", "Pedro Páramo", "Como agua para chocolate"})

    def test_union_generos(self):
        res = self.b.buscar_avanzada(generos=["ensayo", "cuento"], modo_generos="alguno")
        self.assertEqual(len(res), 2)

    def test_autor_y_genero(self):
        res = self.b.buscar_avanzada(autor="Gabriel García Márquez", generos=["romance"])
        self.assertEqual([l.titulo for l in res], ["El amor en los tiempos del cólera"])

    def test_prestamo_diferencia_conjuntos(self):
        self.b.prestar("978-0307474728", "ana")
        res = {l.titulo for l in self.b.buscar_avanzada(generos=["realismo mágico"],
                                                        solo_disponibles=True)}
        self.assertNotIn("Cien años de soledad", res)
        self.assertEqual(len(self.b.disponibles()), len(DATOS_DEMO) - 1)

    def test_prestamo_doble_falla(self):
        self.b.prestar("978-0307474728", "ana")
        with self.assertRaises(ErrorBiblioteca):
            self.b.prestar("978-0307474728", "luis")

    def test_limite_prestamos(self):
        for isbn in ["978-0307474728", "978-0307389732", "978-6070728792"]:
            self.b.prestar(isbn, "ana")
        with self.assertRaises(ErrorBiblioteca):
            self.b.prestar("978-8437604183", "ana")

    def test_devolucion(self):
        self.b.prestar("978-0307474728", "ana")
        self.b.devolver("978-0307474728", "ana")
        self.assertNotIn("978-0307474728", self.b.prestados)
        self.assertNotIn("ana", self.b.prestamos)
        with self.assertRaises(ErrorBiblioteca):
            self.b.devolver("978-0307474728", "ana")

    def test_eliminar_actualiza_todos_los_indices(self):
        self.b.eliminar("978-6070728792")  # Pedro Páramo, 1955
        self.assertIsNone(self.b.buscar_isbn("978-6070728792"))
        self.assertEqual(self.b.buscar_anio(1955), [])
        self.assertEqual(self.b.buscar_prefijo("pedro"), [])
        self.assertEqual([l.titulo for l in self.b.buscar_avanzada(autor="Juan Rulfo")],
                         ["El llano en llamas"])
        self.assertTrue(self.b.indice_anio.es_valido())

    def test_no_eliminar_prestado(self):
        self.b.prestar("978-0451524935", "ana")
        with self.assertRaises(ErrorBiblioteca):
            self.b.eliminar("978-0451524935")

    def test_indices_coinciden_con_busqueda_lineal(self):
        """Prueba de equivalencia: cada índice devuelve lo mismo que un recorrido O(n)."""
        random.seed(1)
        b = Biblioteca()
        palabras = ["sol", "luna", "mar", "rio", "casa", "noche", "dia", "tierra"]
        generos = ["novela", "ensayo", "poesia", "historia", "ciencia"]
        for i in range(3000):
            b.agregar(Libro(f"ISBN{i:06d}", f"{random.choice(palabras)} {random.choice(palabras)} {i}",
                            f"Autor {random.randint(1, 200)}", random.randint(1900, 2025),
                            frozenset(random.sample(generos, 2))))
        self.assertEqual({l.isbn for l in b.buscar_rango_anios(1950, 1980)},
                         {l.isbn for l in b.buscar_lineal(lambda l: 1950 <= l.anio <= 1980)})
        self.assertEqual({l.isbn for l in b.buscar_prefijo("luna m")},
                         {l.isbn for l in b.buscar_lineal(lambda l: l.titulo.startswith("luna m"))})
        self.assertEqual({l.isbn for l in b.buscar_avanzada(autor="Autor 7", generos=["novela"])},
                         {l.isbn for l in b.buscar_lineal(
                             lambda l: l.autor == "Autor 7" and "novela" in l.generos)})


if __name__ == "__main__":
    unittest.main(verbosity=2)
