"""IDE-food: informe ciudadano, complemento del monitor técnico estable.

Se ejecuta DESPUÉS de ide_food_live.py y lee únicamente sus CSV publicados.
No modifica los cálculos, umbrales, estados ni el histórico técnico.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import math
import sys

import pandas as pd

OUTPUT = Path('outputs')
SOURCE = OUTPUT / 'ide_food_live_full_model.csv'
DEST = OUTPUT / 'ide_food_informe_ciudadano.md'
WATCH, RED = 3.0, 3.5
MAX_AGE_DAYS = 120  # Igual que en IDE-food LIVE v0.4.
MONTHS = ('enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
          'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre')
STATES = {
    'GREEN': ('🟢', 'Calma', 'El indicador no supera el umbral de vigilancia.'),
    'WATCH': ('🟡', 'Vigilancia', 'La presión supera el primer umbral del modelo, sin llegar a la alarma roja.'),
    'EARLY_AGROENERGY_WATCH': ('🟠', 'Alerta temprana agroenergética',
          'La energía y/o los fertilizantes están elevados y el modelo detecta una combinación temprana de tensiones.'),
    'RED': ('🔴', 'Alarma roja', 'La puntuación conjunta supera el umbral rojo del modelo.'),
    'RED_STRUCTURAL': ('🔴', 'Alarma roja con robustez por ablación',
          'La puntuación es roja y se mantiene al menos en vigilancia al retirar cualquiera de los tres componentes.'),
}
COMPONENTS = (
    ('⚡', 'Energía', 'Only_E', 'Energy_mom12', 'No_E',
     'Puede influir en transporte, maquinaria y procesamiento.'),
    ('🌾', 'Agricultura', 'Only_A', 'Agriculture_mom12', 'No_A',
     'Refleja tensiones en los índices mundiales de materias primas agrícolas.'),
    ('🧪', 'Fertilizantes', 'Only_F', 'Fertilizers_mom12', 'No_F',
     'Influye en una parte de los costes de producción agrícola.'),
)
REQUIRED = ('IDE_core', 'status', 'Only_E', 'Only_A', 'Only_F',
            'No_E', 'No_A', 'No_F')


def mes(ts):
    return f'{MONTHS[ts.month - 1]} de {ts.year}'


def fmt(x, decimals=2):
    return f'{float(x):.{decimals}f}'.replace('.', ',')


def regime(s):
    if s >= RED:
        return '🔴 Alta'
    if s >= WATCH:
        return '🟡 Vigilancia'
    return '🟢 Bajo umbral'


def read_model():
    if not SOURCE.is_file():
        raise FileNotFoundError(f'No existe {SOURCE}. Ejecuta primero ide_food_live.py')
    df = pd.read_csv(SOURCE, index_col=0, parse_dates=[0])
    missing = [c for c in REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f'Faltan columnas del modelo: {missing}')
    if df.empty or df.index.isna().any() or df.index.has_duplicates:
        raise ValueError('Fechas vacías, duplicadas o inválidas en el CSV técnico.')
    df = df.sort_index()
    nums = list(REQUIRED)
    nums.remove('status')
    for col in nums:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    if df[nums].isna().any().any() or not df[nums].apply(lambda s: s.map(math.isfinite)).all().all():
        raise ValueError('El CSV técnico contiene puntuaciones vacías o no finitas.')
    invalid = set(df['status']) - set(STATES)
    if invalid:
        raise ValueError(f'Estados desconocidos: {sorted(invalid)}')
    return df


def generate(df, now=None):
    now = now or datetime.now(timezone.utc)
    last = df.iloc[-1]
    date = df.index[-1]
    status = str(last['status'])
    icon, title, definition = STATES[status]
    core = float(last['IDE_core'])
    age = (now.date() - date.date()).days
    health = ('Datos actuales según el criterio del monitor'
              if -31 <= age <= MAX_AGE_DAYS else 'ATENCIÓN: fecha de observación fuera del margen habitual')
    previous = df.iloc[-2] if len(df) > 1 else None
    previous_date = df.index[-2] if previous is not None else None

    result = [
        '# 🌡️ IDE-food: ¿qué está pasando con los costes que rodean a los alimentos?',
        '',
        f'**Informe ciudadano · {mes(date)}**',
        f'**Generado:** {now:%Y-%m-%d %H:%M} UTC  ',
        f'**Estado de los datos:** {health} ({age} días desde el cierre del mes).',
        '',
        '## En 30 segundos',
        '',
        f'### {icon} {title}: {fmt(core)} puntos de 5',
        '',
        definition,
        '',
        'Este número resume cambios interanuales de **índices mundiales** de energía, '
        'agricultura y fertilizantes, comparados con su comportamiento histórico. '
        '**No mide directamente el precio de la cesta de la compra** ni predice cuánto subirá.',
        '',
    ]
    if previous is not None:
        delta = core - float(previous['IDE_core'])
        direction = 'subió' if delta > 0.005 else 'bajó' if delta < -0.005 else 'prácticamente no cambió'
        result += [
            f'**Respecto a {mes(previous_date)}:** el indicador {direction} '
            f'({fmt(float(previous["IDE_core"]))} → {fmt(core)}; '
            f'variación {delta:+.2f} puntos).', '',
        ]
        active = {'WATCH', 'EARLY_AGROENERGY_WATCH', 'RED', 'RED_STRUCTURAL'}
        if status in active and str(previous['status']) in active:
            result += [
                '**Continuidad:** hay alerta activa en ambos meses; el tipo de estado '
                f'pasó de `{previous["status"]}` a `{status}`.' if previous['status'] != status
                else '**Continuidad:** se mantiene el mismo estado de alerta respecto al mes anterior.',
                '',
            ]
        elif status in active:
            result += ['**Continuidad:** la alerta aparece después de un mes sin alerta activa.', '']

    result += [
        '## Las tres piezas del termómetro', '',
        '| Componente | Puntaje | Estado | Cambio anual del índice |',
        '|---|---:|---|---:|',
    ]
    for emoji, name, score_col, yoy_col, _, description in COMPONENTS:
        yoy = 'No disponible'
        if yoy_col in df and pd.notna(last[yoy_col]) and math.isfinite(float(last[yoy_col])):
            yoy = f'{fmt(math.expm1(float(last[yoy_col])) * 100, 1)} %'
        result.append(f'| {emoji} {name} | {fmt(last[score_col])} / 5 | {regime(last[score_col])} | {yoy} |')
    result += ['',
        'El **cambio anual** compara el índice de este mes con el del mismo mes del año anterior. '
        'El **puntaje** no es ese porcentaje: representa cuán inusual es el cambio anual '
        'frente a una ventana histórica móvil.', '',
        '## ¿Por qué podría importarme?', '',
        'La energía participa en el transporte y la transformación de alimentos; '
        'los fertilizantes influyen en algunos costes agrícolas; y las materias primas '
        'agrícolas forman parte de la cadena alimentaria. Una presión conjunta puede '
        'transmitirse a otros precios, pero no necesariamente ni en la misma proporción.', '',
        '## ¿Qué ha cambiado?', '',
    ]
    if previous is None:
        result.append('No se dispone de un mes anterior para comparar.')
    else:
        result += ['| Componente | Mes anterior | Mes actual | Cambio (puntos) |', '|---|---:|---:|---:|']
        for emoji, name, col, _, _, _ in COMPONENTS:
            delta = float(last[col]) - float(previous[col])
            result.append(f'| {emoji} {name} | {fmt(previous[col])} | {fmt(last[col])} | {delta:+.3f} |')
    result += ['', '## ¿Qué debemos vigilar?', '']
    for emoji, name, col, _, _, description in COMPONENTS:
        result.append(f'- **{emoji} {name}:** {regime(float(last[col]))}. {description}')
    result += [
        '',
        '## Para quien quiera comprobar los detalles', '',
        f'- **Umbrales del índice total:** vigilancia desde {fmt(WATCH, 1)}; rojo desde {fmt(RED, 1)}.',
        '- **Ponderaciones:** energía 35 %, agricultura 30 % y fertilizantes 35 %.',
        '- **Método:** variaciones logarítmicas interanuales, z-scores móviles de 120 meses '
        '(sin usar el mes evaluado en la media histórica), recorte a ±4 σ y transformación sigmoide a 0–5.',
        '- **Prueba de ablación:** retirar un componente significa recalcular la media '
        'ponderada con los otros dos; no significa que el componente desaparezca de la economía.',
        '',
        '| Prueba matemática | Puntaje del total recalculado |',
        '|---|---:|',
    ]
    for emoji, name, _, _, no, _ in COMPONENTS:
        result.append(f'| Sin {emoji} {name} | {fmt(last[no])} |')
    result += [
        '', '## Lo que este informe NO dice', '',
        '- No anuncia una crisis alimentaria ni pronostica una subida concreta en el supermercado.',
        '- No demuestra por sí solo que una señal anticipará inflación a 6 o 12 meses.',
        '- No sustituye al informe técnico ni a una validación independiente.',
        '- La marca de actualidad se basa en la edad del último mes observado; '
        'no verifica si el Banco Mundial revisó valores anteriores.',
        '', '---', '',
        '**Fuente:** World Bank Commodity Markets Pink Sheet, índices mensuales.  ',
        '[Consultar archivo de origen](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx)  ',
        '**Autor del modelo:** Eric de Jesús Rodríguez Mendoza.  ',
        '**Informe divulgativo generado automáticamente a partir del CSV técnico de IDE-food LIVE.**', '',
    ]
    return '\n'.join(result)


def main():
    df = read_model()
    report = generate(df)
    OUTPUT.mkdir(exist_ok=True, parents=True)
    DEST.write_text(report, encoding='utf-8')
    print(f'Informe ciudadano generado: {DEST} | observación: {df.index[-1].date()}')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'ERROR creando informe ciudadano: {exc}', file=sys.stderr)
        raise SystemExit(1)
