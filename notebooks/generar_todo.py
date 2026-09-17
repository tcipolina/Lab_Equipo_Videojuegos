"""
Genera los datasets limpios y los graficos del proyecto EA Sports FC 26.

Hace exactamente lo mismo que el notebook 01_carga_limpieza_orden.ipynb, pero como
script suelto, para poder correrlo desde la terminal sin depender de Jupyter:

    python generar_todo.py

Salidas:
    data/processed/   -> 3 archivos CSV limpios
    output/figuras/   -> 6 imagenes PNG para las diapositivas
"""

import matplotlib
matplotlib.use("Agg")  # dibuja directo a archivo, sin abrir ventanas

import ast
import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

# Que pandas nos muestre las tablas anchas sin cortar columnas
pd.set_option("display.max_columns", 100)
pd.set_option("display.width", 200)

# Rutas del proyecto.
# Buscamos hacia arriba la carpeta que contiene "data", así el notebook funciona
# tanto si lo ejecutás desde notebooks/ como desde la raíz del repositorio.
DIR_BASE = Path.cwd()
for carpeta in [DIR_BASE, *DIR_BASE.parents]:
    if (carpeta / "data" / "raw").is_dir():
        DIR_BASE = carpeta
        break
else:
    raise FileNotFoundError(
        "No encuentro la carpeta data/raw. Revisá que estés dentro del repositorio "
        "y que los CSV estén en data/raw/."
    )

DIR_CRUDO = DIR_BASE / "data" / "raw"
DIR_LIMPIO = DIR_BASE / "data" / "processed"
DIR_LIMPIO.mkdir(parents=True, exist_ok=True)

print("Proyecto en:", DIR_BASE)
print("Datos crudos en:", DIR_CRUDO)
print("Datos limpios se guardarán en:", DIR_LIMPIO)

jugadores_crudo = pd.read_csv(DIR_CRUDO / "EAFC26.csv", encoding="utf-8")
promo_crudo = pd.read_csv(DIR_CRUDO / "FC26_Promo_Players_-_promo_cards.csv", encoding="utf-8")

print(f"Jugadores: {jugadores_crudo.shape[0]:,} filas x {jugadores_crudo.shape[1]} columnas")
print(f"Cartas promo: {promo_crudo.shape[0]:,} filas x {promo_crudo.shape[1]} columnas")

print(jugadores_crudo.head(3))
print()

# Nombres de las columnas tal como vienen del archivo
print(list(jugadores_crudo.columns))

# ¿Cuántos valores faltan en cada columna?
nulos = jugadores_crudo.isna().sum()
nulos = nulos[nulos > 0].sort_values(ascending=False)
print("Columnas con valores faltantes:\n")
print(nulos.to_string())

# ¿Hay filas repetidas?
print("Filas idénticas duplicadas:", jugadores_crudo.duplicated().sum())
print("IDs de jugador duplicados:", jugadores_crudo["ID"].duplicated().sum())

# ¿Qué tipo de dato detectó pandas en cada columna?
tipos = jugadores_crudo.dtypes.value_counts()
print(tipos.to_string())
print("\nColumnas que deberían ser números pero pandas leyó como texto:")
print(jugadores_crudo[["Height", "Weight", "Alternative positions", "play style"]].head(3).to_string())

arqueros_check = jugadores_crudo[jugadores_crudo["Position"] == "GK"]

equivalencias = {
    "PAC": "GK Diving",
    "SHO": "GK Handling",
    "PAS": "GK Kicking",
    "DRI": "GK Reflexes",
    "PHY": "GK Positioning",
}
for col_campo, col_gk in equivalencias.items():
    iguales = (arqueros_check[col_campo] == arqueros_check[col_gk]).all()
    print(f"Para arqueros, ¿{col_campo} es lo mismo que '{col_gk}'? → {iguales}")

print("\n(La columna DEF de un arquero es su velocidad/SPD: no tiene columna 'GK Speed' propia.)")

print(promo_crudo.head(5))
print()

print("Valores faltantes por columna:")
print(promo_crudo.isna().sum().to_string())
print("\nCartas por tipo de promo:")
print(promo_crudo["promo_code"].value_counts().to_string())

jugadores = jugadores_crudo.copy()
promo = promo_crudo.copy()

filas_iniciales = len(jugadores)
print(f"Partimos de {filas_iniciales:,} jugadores.")

def a_snake_case(nombre: str) -> str:
    """Convierte 'Sprint Speed' -> 'sprint_speed' y 'GK Diving' -> 'gk_diving'."""
    nombre = nombre.strip().lower()
    nombre = re.sub(r"[^\w]+", "_", nombre)  # espacios y símbolos -> guion bajo
    return nombre.strip("_")


# Algunos nombres merecen ser más explícitos que su traducción automática
RENOMBRES_ESPECIALES = {
    "id": "player_id",
    "play_style": "play_styles",
    "card": "card_image_url",
}

jugadores.columns = [a_snake_case(c) for c in jugadores.columns]
jugadores = jugadores.rename(columns=RENOMBRES_ESPECIALES)

promo.columns = [a_snake_case(c) for c in promo.columns]

print(list(jugadores.columns))

COLUMNAS_A_ELIMINAR = [
    "rank",            # fuga de información: se calcula a partir del OVR
    "url",             # link a la web de EA
    "card_image_url",  # link a la imagen de la carta
]

jugadores = jugadores.drop(columns=COLUMNAS_A_ELIMINAR)
print(f"Eliminamos {len(COLUMNAS_A_ELIMINAR)} columnas. Quedan {jugadores.shape[1]}.")

def extraer_numero(texto: str, unidad: str) -> float:
    """De '175cm / 5\\'9\"' con unidad 'cm' devuelve 175.0. Si no encuentra nada, NaN."""
    if pd.isna(texto):
        return np.nan
    encontrado = re.search(rf"(\d+)\s*{unidad}", str(texto))
    return float(encontrado.group(1)) if encontrado else np.nan


jugadores["height_cm"] = jugadores["height"].apply(lambda x: extraer_numero(x, "cm"))
jugadores["weight_kg"] = jugadores["weight"].apply(lambda x: extraer_numero(x, "kg"))

# Verificamos que no se haya roto ninguna conversión antes de borrar las originales
assert jugadores["height_cm"].notna().all(), "Hay alturas que no se pudieron convertir"
assert jugadores["weight_kg"].notna().all(), "Hay pesos que no se pudieron convertir"

jugadores = jugadores.drop(columns=["height", "weight"])

print(jugadores[["height_cm", "weight_kg"]].describe().round(1).to_string())

def texto_a_lista(valor) -> list:
    """Convierte la cadena \"['RW', 'LM']\" en la lista ['RW', 'LM']. NaN -> []."""
    if pd.isna(valor):
        return []
    if isinstance(valor, list):
        return valor
    try:
        resultado = ast.literal_eval(str(valor))
        return list(resultado) if isinstance(resultado, (list, tuple)) else []
    except (ValueError, SyntaxError):
        return []


jugadores["alternative_positions"] = jugadores["alternative_positions"].apply(texto_a_lista)
jugadores["play_styles"] = jugadores["play_styles"].apply(texto_a_lista)

# De cada lista sacamos variables numéricas, que sí se pueden analizar
jugadores["n_alternative_positions"] = jugadores["alternative_positions"].str.len()
jugadores["n_play_styles"] = jugadores["play_styles"].str.len()
# Los PlayStyle terminados en '+' son los "PlayStyle+", la versión mejorada
jugadores["n_play_styles_plus"] = jugadores["play_styles"].apply(
    lambda lista: sum(1 for ps in lista if str(ps).endswith("+"))
)

print(jugadores[["n_alternative_positions", "n_play_styles", "n_play_styles_plus"]].describe().round(2).to_string())

COLUMNAS_GK = ["gk_diving", "gk_handling", "gk_kicking", "gk_positioning", "gk_reflexes"]

print("Nulos en gk_* que NO son arqueros:",
      jugadores.loc[jugadores["position"] != "GK", COLUMNAS_GK].isna().all().all())
print("Arqueros sin datos de gk_*:",
      jugadores.loc[jugadores["position"] == "GK", COLUMNAS_GK].isna().sum().sum())

nulos_restantes = jugadores.isna().sum()
print("\nColumnas con nulos que quedan (deberían ser sólo las gk_*):")
print(nulos_restantes[nulos_restantes > 0].to_string())

dup_id = jugadores["player_id"].duplicated().sum()
dup_persona = jugadores.duplicated(subset=["name", "team", "age"]).sum()
print(f"Duplicados por player_id: {dup_id}")
print(f"Duplicados por nombre + equipo + edad: {dup_persona}")

if dup_id or dup_persona:
    jugadores = jugadores.drop_duplicates(subset=["player_id"]).reset_index(drop=True)
    print(f"→ Eliminados. Quedan {len(jugadores):,} jugadores.")
else:
    print("→ No hay duplicados que eliminar.")

ATRIBUTOS_CARA = ["pac", "sho", "pas", "dri", "def", "phy"]
ATRIBUTOS_DETALLE = [
    "acceleration", "sprint_speed", "positioning", "finishing", "shot_power",
    "long_shots", "volleys", "penalties", "vision", "crossing", "free_kick_accuracy",
    "short_passing", "long_passing", "curve", "dribbling", "agility", "balance",
    "reactions", "ball_control", "composure", "interceptions", "heading_accuracy",
    "def_awareness", "standing_tackle", "sliding_tackle", "jumping", "stamina",
    "strength", "aggression",
]
TODOS_LOS_ATRIBUTOS = ["ovr"] + ATRIBUTOS_CARA + ATRIBUTOS_DETALLE

fuera_de_rango = {
    col: int(((jugadores[col] < 0) | (jugadores[col] > 99)).sum())
    for col in TODOS_LOS_ATRIBUTOS
}
problemas = {c: n for c, n in fuera_de_rango.items() if n > 0}
print("Atributos fuera del rango 0-99:", problemas if problemas else "ninguno ✓")

print("\nEdad: de", jugadores["age"].min(), "a", jugadores["age"].max(), "años")
print("Pie preferido:", sorted(jugadores["preferred_foot"].unique()))
print("Weak foot (estrellas):", sorted(jugadores["weak_foot"].unique()))
print("Skill moves (estrellas):", sorted(jugadores["skill_moves"].unique()))

# Las variables de texto con pocos valores distintos se guardan como 'category':
# ocupan mucha menos memoria y dejan claro que son categóricas, no texto libre.
COLUMNAS_CATEGORICAS = ["gender", "position", "preferred_foot", "nation", "league", "team"]
for col in COLUMNAS_CATEGORICAS:
    jugadores[col] = jugadores[col].astype("category")

memoria_mb = jugadores.memory_usage(deep=True).sum() / 1024**2
print(f"Memoria del DataFrame: {memoria_mb:.1f} MB")
print(f"\nLigas distintas: {jugadores['league'].nunique()}")
print(f"Equipos distintos: {jugadores['team'].nunique()}")
print(f"Nacionalidades distintas: {jugadores['nation'].nunique()}")

es_arquero = jugadores["position"] == "GK"

# --- Jugadores de campo ---
campo = jugadores[~es_arquero].copy()
campo = campo.drop(columns=COLUMNAS_GK)  # estaban 100% vacías para ellos
campo["position"] = campo["position"].cat.remove_unused_categories()

# --- Arqueros ---
arqueros = jugadores[es_arquero].copy()
# Las columnas gk_* son copia exacta de pac/sho/pas/dri/phy → las quitamos
arqueros = arqueros.drop(columns=COLUMNAS_GK)
arqueros = arqueros.rename(columns={
    "pac": "gk_diving",        # DIV - estiradas
    "sho": "gk_handling",      # HAN - blocaje
    "pas": "gk_kicking",       # KIC - saque
    "dri": "gk_reflexes",      # REF - reflejos
    "def": "gk_speed",         # SPD - velocidad
    "phy": "gk_positioning",   # POS - colocación
})
arqueros["position"] = arqueros["position"].cat.remove_unused_categories()

ATRIBUTOS_CARA_GK = ["gk_diving", "gk_handling", "gk_kicking", "gk_reflexes", "gk_speed", "gk_positioning"]

print(f"Jugadores de campo: {len(campo):,}")
print(f"Arqueros:           {len(arqueros):,}")
print(f"Total:              {len(campo) + len(arqueros):,}  (original: {filas_iniciales:,})")
assert len(campo) + len(arqueros) == filas_iniciales, "¡Se perdieron filas al separar!"
print("\n✓ No se perdió ningún jugador en la separación.")

# Columnas que están 100% vacías: no aportan nada
vacias = [c for c in promo.columns if promo[c].isna().all()]
print("Columnas 100% vacías que eliminamos:", vacias)
promo = promo.drop(columns=vacias)

# La fecha de salida como fecha de verdad, no como texto
promo["release_date"] = pd.to_datetime(promo["release_date"], errors="coerce")
print("Fechas que no se pudieron convertir:", promo["release_date"].isna().sum())
print("Rango de fechas:", promo["release_date"].min().date(), "→", promo["release_date"].max().date())

# Categóricas
for col in ["promo_code", "drop_label", "team", "acquisition"]:
    promo[col] = promo[col].astype("category")

print("\nDuplicados exactos:", promo.duplicated().sum())
print("Mismo jugador en la misma promo:", promo.duplicated(subset=["player_name", "promo_code", "drop_label"]).sum())

def normalizar_nombre(nombre: str) -> str:
    """'Kylian Mbappé' -> 'kylian mbappe'. Sirve como clave para cruzar datasets."""
    if pd.isna(nombre):
        return ""
    texto = unicodedata.normalize("NFKD", str(nombre))
    texto = "".join(c for c in texto if not unicodedata.combining(c))  # saca tildes
    texto = texto.lower()
    texto = re.sub(r"[^a-z0-9 ]", " ", texto)  # saca puntos, guiones, apóstrofes
    return re.sub(r"\s+", " ", texto).strip()


promo["name_key"] = promo["player_name"].apply(normalizar_nombre)
campo["name_key"] = campo["name"].apply(normalizar_nombre)
arqueros["name_key"] = arqueros["name"].apply(normalizar_nombre)

# ¿Qué porcentaje de las cartas promo cruza con una coincidencia exacta?
claves_base = set(campo["name_key"]) | set(arqueros["name_key"])
cruzan_exacto = promo["name_key"].isin(claves_base).sum()

print(f"Coincidencia exacta: {cruzan_exacto} de {len(promo)} ({cruzan_exacto/len(promo):.1%})")
print("\nSin coincidencia exacta:")
print(sorted(set(promo.loc[~promo["name_key"].isin(claves_base), "player_name"])))

# Índice de apellidos del dataset base, para el segundo pase
apellidos_base = {}
for clave in claves_base:
    apellido = clave.split()[-1] if clave else ""
    apellidos_base.setdefault(apellido, set()).add(clave)


def buscar_carta_base(clave_promo: str) -> str | None:
    """Devuelve la clave de la carta base, o None si no hay una coincidencia segura."""
    if clave_promo in claves_base:            # 1er pase: coincidencia exacta
        return clave_promo
    apellido = clave_promo.split()[-1] if clave_promo else ""
    candidatos = apellidos_base.get(apellido, set())
    if len(candidatos) == 1:                  # 2do pase: apellido único
        return next(iter(candidatos))
    return None                               # ambiguo o inexistente → no adivinamos


promo["clave_carta_base"] = promo["name_key"].apply(buscar_carta_base)
promo["tiene_carta_base"] = promo["clave_carta_base"].notna()
cruzan = int(promo["tiene_carta_base"].sum())

print(f"Cruce final: {cruzan} de {len(promo)} cartas promo ({cruzan/len(promo):.1%})")
print(f"  · coincidencia exacta:  {cruzan_exacto}")
print(f"  · por apellido único:   {cruzan - cruzan_exacto}")
print(f"  · sin cruzar:           {len(promo) - cruzan}")

if cruzan < len(promo):
    print("\nSin cruzar (no están en el dataset base o el apellido es ambiguo):")
    print(sorted(set(promo.loc[~promo["tiene_carta_base"], "player_name"])))

BLOQUE_IDENTIDAD = ["player_id", "name", "gender", "age", "position",
                    "alternative_positions", "n_alternative_positions"]
BLOQUE_PERFIL = ["height_cm", "weight_kg", "preferred_foot", "weak_foot", "skill_moves",
                 "play_styles", "n_play_styles", "n_play_styles_plus"]
BLOQUE_CONTEXTO = ["nation", "league", "team", "name_key"]


def ordenar_columnas(df: pd.DataFrame, atributos_cara: list) -> pd.DataFrame:
    """Reordena las columnas en bloques: identidad, carta, detalle, perfil, contexto."""
    orden = (
        BLOQUE_IDENTIDAD
        + ["ovr"] + atributos_cara
        + ATRIBUTOS_DETALLE
        + BLOQUE_PERFIL
        + BLOQUE_CONTEXTO
    )
    # Nos aseguramos de no perder ninguna columna por el camino
    faltantes = [c for c in df.columns if c not in orden]
    assert not faltantes, f"Columnas fuera del orden definido: {faltantes}"
    return df[[c for c in orden if c in df.columns]]


campo = ordenar_columnas(campo, ATRIBUTOS_CARA)
arqueros = ordenar_columnas(arqueros, ATRIBUTOS_CARA_GK)

print("Orden final del dataset de jugadores de campo:\n")
print(list(campo.columns))

def ordenar_y_rankear(df: pd.DataFrame) -> pd.DataFrame:
    """Ordena por OVR descendente y agrega ranking global y por posición."""
    df = df.sort_values(["ovr", "name"], ascending=[False, True]).reset_index(drop=True)
    df.insert(0, "rank_global", df["ovr"].rank(method="min", ascending=False).astype(int))
    df.insert(1, "rank_posicion",
              df.groupby("position", observed=True)["ovr"]
                .rank(method="min", ascending=False).astype(int))
    return df


campo = ordenar_y_rankear(campo)
arqueros = ordenar_y_rankear(arqueros)
promo = promo.sort_values(["card_ovr", "release_date", "player_name"],
                          ascending=[False, True, True]).reset_index(drop=True)

print(campo[["rank_global", "rank_posicion", "name", "position", "ovr", "pac", "sho", "pas", "dri", "def", "phy"]].head(10))
print()

print(arqueros[["rank_global", "name", "team", "ovr"] + ATRIBUTOS_CARA_GK].head(10))
print()

print(promo[["player_name", "team", "promo_code", "drop_label", "card_ovr", "release_date"]].head(10))
print()

# Top 3 de cada posición
top_por_posicion = (
    campo.sort_values(["position", "ovr"], ascending=[True, False])
         .groupby("position", observed=True)
         .head(3)[["position", "rank_posicion", "name", "team", "ovr"]]
)
print(top_por_posicion)
print()

# Ligas ordenadas por OVR promedio (sólo las que tienen 100 jugadores o más,
# para que una liga con 12 jugadores de élite no distorsione el ranking)
resumen_ligas = (
    campo.groupby("league", observed=True)
         .agg(jugadores=("ovr", "size"), ovr_promedio=("ovr", "mean"), ovr_maximo=("ovr", "max"))
         .query("jugadores >= 100")
         .sort_values("ovr_promedio", ascending=False)
         .round(2)
)
print(resumen_ligas.head(10))
print()

# Cuántas cartas hay de cada tipo de promo, ordenadas por OVR promedio
resumen_promos = (
    promo.groupby("promo_code", observed=True)
         .agg(cartas=("card_ovr", "size"),
              ovr_promedio=("card_ovr", "mean"),
              ovr_maximo=("card_ovr", "max"))
         .sort_values("ovr_promedio", ascending=False)
         .round(2)
)
print(resumen_promos)
print()

def preparar_para_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Convierte las columnas de listas en texto separado por '|' para exportar."""
    salida = df.copy()
    for col in ["alternative_positions", "play_styles"]:
        if col in salida.columns:
            salida[col] = salida[col].apply(lambda lista: "|".join(map(str, lista)))
    return salida


archivos = {
    "jugadores_campo_limpio.csv": preparar_para_csv(campo),
    "arqueros_limpio.csv": preparar_para_csv(arqueros),
    "cartas_promo_limpio.csv": promo,
}

for nombre, df in archivos.items():
    ruta = DIR_LIMPIO / nombre
    df.to_csv(ruta, index=False, encoding="utf-8")
    print(f"✓ {nombre:32s} {len(df):>6,} filas x {df.shape[1]:>2} columnas")

def leer_dataset_limpio(nombre_archivo: str) -> pd.DataFrame:
    """Lee un CSV de data/processed/ devolviendo las listas vacías como '' y no como NaN."""
    df = pd.read_csv(DIR_LIMPIO / nombre_archivo, encoding="utf-8")
    for col in ["alternative_positions", "play_styles"]:
        if col in df.columns:
            df[col] = df[col].fillna("")
    return df


# Verificación: releemos y confirmamos que no queda ningún nulo inesperado
prueba = leer_dataset_limpio("jugadores_campo_limpio.csv")
print(f"Releído: {prueba.shape[0]:,} filas x {prueba.shape[1]} columnas")
print("Nulos restantes:", prueba.isna().sum().sum())

resumen = pd.DataFrame([
    {"Etapa": "1. CARGA", "Detalle": f"{filas_iniciales:,} jugadores + {len(promo_crudo)} cartas promo leídos desde CSV"},
    {"Etapa": "1. CARGA", "Detalle": "7 problemas de calidad identificados y documentados"},
    {"Etapa": "2. LIMPIEZA", "Detalle": "59 columnas normalizadas a snake_case"},
    {"Etapa": "2. LIMPIEZA", "Detalle": "3 columnas eliminadas (rank por data leakage, 2 URLs)"},
    {"Etapa": "2. LIMPIEZA", "Detalle": "height y weight convertidas de texto a número (cm y kg)"},
    {"Etapa": "2. LIMPIEZA", "Detalle": "2 columnas de listas parseadas → 3 variables numéricas nuevas"},
    {"Etapa": "2. LIMPIEZA", "Detalle": "0 duplicados, 0 atributos fuera del rango 0-99"},
    {"Etapa": "2. LIMPIEZA", "Detalle": f"Arqueros separados: {len(campo):,} de campo + {len(arqueros):,} arqueros"},
    {"Etapa": "2. LIMPIEZA", "Detalle": f"Cartas promo: 2 columnas vacías eliminadas, {cruzan}/{len(promo)} cruzan con su carta base"},
    {"Etapa": "3. ORDENACIÓN", "Detalle": "Columnas reordenadas en 5 bloques temáticos"},
    {"Etapa": "3. ORDENACIÓN", "Detalle": "Filas ordenadas por OVR + ranking global y por posición"},
    {"Etapa": "3. ORDENACIÓN", "Detalle": "3 archivos CSV limpios exportados a data/processed/"},
])
print(resumen)
print()

import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch, Rectangle
from matplotlib.ticker import FuncFormatter

DIR_FIGURAS = DIR_BASE / "output" / "figuras"
DIR_FIGURAS.mkdir(parents=True, exist_ok=True)

# Una sola paleta para todos los gráficos, así la presentación se ve coherente
SUPERFICIE = "#fcfcfb"
TINTA = "#0b0b0b"
TINTA_SUAVE = "#52514e"
TINTA_TENUE = "#898781"
GRILLA = "#e1e0d9"
AZUL = "#2a78d6"
AZUL_CLARO = "#b7d3f6"
NARANJA = "#eb6834"
AQUA = "#1baf7a"
GRIS = "#c3c2b7"

mpl.rcParams.update({
    "figure.facecolor": SUPERFICIE,
    "axes.facecolor": SUPERFICIE,
    "savefig.facecolor": SUPERFICIE,
    "font.family": "sans-serif",
    "font.size": 11,
    "text.color": TINTA,
    "axes.labelcolor": TINTA_SUAVE,
    "axes.edgecolor": GRIS,
    "xtick.color": TINTA_TENUE,
    "ytick.color": TINTA_TENUE,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "grid.color": GRILLA,
    "grid.linewidth": 0.8,
    "figure.dpi": 110,
    "savefig.dpi": 200,
    "savefig.bbox": "tight",
})


def poner_titulo(ax, titulo: str, subtitulo: str, alto=(1.14, 1.045)) -> None:
    """Título en negrita + subtítulo gris arriba del gráfico, sin superponerse.

    `alto` es la altura de cada uno en fracción del alto del gráfico; hay que
    subirlos cuando el gráfico es bajito (como el de la barra apilada).
    """
    ax.text(0, alto[0], titulo, transform=ax.transAxes, fontsize=14,
            fontweight="bold", color=TINTA, va="bottom", ha="left")
    ax.text(0, alto[1], subtitulo, transform=ax.transAxes, fontsize=10.5,
            color=TINTA_SUAVE, va="bottom", ha="left")


def miles(valor, _=None) -> str:
    """Formatea 15859 como '15.859' (separador de miles al estilo rioplatense)."""
    return f"{int(valor):,}".replace(",", ".")


def guardar(fig, nombre: str) -> None:
    """Guarda la figura en output/figuras/ y avisa dónde quedó."""
    fig.savefig(DIR_FIGURAS / nombre)
    print(f"✓ {nombre}")

CARAS = ["pac", "sho", "pas", "dri", "def", "phy"]
NOMBRE_GK = ["diving", "handling", "kicking", "reflexes", "speed", "positioning"]
SIGLA_GK = ["DIV", "HAN", "KIC", "REF", "SPD", "POS"]

corr_campo = [campo[c].corr(campo["ovr"]) for c in CARAS]
corr_arqueros = [arqueros[f"gk_{n}"].corr(arqueros["ovr"]) for n in NOMBRE_GK]

fig, ax = plt.subplots(figsize=(10, 5.6))

# Fondo suave en la fila PAC: es el caso más extremo y queremos que el ojo vaya ahí
ax.add_patch(Rectangle((0, -0.45), 1.18, 0.9, color="#f0f4fa", zorder=0))

for i, (a, b) in enumerate(zip(corr_campo, corr_arqueros)):
    ax.plot([a, b], [i, i], color=GRIS, linewidth=2.5, zorder=1, solid_capstyle="round")

ax.scatter(corr_campo, range(len(CARAS)), s=170, color=AZUL, zorder=3,
           edgecolors=SUPERFICIE, linewidths=2, label="Jugadores de campo")
ax.scatter(corr_arqueros, range(len(CARAS)), s=170, color=NARANJA, zorder=3,
           edgecolors=SUPERFICIE, linewidths=2, label="Arqueros")

# Etiqueta directa de cada valor: nadie debería tener que leer el eje
for i, (a, b) in enumerate(zip(corr_campo, corr_arqueros)):
    (izq, col_izq), (der, col_der) = sorted([(a, AZUL), (b, NARANJA)])
    ax.text(izq - 0.03, i, f"{izq:.2f}".replace(".", ","), ha="right", va="center",
            fontsize=10.5, color=col_izq, fontweight="bold", zorder=4)
    ax.text(der + 0.03, i, f"{der:.2f}".replace(".", ","), ha="left", va="center",
            fontsize=10.5, color=col_der, fontweight="bold", zorder=4)

ax.set_yticks(range(len(CARAS)),
              [f"{c.upper()}\n(arquero: {s})" for c, s in zip(CARAS, SIGLA_GK)],
              fontsize=10.5, color=TINTA_SUAVE)
ax.set_ylim(5.6, -0.6)
ax.set_xlim(0, 1.15)
ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "0,25", "0,50", "0,75", "1"])
ax.set_xlabel("Cuánto acompaña al OVR (correlación: 0 = nada, 1 = del todo)", labelpad=8)
ax.xaxis.grid(True, zorder=0)
ax.set_axisbelow(True)

ax.legend(loc="lower left", ncol=2, frameon=False, fontsize=10.5,
          labelcolor=TINTA_SUAVE, handletextpad=0.3, columnspacing=2)

poner_titulo(ax, "La misma columna significa cosas distintas según la posición",
             "Por eso el dataset se divide en dos: 15.859 jugadores de campo y 2.014 arqueros")

ax.text(0, -0.20,
         "Fila PAC: en un jugador de campo esa columna casi no acompaña al OVR (0,24); en un arquero sí (0,97),\n"
         "porque ahí no guarda el ritmo sino sus estiradas. Mezclarlos habría falseado todo el análisis.",
         transform=ax.transAxes, fontsize=9.5, color=TINTA_TENUE, va="top", ha="left")

guardar(fig, "01_por_que_separamos_arqueros.png")

nulos_antes = jugadores_crudo.isna().sum()
nulos_antes = nulos_antes[nulos_antes > 0].sort_values()

EXPLICACIONES = {
    "Alternative positions": "juega en una sola posición",
    "GK Diving": "no es arquero",
    "GK Handling": "no es arquero",
    "GK Kicking": "no es arquero",
    "GK Positioning": "no es arquero",
    "GK Reflexes": "no es arquero",
}

fig, ax = plt.subplots(figsize=(10, 4.8))

for i, valor in enumerate(nulos_antes.values):
    ax.plot([0, valor], [i, i], color=GRIS, linewidth=2.5, zorder=1, solid_capstyle="round")

ax.scatter(nulos_antes.values, range(len(nulos_antes)), s=150, color=AZUL, zorder=3,
           edgecolors=SUPERFICIE, linewidths=2, label="Antes de limpiar")
ax.scatter([0] * len(nulos_antes), range(len(nulos_antes)), s=150, color=AZUL_CLARO,
           zorder=3, edgecolors=SUPERFICIE, linewidths=2, label="Después de limpiar")

for i, (col, valor) in enumerate(nulos_antes.items()):
    ax.text(valor + 400, i, miles(valor), ha="left", va="center",
            fontsize=10.5, color=AZUL, fontweight="bold")
    ax.text(valor + 3200, i, f"→ {EXPLICACIONES.get(col, '')}", ha="left", va="center",
            fontsize=9.5, color=TINTA_TENUE, style="italic")

ax.set_yticks(range(len(nulos_antes)), list(nulos_antes.index),
              fontsize=10.5, color=TINTA_SUAVE)
ax.set_ylim(-0.7, len(nulos_antes) - 0.3)
ax.set_xlim(-500, 25500)
ax.set_xticks([0, 5000, 10000, 15000])
ax.xaxis.set_major_formatter(FuncFormatter(miles))
ax.set_xlabel("Cantidad de celdas vacías")
ax.xaxis.grid(True, zorder=0)
ax.set_axisbelow(True)

ax.legend(loc="lower right", ncol=2, frameon=False, fontsize=10.5,
          labelcolor=TINTA_SUAVE, handletextpad=0.3, columnspacing=2)

poner_titulo(ax, "Ningún valor faltante era un error de carga",
             "Todos tenían explicación, así que no hubo que rellenar ni inventar ningún dato")

guardar(fig, "02_valores_faltantes.png")

fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.6), sharex=True, sharey=True)

paneles = [
    (axes[0], campo, f"Jugadores de campo ({miles(len(campo))})", AZUL),
    (axes[1], arqueros, f"Arqueros ({miles(len(arqueros))})", NARANJA),
]

for ax, df, titulo, color in paneles:
    pesos = [100 / len(df)] * len(df)  # cada jugador vale su % del dataset
    ax.hist(df["ovr"], bins=range(45, 95, 2), weights=pesos,
            color=color, edgecolor=SUPERFICIE, linewidth=1.2, zorder=2)
    mediana = df["ovr"].median()
    ax.axvline(mediana, color=TINTA, linewidth=1.5, linestyle="--", zorder=5)
    ax.text(mediana + 1.2, 12.4, f"mediana {mediana:.0f}", fontsize=10,
            color=TINTA, fontweight="bold")
    ax.text(0, 1.03, titulo, transform=ax.transAxes, fontsize=11.5,
            color=TINTA_SUAVE, va="bottom", ha="left")
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    ax.set_xlabel("OVR (valoración general)")

axes[0].set_ylabel("% de jugadores del dataset")
axes[0].set_ylim(0, 14)
axes[0].yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{int(v)}%"))

# Se suben más que en otros gráficos porque abajo están los títulos de cada panel
poner_titulo(axes[0], "Distribución del OVR en los dos datasets limpios",
             "Misma forma en ambos, pero entre los arqueros hay menos jugadores de élite",
             alto=(1.26, 1.15))

guardar(fig, "03_distribucion_ovr.png")

conteo = jugadores["position"].value_counts().sort_values()
porcentaje_gk = conteo["GK"] / conteo.sum()

fig, ax = plt.subplots(figsize=(9.5, 5.4))
ax.barh(range(len(conteo)), conteo.values, height=0.72,
        color=[NARANJA if pos == "GK" else GRIS for pos in conteo.index])

for i, (pos, valor) in enumerate(conteo.items()):
    es_gk = pos == "GK"
    ax.text(valor + 50, i, miles(valor), ha="left", va="center", fontsize=10.5,
            color=NARANJA if es_gk else TINTA_SUAVE,
            fontweight="bold" if es_gk else "normal")

ax.set_yticks(range(len(conteo)), list(conteo.index), fontsize=10.5, color=TINTA_SUAVE)
ax.set_xlim(0, 3650)
ax.set_xticks([0, 1000, 2000, 3000])
ax.xaxis.set_major_formatter(FuncFormatter(miles))
ax.set_xlabel("Cantidad de jugadores")
ax.xaxis.grid(True, zorder=0)
ax.set_axisbelow(True)

poner_titulo(ax, f"Los arqueros son el {porcentaje_gk:.0%} del dataset",
             f"{miles(conteo['GK'])} de {miles(conteo.sum())} jugadores: suficientes para analizarlos por separado")

guardar(fig, "04_jugadores_por_posicion.png")

tramos = [
    ("Coincidencia exacta", cruzan_exacto, AZUL),
    ("2º pase: apellido único", cruzan - cruzan_exacto, AQUA),
    ("Sin cruzar", len(promo) - cruzan, GRIS),
]

fig, ax = plt.subplots(figsize=(10, 2.2))

izquierda = 0
for _, valor, color in tramos:
    ax.barh(0, valor, left=izquierda, color=color, height=0.5, zorder=2)
    izquierda += valor
    ax.barh(0, 1.4, left=izquierda - 0.7, color=SUPERFICIE, height=0.5, zorder=3)  # separador

ax.text(cruzan_exacto / 2, 0, str(cruzan_exacto), ha="center", va="center",
        fontsize=15, fontweight="bold", color="white", zorder=4)

# Leyenda nativa de matplotlib: reparte el espacio sola, así nunca se pisan las etiquetas
ax.legend(handles=[Patch(facecolor=color, label=f"{etiqueta}: {valor}")
                   for etiqueta, valor, color in tramos],
          loc="upper left", bbox_to_anchor=(0, -0.10), ncol=3, frameon=False,
          fontsize=10, labelcolor=TINTA_SUAVE, handlelength=1.1, handleheight=1.1,
          handletextpad=0.6, columnspacing=3)

ax.set_xlim(0, len(promo))
ax.set_ylim(-0.3, 0.3)
ax.axis("off")

poner_titulo(ax, f"Cruzamos {cruzan} de {len(promo)} cartas promocionales ({cruzan/len(promo):.1%})",
             "Las 4 restantes no se adivinaron: o no están en el dataset base, o el apellido es ambiguo",
             alto=(1.42, 1.16))

guardar(fig, "05_cruce_cartas_promo.png")

resumen_promo = (promo.groupby("promo_code", observed=True)
                      .agg(cartas=("card_ovr", "size"), ovr_max=("card_ovr", "max"))
                      .sort_values("cartas"))

fig, ax = plt.subplots(figsize=(9.5, 4))
ax.barh(range(len(resumen_promo)), resumen_promo["cartas"], color=AZUL, height=0.62)

for i, (_, fila) in enumerate(resumen_promo.iterrows()):
    ax.text(fila["cartas"] + 1.5, i,
            f"{int(fila['cartas'])} cartas   ·   OVR máximo {int(fila['ovr_max'])}",
            ha="left", va="center", fontsize=10.5, color=TINTA_SUAVE)

ax.set_yticks(range(len(resumen_promo)), list(resumen_promo.index),
              fontsize=10.5, color=TINTA_SUAVE)
ax.set_xlim(0, 125)
ax.set_xticks([0, 20, 40, 60, 80])
ax.set_xlabel("Cantidad de cartas")
ax.xaxis.grid(True, zorder=0)
ax.set_axisbelow(True)

poner_titulo(ax, f"{len(promo)} cartas promocionales repartidas en {promo['promo_code'].nunique()} promos",
             "TOTY es la más chica con 24 cartas, y aun así llega al OVR más alto del dataset")

guardar(fig, "06_cartas_promo_por_tipo.png")

print("\nListo. Revisa las carpetas data/processed/ y output/figuras/.")
