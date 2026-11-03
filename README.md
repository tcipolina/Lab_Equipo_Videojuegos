# ¿Qué determina el OVR de una carta en EA Sports FC 26?

**Introducción a la Ciencia de Datos** · Equipo Videojuegos

## La pregunta

Cada jugador de EA Sports FC 26 es una carta con una **valoración general (OVR)**, un
número del 1 al 99 que lo resume. La carta muestra seis atributos — ritmo, tiro, pase,
regate, defensa y físico — pero detrás de esos seis hay **29 atributos de detalle**, los
*in-game stats*, que el jugador no ve.

Nuestra pregunta: **con qué pesos esos 29 in-game stats arman el OVR, y si esos pesos
cambian según la posición en la que juega el futbolista.**

## La respuesta

**El OVR es un promedio ponderado de los in-game stats, con una receta distinta para cada
posición.** Lo reconstruimos sin conocer la fórmula de EA, sólo a partir de los datos
públicos de 15.859 jugadores.

Un modelo de regresión lineal entrenado por separado para cada posición predice el OVR
con un **R² de 0,998** y un error medio de **0,29 puntos** sobre 3.968 jugadores que nunca
vio. El 99,6% de ellos queda a menos de 1 punto de su OVR real.

Que sea un promedio ponderado no lo supusimos: se deduce de que **los coeficientes de los
once modelos suman 1,00** (entre 1,00 y 1,02) con un término independiente muy chico, de
−0,9 a +1,8 sobre un OVR que ronda 67.

### Las recetas, posición por posición

| Posición | Atributos con más peso |
|---|---|
| Delantero (ST) | Definición 0,19 · Posicionamiento 0,13 · Cabeceo 0,11 · Control del balón 0,10 |
| Mediapunta (CAM) | Pase corto 0,16 · Control 0,15 · Centros 0,15 · Regate 0,13 |
| Mediocampista (CM) | Pase corto 0,16 · Control 0,15 · Pase largo 0,13 · Centros 0,13 |
| Volante defensivo (CDM) | Pase corto 0,15 · Intercepciones 0,13 · Entrada 0,13 |
| Central (CB) | Entrada 0,17 · Corte defensivo 0,14 · Intercepciones 0,13 |

A un delantero la definición le pesa 0,19 y la entrada 0,00; a un central, al revés.

**Reacciones es el único atributo que entra en las nueve recetas**, siempre con un peso
parecido (entre 0,05 y 0,09). Eso explica un resultado que nos había llamado la atención
en la etapa anterior: correlacionaba 0,90 con el OVR en todas las posiciones, y ninguno
de los otros atributos lo hacía.

## Los datos

| Archivo | Filas | Columnas | Contenido |
|---|---:|---:|---|
| `EAFC26.csv` | 17.873 | 59 | Cartas base de todos los jugadores del juego |
| `FC26_Promo_Players_-_promo_cards.csv` | 212 | 10 | Cartas promocionales (TOTY, TOTS, TOTW, Future Stars) |

Después de limpiar quedaron tres datasets: **15.859 jugadores de campo**, **2.014
arqueros** y las **212 cartas promocionales**, 208 de ellas cruzadas con su carta base.

## Qué hicimos

### Etapa 1 — Carga, limpieza y ordenación

Seis decisiones de limpieza, todas documentadas en el notebook con su justificación:

1. **Arqueros separados de jugadores de campo.** En el CSV las columnas
   `PAC/SHO/PAS/DRI/DEF/PHY` guardan cosas distintas según la posición: para un arquero
   son paradas, saque, reflejos, velocidad y colocación. Analizarlos juntos habría
   producido correlaciones falsas, así que son dos datasets y en el de arqueros esas
   columnas están renombradas.
2. **Columna `Rank` eliminada.** Es el puesto del jugador ordenado por OVR, o sea que se
   calcula *a partir* del OVR. Dejarla habría sido **fuga de información (data
   leakage)**: cualquier modelo la usaría para "predecir" el OVR de forma tramposa.
3. **`Height` y `Weight` convertidas a número.** Venían como texto (`"175cm / 5'9\""`);
   nos quedamos con el sistema métrico.
4. **Listas de texto parseadas.** `Alternative positions` y `play style` venían como
   `"['RW', 'LM']"`. Se convirtieron en listas reales y se derivaron tres variables
   numéricas.
5. **Nulos interpretados, no rellenados.** Los 15.859 nulos de las columnas `gk_*` no son
   datos faltantes: son jugadores que no son arqueros.
6. **Cruce por nombre normalizado.** El dataset de promos no trae ID. Se creó la clave
   `name_key` (sin tildes, en minúsculas) y un segundo pase por apellido único, que logra
   cruzar 208 de 212 cartas promo (98,1%).

### Etapa 2 — Correlaciones

Medimos qué atributos acompañan al OVR, con Pearson y Spearman, en el total y por
posición.

| Atributo | Coeficiente | ¿Está en la cara de la carta? |
|---|---:|---|
| Reacciones | **0,896** | No |
| Pase corto | 0,829 | No |
| Serenidad | 0,820 | No |
| Control del balón | 0,810 | No |
| Pase (PAS) | 0,744 | Sí |
| Ritmo (PAC) | 0,240 | Sí |
| Altura | −0,080 | No |

**El atributo que más acompaña al OVR no aparece en la cara de la carta**, y el ritmo —
el número más grande que ve el jugador — apenas llega a 0,24.

El límite de esta etapa es lo que motivó la siguiente: la correlación dice que dos cosas
se mueven juntas, pero no cuánto aporta cada una ni cómo se combinan, y no permite
calcular el OVR de un jugador nuevo.

### Etapa 3 — Modelos

Cuatro modelos, todos evaluados sobre el 25% de los jugadores apartado **antes** de
entrenar, para que ninguno se evalúe con datos que ya vio.

| Modelo | R² | Error medio |
|---|---:|---:|
| Sólo las 6 caras de la carta | 0,772 | 2,66 puntos |
| Los 29 in-game stats | 0,914 | 1,61 puntos |
| Random Forest (29 in-game stats) | 0,973 | 0,87 puntos |
| **Una regresión por cada posición** | **0,998** | **0,29 puntos** |

Tres resultados que vale la pena señalar:

- **Las 6 caras son un resumen, no un dato.** Agregarlas al modelo de los 29 in-game
  stats no mejora nada (0,9135 contra 0,9134): no traen información nueva.
- **Alcanzan 12 de los 29 atributos.** Entrenando con sólo los N de mayor peso de cada
  posición, el R² ya llega a 0,998 con 12; los otros 17 no entran en ninguna receta. Con
  uno solo (Reacciones) se explica el 85%, y con cinco el 97%. Esto descarta que el
  modelo acierte por acumular variables.
- **El Random Forest llega al mismo ganador por otro camino.** Le asigna a Reacciones el
  76% de la decisión, con un método que no tiene nada que ver con la correlación de la
  etapa 2.

## Lo que no cierra

El modelo es lineal: supone que subir un punto de definición suma siempre lo mismo, valga
el jugador 60 u 85. Los datos dicen que en el tramo alto eso no se cumple.

Entre 47 y 80 de OVR el error medio es de 0,28 puntos y no se inclina para ningún lado.
En los **113 jugadores de 81 o más sube a 0,45 y además es sistemático: el modelo los
subestima en 0,27 puntos**. Ahí la relación deja de ser una recta, y es el único lugar
donde nuestra receta todavía no reproduce la de EA.

Queda pendiente, junto con modelar los arqueros y las cartas promocionales, que quedaron
separados desde la etapa 1.

## Los notebooks

| Notebook | Qué hace | Gráficos |
|---|---|---|
| `01_carga_limpieza_orden.ipynb` | Lee los CSV crudos, limpia, ordena y genera los tres datasets limpios | 01 a 06 |
| `02_correlaciones.ipynb` | Mide qué atributos acompañan al OVR, en total y por posición | 07 a 11 |
| `03_modelos.ipynb` | Entrena y evalúa los cuatro modelos, y extrae la receta de cada posición | 12 a 15, 18 a 20 |

Se corren **en ese orden**: el 01 genera los CSV limpios que leen los otros dos. Ninguno
repite el trabajo del anterior; si los CSV no existen, avisan con un error claro.

Los gráficos 16 y 17 son esquemas explicativos que no analizan datos (la anatomía de una
carta y la diferencia entre las 6 caras y los 29 in-game stats); los genera
`presentacion/diagramas_explicativos.py`.

## Cómo reproducirlo

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Después se corren los tres notebooks en orden. Se regeneran los tres CSV de
`data/processed/` y los 18 gráficos de `output/figuras/`.

## Estructura del repositorio

```
.
├── data/
│   ├── raw/                  # Datos originales — nunca se modifican
│   └── processed/            # Datasets limpios (los genera el notebook 01)
├── notebooks/                # Los tres notebooks, uno por etapa
├── output/figuras/           # Los 20 gráficos
├── presentacion/             # Diagramas explicativos y generadores de las diapositivas
├── requirements.txt
└── README.md
```

## Diccionario de datos

| Columna | Descripción |
|---|---|
| `ovr` | **Valoración general — la variable que queremos explicar** |
| `position` | Posición principal (ST, CM, CB, …) |
| `pac` `sho` `pas` `dri` `def` `phy` | Las 6 caras de la carta (jugadores de campo) |
| `gk_diving` … `gk_positioning` | Las 6 caras de la carta (arqueros) |
| 29 in-game stats | `finishing`, `short_passing`, `reactions`, `interceptions`, … (0-99) |
| `height_cm` `weight_kg` | Altura y peso en sistema métrico |
| `weak_foot` `skill_moves` | Estrellas (1-5) |
| `n_play_styles` `n_play_styles_plus` | Cantidad de PlayStyles y cuántos son PlayStyle+ |
| `rank_global` `rank_posicion` | Puesto por OVR, en el dataset y dentro de su posición |
| `name_key` | Nombre normalizado, clave para cruzar los dos datasets |

---

Equipo Videojuegos — Introducción a la Ciencia de Datos
