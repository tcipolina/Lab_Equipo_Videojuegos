# EA Sports FC 26 — Análisis de atributos y valoración general (OVR)

**Introducción a la Ciencia de Datos** · Equipo Videojuegos

## Pregunta del proyecto

¿Qué atributos de la carta determinan la **valoración general (OVR)** de los jugadores
de EA Sports FC 26 en Ultimate Team?

## Estado actual

- [x] **Etapa 1 — Carga, limpieza y ordenación** → `notebooks/01_carga_limpieza_orden.ipynb`
- [ ] Etapa 2 — Análisis exploratorio y correlaciones
- [ ] Etapa 3 — Modelado y conclusiones

## Estructura del repositorio

```
.
├── data/
│   ├── raw/                  # Datos originales — NUNCA se modifican
│   │   ├── EAFC26.csv
│   │   └── FC26_Promo_Players_-_promo_cards.csv
│   └── processed/            # Datos limpios (los genera el notebook)
│       ├── jugadores_campo_limpio.csv
│       ├── arqueros_limpio.csv
│       └── cartas_promo_limpio.csv
├── notebooks/
│   └── 01_carga_limpieza_orden.ipynb
├── output/
│   └── figuras/              # Los 6 PNG para las diapositivas (los genera el notebook)
├── requirements.txt
└── README.md
```

## Cómo ejecutarlo

```bash
pip install -r requirements.txt
```

Después abrir `notebooks/01_carga_limpieza_orden.ipynb` en VS Code y ejecutar todas
las celdas (`Run All`). Genera los tres CSV de `data/processed/` y los seis PNG de
`output/figuras/`.

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

## Gráficos para la presentación

La Parte 4 del notebook genera seis PNG en `output/figuras/`. No analizan todavía qué
define el OVR: **documentan las decisiones de limpieza**, que es lo que se presenta
en esta etapa.

| Archivo | Responde a |
|---|---|
| `01_por_que_separamos_arqueros.png` | ¿Por qué separaron a los arqueros? |
| `02_valores_faltantes.png` | ¿Qué hicieron con los valores faltantes? |
| `03_distribucion_ovr.png` | ¿Cómo quedaron los datos después de limpiar? |
| `04_jugadores_por_posicion.png` | ¿Cuántos jugadores hay de cada posición? |
| `05_cruce_cartas_promo.png` | ¿Pudieron cruzar los dos datasets? |
| `06_cartas_promo_por_tipo.png` | ¿Qué hay en el dataset de cartas promocionales? |

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
| 29 atributos de detalle | int | `acceleration`, `finishing`, `vision`, `composure`, … (0-99) |
| `height_cm` `weight_kg` | float | Altura y peso en sistema métrico |
| `preferred_foot` | categoría | `Left` / `Right` |
| `weak_foot` `skill_moves` | int | Estrellas (1-5) |
| `n_play_styles` | int | Cantidad de PlayStyles |
| `n_play_styles_plus` | int | Cuántos de esos son PlayStyle+ |
| `nation` `league` `team` | categoría | Contexto del jugador |
| `name_key` | texto | Nombre normalizado, clave para cruzar datasets |

## Equipo

Equipo Videojuegos — Introducción a la Ciencia de Datos
