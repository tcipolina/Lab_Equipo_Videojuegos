# EA Sports FC 26 — Análisis de atributos y valoración general (OVR)

**Introducción a la Ciencia de Datos** · Equipo Videojuegos

## Pregunta del proyecto

¿Qué atributos de la carta determinan la **valoración general (OVR)** de los jugadores
de EA Sports FC 26 en Ultimate Team?

Dicho con precisión: con qué pesos los **29 in-game stats** arman el OVR, y si esos pesos
cambian según la posición. Las 6 caras de la carta (ritmo, tiro, pase, regate, defensa,
físico) son un resumen de esos 29: no son el dato original.

## Estado actual

- [x] **Etapa 1 — Carga, limpieza y ordenación** → `notebooks/01_carga_limpieza_orden.ipynb`
- [x] **Etapa 2 — Correlaciones** → `notebooks/02_correlaciones.ipynb`
- [x] **Etapa 3 — Modelos** → `notebooks/03_modelos.ipynb`
- [ ] Etapa 4 — El tramo de élite (OVR ≥ 81), arqueros y cartas promocionales

## Estructura del repositorio

```
.
├── data/
│   ├── raw/                  # Datos originales — NUNCA se modifican
│   │   ├── EAFC26.csv
│   │   └── FC26_Promo_Players_-_promo_cards.csv
│   └── processed/            # Datos limpios (los genera el notebook 01)
│       ├── jugadores_campo_limpio.csv
│       ├── arqueros_limpio.csv
│       └── cartas_promo_limpio.csv
├── notebooks/
│   ├── 01_carga_limpieza_orden.ipynb    # Etapa 1 — genera los CSV limpios
│   ├── 02_correlaciones.ipynb           # Etapa 2 — lee esos CSV y analiza
│   └── 03_modelos.ipynb                 # Etapa 3 — entrena y evalúa los modelos
├── output/
│   └── figuras/              # Los 20 PNG para las diapositivas
├── presentacion/
│   ├── diagramas_explicativos.py        # Los esquemas 16 y 17 (no analizan datos)
│   ├── generar_presentacion.js          # Deck de setiembre (etapas 1 y 2)
│   └── generar_presentacion_octubre.js  # Deck de octubre (etapa 3)
├── requirements.txt
├── GUIA_PASO_A_PASO.md
└── README.md
```

## Cómo ejecutarlo

Crear un entorno virtual e instalar las dependencias. En VS Code: `Cmd/Ctrl + Shift + P`
→ `Python: Create Environment` → `Venv` → tildar `requirements.txt`. O por terminal:

```bash
python3 -m venv .venv
source .venv/bin/activate        # en Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

En Mac `pip install` sin entorno virtual falla con `externally-managed-environment`.

> El archivo incluye `ipykernel` pero **no** el paquete `jupyter`: VS Code no lo necesita,
> y `jupyter` arrastra `argon2-cffi-bindings`, que no compila en Python 3.14 o posterior.

Después se abren los notebooks en VS Code, se elige el kernel `.venv` arriba a la derecha
y `Run All`. **En orden:** primero el `01`, que genera los CSV limpios en
`data/processed/`; después el `02` y el `03`, que los leen. Ninguno repite el trabajo del
anterior: si los CSV no existen, avisan con un error claro.

Los tres notebooks juntos generan los tres CSV de `data/processed/` y 18 de los 20 PNG de
`output/figuras/`. Los dos restantes (el 16 y el 17) son esquemas explicativos que no
analizan datos y se generan aparte:

```bash
python presentacion/diagramas_explicativos.py
```

## Los datos

| Archivo | Filas | Columnas | Descripción |
|---|---:|---:|---|
| `EAFC26.csv` | 17.873 | 59 | Cartas base de todos los jugadores del juego |
| `FC26_Promo_Players_-_promo_cards.csv` | 212 | 10 | Cartas promocionales (TOTY, TOTS, TOTW, Future Stars) |

### Resultado de la limpieza

| Dataset limpio | Filas | Columnas |
|---|---:|---:|
| `jugadores_campo_limpio.csv` | 15.859 | 57 |
| `arqueros_limpio.csv` | 2.014 | 57 |
| `cartas_promo_limpio.csv` | 212 | 11 |

## Gráficos

### Etapa 1 — Limpieza (notebook 01)

No analizan todavía qué define el OVR: **documentan las decisiones de limpieza**.

| Archivo | Responde a |
|---|---|
| `01_por_que_separamos_arqueros.png` | ¿Por qué separaron a los arqueros? |
| `02_valores_faltantes.png` | ¿Qué hicieron con los valores faltantes? |
| `03_distribucion_ovr.png` | ¿Cómo quedaron los datos después de limpiar? |
| `04_jugadores_por_posicion.png` | ¿Cuántos jugadores hay de cada posición? |
| `05_cruce_cartas_promo.png` | ¿Pudieron cruzar los dos datasets? |
| `06_cartas_promo_por_tipo.png` | ¿Qué hay en el dataset de cartas promocionales? |

### Etapa 2 — Correlaciones (notebook 02)

| Archivo | Responde a |
|---|---|
| `07_matriz_correlacion.png` | El diagrama de correlación: ¿cómo se relacionan todas las variables? |
| `08_ranking_correlacion_ovr.png` | **¿Qué atributo acompaña al OVR?** |
| `09_dispersion_fuerte_vs_debil.png` | ¿Qué aspecto tiene un 0,90 y un 0,24? |
| `10_correlacion_por_posicion.png` | ¿La respuesta cambia según la posición? |
| `11_correlacion_arqueros.png` | ¿Y en los arqueros? |

#### Resultados

| Atributo | Coeficiente | ¿Está en la carta? |
|---|---:|---|
| Reacciones | **0,896** | No |
| Pase corto | 0,829 | No |
| Serenidad | 0,820 | No |
| Control del balón | 0,810 | No |
| PAS (pase) | 0,744 | Sí |
| PAC (ritmo) | 0,240 | Sí |
| Altura | -0,080 | No |

**El atributo que más acompaña al OVR no aparece en la cara de la carta.** Reacciones se
mantiene además entre 0,89 y 0,92 en las once posiciones y en 0,89 en los arqueros: es el
único atributo que manda en todos los grupos.

Correlación no es causalidad: para medir el efecto de cada atributo por separado hizo
falta una regresión múltiple, que es la etapa 3.

### Etapa 3 — Modelos (notebook 03)

| Archivo | Responde a |
|---|---|
| `12_comparacion_modelos.png` | ¿Qué tan bien se puede predecir el OVR? |
| `13_predicho_vs_real.png` | ¿Cuánto le acierta el mejor modelo? |
| `14_importancia_random_forest.png` | ¿Qué atributo usa más el modelo para decidir? |
| `15_pesos_por_posicion.png` | **La receta del OVR, posición por posición** |
| `18_ejemplo_calculo_ovr.png` | La receta aplicada a un jugador concreto (Mbappé) |
| `19_cuantos_atributos.png` | ¿Hacen falta los 29 in-game stats o alcanzan menos? |
| `20_donde_falla_el_modelo.png` | ¿Dónde se equivoca más el modelo? |

Además, dos esquemas explicativos que no analizan datos
(`presentacion/diagramas_explicativos.py`): `16_anatomia_carta.png` y
`17_caras_vs_ingame_stats.png`.

#### Resultados de los modelos

Todos evaluados sobre el 25% de los jugadores, apartado antes de entrenar.

| Modelo | R² | Error medio |
|---|---:|---:|
| Sólo las 6 caras de la carta | 0,772 | 2,66 puntos |
| Los 29 in-game stats | 0,914 | 1,61 puntos |
| Random Forest (29 in-game stats) | 0,973 | 0,87 puntos |
| **Un modelo por cada posición** | **0,998** | **0,29 puntos** |

**El OVR es un promedio ponderado de los in-game stats, con pesos propios por posición.**
Los coeficientes de los 11 modelos suman 1,00 en todas las posiciones, lo que confirma que
se trata de un promedio ponderado. Reacciones es el único atributo con peso en todas las
recetas (0,05 a 0,09), y eso explica por qué en la etapa 2 correlacionaba 0,90 en
cualquier posición.

El 99,6% de los jugadores de prueba queda a menos de 1 punto de su OVR real.

Dos controles más sobre ese resultado:

- **Alcanzan 12 de los 29 in-game stats.** Entrenando con sólo los N atributos de mayor peso
  de cada posición, el R² llega a 0,998 ya con 12; los otros 17 no entran en ninguna receta.
  Con uno solo (Reacciones) se explica el 85%, y con cinco el 97%.
- **El modelo falla en el tramo de élite.** Entre 47 y 80 de OVR el error medio es 0,28 y no se
  inclina para ningún lado. En los 113 jugadores de 81 o más sube a 0,45 y los **subestima** en
  0,27 puntos en promedio: ahí la relación deja de ser lineal.

## Decisiones de limpieza

1. **Arqueros separados de jugadores de campo.** En el CSV, las columnas
   `PAC/SHO/PAS/DRI/DEF/PHY` guardan cosas distintas según la posición: para un arquero
   son `DIV/HAN/KIC/REF/SPD/POS`. Mezclarlos produciría correlaciones falsas, así que
   son dos datasets y en el de arqueros esas columnas están renombradas.
2. **Columna `Rank` eliminada.** Es el puesto del jugador ordenado por OVR, o sea que
   se calcula *a partir* del OVR. Dejarla sería **fuga de información (data leakage)**:
   cualquier modelo la usaría para "predecir" el OVR de forma tramposa.
3. **`Height` y `Weight` convertidas a número.** Venían como texto
   (`"175cm / 5'9\""`); nos quedamos con el sistema métrico.
4. **Listas de texto parseadas.** `Alternative positions` y `play style` venían como
   `"['RW', 'LM']"`. Se convirtieron en listas reales y se derivaron tres variables
   numéricas: `n_alternative_positions`, `n_play_styles` y `n_play_styles_plus`.
5. **Nulos interpretados, no rellenados.** Los 15.859 nulos de las columnas `gk_*` no
   son datos faltantes: son jugadores que no son arqueros. Los 6.380 nulos de
   `Alternative positions` son jugadores de una sola posición.
6. **Cruce por nombre normalizado.** El dataset de promos no trae ID. Se creó la clave
   `name_key` (sin tildes, en minúsculas) y un segundo pase por apellido único, que
   logra cruzar 208 de 212 cartas promo (98,1%) con su carta base.

## Diccionario de datos (columnas principales)

| Columna | Tipo | Descripción |
|---|---|---|
| `rank_global` | int | Puesto por OVR dentro de su dataset |
| `rank_posicion` | int | Puesto por OVR dentro de su posición |
| `player_id` | int | Identificador del jugador en EA |
| `name` | texto | Nombre como figura en la carta |
| `gender` | categoría | `M` / `F` |
| `age` | int | Edad en años |
| `position` | categoría | Posición principal (ST, CM, CB, …) |
| `alternative_positions` | texto | Otras posiciones, separadas por `\|` |
| `ovr` | int | **Valoración general — variable a explicar** |
| `pac` `sho` `pas` `dri` `def` `phy` | int | Las 6 caras de la carta (jugadores de campo) |
| `gk_diving` … `gk_positioning` | int | Las 6 caras de la carta (arqueros) |
| 29 in-game stats | int | `acceleration`, `finishing`, `vision`, `composure`, … (0-99) |
| `height_cm` `weight_kg` | float | Altura y peso en sistema métrico |
| `preferred_foot` | categoría | `Left` / `Right` |
| `weak_foot` `skill_moves` | int | Estrellas (1-5) |
| `n_play_styles` | int | Cantidad de PlayStyles |
| `n_play_styles_plus` | int | Cuántos de esos son PlayStyle+ |
| `nation` `league` `team` | categoría | Contexto del jugador |
| `name_key` | texto | Nombre normalizado, clave para cruzar datasets |

## Equipo

Equipo Videojuegos — Introducción a la Ciencia de Datos
