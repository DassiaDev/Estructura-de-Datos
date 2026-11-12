"""
Sistema de Gestión de Biblioteca (caso práctico)
=================================================
Estructuras de datos avanzadas utilizadas:
  * Árbol AVL      -> índice ordenado por año de publicación (búsqueda exacta y por rango)
  * Trie           -> índice de títulos para búsqueda por prefijo (autocompletado)
  * Diccionarios   -> catálogo principal ISBN -> Libro, préstamos por usuario
  * Conjuntos      -> índices invertidos por autor y género, control de disponibilidad

Autor del caso: reporte técnico de Estructuras de Datos Avanzadas.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional


# --------------------------------------------------------------------------- #
#  Modelo de datos
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Libro:
    isbn: str
    titulo: str
    autor: str
    anio: int
    generos: frozenset = field(default_factory=frozenset)


# --------------------------------------------------------------------------- #
#  Árbol AVL (árbol binario de búsqueda auto-balanceado)
# --------------------------------------------------------------------------- #
class _NodoAVL:
    __slots__ = ("clave", "valores", "izq", "der", "altura")

    def __init__(self, clave):
        self.clave = clave
        self.valores: set = set()      # varios libros pueden compartir año
        self.izq: Optional[_NodoAVL] = None
        self.der: Optional[_NodoAVL] = None
        self.altura = 1


class ArbolAVL:
    """AVL cuyas claves son comparables y cada nodo guarda un conjunto de valores."""

    def __init__(self):
        self.raiz: Optional[_NodoAVL] = None
        self._nodos = 0

    # ---- utilidades internas ------------------------------------------------
    @staticmethod
    def _h(n):
        return n.altura if n else 0

    def _actualizar(self, n):
        n.altura = 1 + max(self._h(n.izq), self._h(n.der))

    def _balance(self, n):
        return self._h(n.izq) - self._h(n.der) if n else 0

    def _rot_der(self, y):
        x = y.izq
        y.izq = x.der
        x.der = y
        self._actualizar(y)
        self._actualizar(x)
        return x

    def _rot_izq(self, x):
        y = x.der
        x.der = y.izq
        y.izq = x
        self._actualizar(x)
        self._actualizar(y)
        return y

    def _rebalancear(self, n):
        self._actualizar(n)
        b = self._balance(n)
        if b > 1:                                   # cargado a la izquierda
            if self._balance(n.izq) < 0:            # caso Izq-Der
                n.izq = self._rot_izq(n.izq)
            return self._rot_der(n)                 # caso Izq-Izq
        if b < -1:                                  # cargado a la derecha
            if self._balance(n.der) > 0:            # caso Der-Izq
                n.der = self._rot_der(n.der)
            return self._rot_izq(n)                 # caso Der-Der
        return n

    # ---- inserción ----------------------------------------------------------
    def insertar(self, clave, valor):
        self.raiz = self._insertar(self.raiz, clave, valor)

    def _insertar(self, n, clave, valor):
        if n is None:
            nuevo = _NodoAVL(clave)
            nuevo.valores.add(valor)
            self._nodos += 1
            return nuevo
        if clave < n.clave:
            n.izq = self._insertar(n.izq, clave, valor)
        elif clave > n.clave:
            n.der = self._insertar(n.der, clave, valor)
        else:
            n.valores.add(valor)
            return n
        return self._rebalancear(n)

    # ---- eliminación --------------------------------------------------------
    def eliminar(self, clave, valor):
        self.raiz = self._eliminar(self.raiz, clave, valor)

    def _eliminar(self, n, clave, valor):
        if n is None:
            return None
        if clave < n.clave:
            n.izq = self._eliminar(n.izq, clave, valor)
        elif clave > n.clave:
            n.der = self._eliminar(n.der, clave, valor)
        else:
            n.valores.discard(valor)
            if n.valores:                     # aún quedan libros con ese año
                return n
            self._nodos -= 1
            if n.izq is None:
                return n.der
            if n.der is None:
                return n.izq
            suc = n.der                       # sucesor in-orden
            while suc.izq:
                suc = suc.izq
            n.clave, n.valores = suc.clave, set(suc.valores)
            n.der = self._eliminar_nodo(n.der, suc.clave)
        return self._rebalancear(n)

    def _eliminar_nodo(self, n, clave):
        """Elimina el nodo completo con `clave` (usado al mover el sucesor)."""
        if clave < n.clave:
            n.izq = self._eliminar_nodo(n.izq, clave)
        elif clave > n.clave:
            n.der = self._eliminar_nodo(n.der, clave)
        else:
            return n.der                      # el sucesor nunca tiene hijo izq
        return self._rebalancear(n)

    # ---- búsquedas ----------------------------------------------------------
    def buscar(self, clave) -> set:
        """Búsqueda binaria en el árbol: O(log n)."""
        n = self.raiz
        while n:
            if clave == n.clave:
                return set(n.valores)
            n = n.izq if clave < n.clave else n.der
        return set()

    def rango(self, minimo, maximo) -> list:
        """Recorrido in-orden podado: O(log n + k)."""
        res: list = []
        self._rango(self.raiz, minimo, maximo, res)
        return res

    def _rango(self, n, lo, hi, res):
        if n is None:
            return
        if lo < n.clave:
            self._rango(n.izq, lo, hi, res)
        if lo <= n.clave <= hi:
            res.append((n.clave, set(n.valores)))
        if n.clave < hi:
            self._rango(n.der, lo, hi, res)

    def inorden(self) -> Iterator:
        pila, n = [], self.raiz
        while pila or n:
            while n:
                pila.append(n)
                n = n.izq
            n = pila.pop()
            yield n.clave, n.valores
            n = n.der

    # ---- métricas / validación ---------------------------------------------
    @property
    def altura(self):
        return self._h(self.raiz)

    def __len__(self):
        return self._nodos

    def es_valido(self) -> bool:
        """Verifica propiedad de BST, alturas y factor de balance |b| <= 1."""
        def chequear(n, lo, hi):
            if n is None:
                return True, 0
            if (lo is not None and n.clave <= lo) or (hi is not None and n.clave >= hi):
                return False, 0
            ok_i, h_i = chequear(n.izq, lo, n.clave)
            ok_d, h_d = chequear(n.der, n.clave, hi)
            h = 1 + max(h_i, h_d)
            return ok_i and ok_d and abs(h_i - h_d) <= 1 and n.altura == h, h
        return chequear(self.raiz, None, None)[0]


# --------------------------------------------------------------------------- #
#  Trie (árbol de prefijos)
# --------------------------------------------------------------------------- #
class _NodoTrie:
    __slots__ = ("hijos", "isbns")

    def __init__(self):
        self.hijos: dict[str, _NodoTrie] = {}   # diccionario de hijos
        self.isbns: set[str] = set()            # libros cuyo título termina aquí


class Trie:
    def __init__(self):
        self.raiz = _NodoTrie()

    @staticmethod
    def _normalizar(texto: str) -> str:
        tabla = str.maketrans("áéíóúüñ", "aeiouun")
        return texto.lower().translate(tabla).strip()

    def insertar(self, texto: str, isbn: str):
        n = self.raiz
        for c in self._normalizar(texto):
            n = n.hijos.setdefault(c, _NodoTrie())
        n.isbns.add(isbn)

    def eliminar(self, texto: str, isbn: str):
        camino, n = [], self.raiz
        for c in self._normalizar(texto):
            if c not in n.hijos:
                return
            camino.append((n, c))
            n = n.hijos[c]
        n.isbns.discard(isbn)
        # poda de ramas vacías
        for padre, c in reversed(camino):
            hijo = padre.hijos[c]
            if hijo.isbns or hijo.hijos:
                break
            del padre.hijos[c]

    def con_prefijo(self, prefijo: str) -> set[str]:
        """Devuelve todos los ISBN cuyo título empieza con `prefijo`: O(m + k)."""
        n = self.raiz
        for c in self._normalizar(prefijo):
            n = n.hijos.get(c)
            if n is None:
                return set()
        res, pila = set(), [n]
        while pila:                               # DFS iterativo
            actual = pila.pop()
            res |= actual.isbns
            pila.extend(actual.hijos.values())
        return res


# --------------------------------------------------------------------------- #
#  Fachada: Biblioteca
# --------------------------------------------------------------------------- #
class ErrorBiblioteca(Exception):
    pass


class Biblioteca:
    def __init__(self):
        self.catalogo: dict[str, Libro] = {}            # ISBN -> Libro
        self.por_autor: dict[str, set[str]] = {}        # autor -> {ISBN}
        self.por_genero: dict[str, set[str]] = {}       # género -> {ISBN}
        self.prestados: set[str] = set()                # ISBN prestados
        self.prestamos: dict[str, set[str]] = {}        # usuario -> {ISBN}
        self.indice_anio = ArbolAVL()                   # año -> {ISBN}
        self.indice_titulo = Trie()                     # prefijo título -> {ISBN}

    # ---- altas y bajas ------------------------------------------------------
    def agregar(self, libro: Libro):
        if libro.isbn in self.catalogo:
            raise ErrorBiblioteca(f"ISBN duplicado: {libro.isbn}")
        self.catalogo[libro.isbn] = libro
        self.por_autor.setdefault(libro.autor.lower(), set()).add(libro.isbn)
        for g in libro.generos:
            self.por_genero.setdefault(g.lower(), set()).add(libro.isbn)
        self.indice_anio.insertar(libro.anio, libro.isbn)
        self.indice_titulo.insertar(libro.titulo, libro.isbn)

    def eliminar(self, isbn: str):
        libro = self.catalogo.get(isbn)
        if libro is None:
            raise ErrorBiblioteca(f"ISBN inexistente: {isbn}")
        if isbn in self.prestados:
            raise ErrorBiblioteca("No se puede eliminar un libro prestado")
        del self.catalogo[isbn]
        self._quitar(self.por_autor, libro.autor.lower(), isbn)
        for g in libro.generos:
            self._quitar(self.por_genero, g.lower(), isbn)
        self.indice_anio.eliminar(libro.anio, isbn)
        self.indice_titulo.eliminar(libro.titulo, isbn)

    @staticmethod
    def _quitar(indice: dict, clave: str, isbn: str):
        s = indice.get(clave)
        if s is not None:
            s.discard(isbn)
            if not s:
                del indice[clave]

    # ---- métodos de búsqueda -----------------------------------------------
    def buscar_isbn(self, isbn: str) -> Optional[Libro]:
        """Búsqueda por tabla hash: O(1) promedio."""
        return self.catalogo.get(isbn)

    def buscar_anio(self, anio: int) -> list[Libro]:
        """Búsqueda binaria en AVL: O(log n)."""
        return self._libros(self.indice_anio.buscar(anio))

    def buscar_rango_anios(self, desde: int, hasta: int) -> list[Libro]:
        """Búsqueda por rango en AVL, resultado ordenado por año."""
        res = []
        for _, isbns in self.indice_anio.rango(desde, hasta):
            res.extend(sorted(self._libros(isbns), key=lambda l: l.titulo))
        return res

    def buscar_prefijo(self, prefijo: str) -> list[Libro]:
        """Búsqueda por prefijo de título con Trie: O(m + k)."""
        return sorted(self._libros(self.indice_titulo.con_prefijo(prefijo)),
                      key=lambda l: l.titulo)

    def buscar_avanzada(self, autor: str | None = None, generos: list[str] | None = None,
                        solo_disponibles: bool = False, modo_generos: str = "todos"):
        """Combina índices con operaciones de conjuntos (∩, ∪, −).

        Optimización: se intersecan los conjuntos empezando por el MÁS PEQUEÑO;
        el costo de A ∩ B en Python es O(min(|A|, |B|)), así que nunca se copia
        el catálogo completo salvo que no haya ningún filtro.
        """
        filtros: list[set[str]] = []
        if autor:
            filtros.append(self.por_autor.get(autor.lower(), set()))
        if generos:
            conjuntos = [self.por_genero.get(g.lower(), set()) for g in generos]
            if modo_generos == "todos":
                filtros.extend(conjuntos)
            else:
                filtros.append(set().union(*conjuntos))
        if filtros:
            filtros.sort(key=len)
            candidatos = set(filtros[0])
            for s in filtros[1:]:
                if not candidatos:
                    break
                candidatos &= s
        else:
            candidatos = set(self.catalogo)
        if solo_disponibles:
            candidatos -= self.prestados
        return sorted(self._libros(candidatos), key=lambda l: l.titulo)

    def buscar_lineal(self, predicado) -> list[Libro]:
        """Búsqueda secuencial de referencia: O(n)."""
        return [l for l in self.catalogo.values() if predicado(l)]

    # ---- préstamos ----------------------------------------------------------
    def prestar(self, isbn: str, usuario: str, limite: int = 3):
        if isbn not in self.catalogo:
            raise ErrorBiblioteca(f"ISBN inexistente: {isbn}")
        if isbn in self.prestados:
            raise ErrorBiblioteca("El libro ya está prestado")
        actuales = self.prestamos.setdefault(usuario, set())
        if len(actuales) >= limite:
            raise ErrorBiblioteca(f"El usuario {usuario} alcanzó el límite de {limite}")
        actuales.add(isbn)
        self.prestados.add(isbn)

    def devolver(self, isbn: str, usuario: str):
        actuales = self.prestamos.get(usuario, set())
        if isbn not in actuales:
            raise ErrorBiblioteca("Ese usuario no tiene prestado ese libro")
        actuales.discard(isbn)
        self.prestados.discard(isbn)
        if not actuales:
            del self.prestamos[usuario]

    def disponibles(self) -> set[str]:
        return set(self.catalogo) - self.prestados

    # ---- utilidades ---------------------------------------------------------
    def _libros(self, isbns) -> list[Libro]:
        return [self.catalogo[i] for i in isbns if i in self.catalogo]

    def __len__(self):
        return len(self.catalogo)


# --------------------------------------------------------------------------- #
#  Demostración
# --------------------------------------------------------------------------- #
DATOS_DEMO = [
    Libro("978-0307474728", "Cien años de soledad", "Gabriel García Márquez", 1967,
          frozenset({"novela", "realismo mágico"})),
    Libro("978-0307389732", "El amor en los tiempos del cólera", "Gabriel García Márquez", 1985,
          frozenset({"novela", "romance"})),
    Libro("978-6070728792", "Pedro Páramo", "Juan Rulfo", 1955,
          frozenset({"novela", "realismo mágico"})),
    Libro("978-8437604183", "El llano en llamas", "Juan Rulfo", 1953,
          frozenset({"cuento"})),
    Libro("978-0451524935", "1984", "George Orwell", 1949,
          frozenset({"novela", "ciencia ficción", "distopía"})),
    Libro("978-0060850524", "Un mundo feliz", "Aldous Huxley", 1932,
          frozenset({"novela", "ciencia ficción", "distopía"})),
    Libro("978-0262033848", "Introduction to Algorithms", "Thomas H. Cormen", 2009,
          frozenset({"computación", "algoritmos"})),
    Libro("978-0321573513", "Algorithms", "Robert Sedgewick", 2011,
          frozenset({"computación", "algoritmos"})),
    Libro("978-8420471839", "El laberinto de la soledad", "Octavio Paz", 1950,
          frozenset({"ensayo"})),
    Libro("978-6073143202", "Como agua para chocolate", "Laura Esquivel", 1989,
          frozenset({"novela", "realismo mágico", "romance"})),
]


def demo():
    b = Biblioteca()
    for libro in DATOS_DEMO:
        b.agregar(libro)

    print(f"Libros en catálogo: {len(b)} | nodos AVL: {len(b.indice_anio)} "
          f"| altura AVL: {b.indice_anio.altura}")
    print("\n[Hash] ISBN 978-6070728792 ->", b.buscar_isbn("978-6070728792").titulo)
    print("\n[AVL] Libros publicados entre 1950 y 1970:")
    for l in b.buscar_rango_anios(1950, 1970):
        print(f"   {l.anio}  {l.titulo} — {l.autor}")
    print("\n[Trie] Títulos que empiezan con 'el':")
    for l in b.buscar_prefijo("el"):
        print("   ", l.titulo)
    print("\n[Conjuntos] Novelas de realismo mágico:")
    for l in b.buscar_avanzada(generos=["novela", "realismo mágico"]):
        print("   ", l.titulo)
    b.prestar("978-0307474728", "ana")
    print("\n[Conjuntos] Realismo mágico disponible tras prestar 'Cien años de soledad':")
    for l in b.buscar_avanzada(generos=["realismo mágico"], solo_disponibles=True):
        print("   ", l.titulo)


if __name__ == "__main__":
    demo()
