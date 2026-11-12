"""Medición de rendimiento: estructuras avanzadas vs. búsqueda lineal."""
import math
import random
import timeit

from biblioteca import Biblioteca, Libro

PALABRAS = ["sol", "luna", "mar", "rio", "casa", "noche", "dia", "tierra", "fuego", "viento"]
GENEROS = ["novela", "ensayo", "poesia", "historia", "ciencia", "cuento"]


def construir(n, semilla=42):
    random.seed(semilla)
    b = Biblioteca()
    for i in range(n):
        b.agregar(Libro(f"ISBN{i:07d}",
                        f"{random.choice(PALABRAS)} {random.choice(PALABRAS)} {i}",
                        f"Autor {random.randint(1, n // 20 + 1)}",
                        random.randint(1900, 2025),
                        frozenset(random.sample(GENEROS, 2))))
    return b


def medir(f, repeticiones):
    return min(timeit.repeat(f, number=repeticiones, repeat=5)) / repeticiones * 1e6  # µs


def main():
    print("n,operacion,estructura_us,lineal_us,aceleracion")
    for n in (1_000, 10_000, 100_000):
        b = construir(n)
        objetivo = f"ISBN{n // 2:07d}"
        rep = 2000 if n <= 10_000 else 200
        rep_lin = 50 if n <= 10_000 else 5

        filas = [
            ("ISBN exacto (hash vs lineal)",
             lambda: b.buscar_isbn(objetivo),
             lambda: b.buscar_lineal(lambda l: l.isbn == objetivo)),
            ("Año exacto (AVL vs lineal)",
             lambda: b.buscar_anio(1987),
             lambda: b.buscar_lineal(lambda l: l.anio == 1987)),
            ("Rango 1980-1985 (AVL vs lineal)",
             lambda: b.buscar_rango_anios(1980, 1985),
             lambda: b.buscar_lineal(lambda l: 1980 <= l.anio <= 1985)),
            ("Prefijo 'luna mar 1' (Trie vs lineal)",
             lambda: b.buscar_prefijo("luna mar 1"),
             lambda: b.buscar_lineal(lambda l: l.titulo.startswith("luna mar 1"))),
            ("Autor + género (conjuntos vs lineal)",
             lambda: b.buscar_avanzada(autor="Autor 3", generos=["novela"]),
             lambda: b.buscar_lineal(lambda l: l.autor == "Autor 3" and "novela" in l.generos)),
        ]
        for nombre, f_est, f_lin in filas:
            te = medir(f_est, rep)
            tl = medir(f_lin, rep_lin)
            print(f"{n},{nombre},{te:.2f},{tl:.2f},{tl / te:.1f}")
        print(f"# n={n}: nodos AVL={len(b.indice_anio)} altura AVL={b.indice_anio.altura} "
              f"log2(nodos)={math.log2(len(b.indice_anio)):.2f}")

    # altura del AVL con claves únicas (peor caso de un BST: inserción ordenada)
    from biblioteca import ArbolAVL
    print("\nn_claves,altura_avl,log2n,cota_1.44log2n")
    for n in (1_000, 10_000, 100_000, 1_000_000):
        t = ArbolAVL()
        for k in range(n):
            t.insertar(k, k)
        print(f"{n},{t.altura},{math.log2(n):.2f},{1.44 * math.log2(n + 2):.2f}")


if __name__ == "__main__":
    main()
