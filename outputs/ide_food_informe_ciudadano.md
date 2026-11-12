# 🌡️ IDE-food: ¿qué está pasando con los costes que rodean a los alimentos?

**Informe ciudadano · octubre de 2026**
**Generado:** 2026-11-12 10:59 UTC  
**Estado de los datos:** Datos actuales según el criterio del monitor (12 días desde el cierre del mes).

## En 30 segundos

### 🟠 Alerta temprana agroenergética: 3,31 puntos de 5

La energía y/o los fertilizantes están elevados y el modelo detecta una combinación temprana de tensiones.

Este número resume cambios interanuales de **índices mundiales** de energía, agricultura y fertilizantes, comparados con su comportamiento histórico. **No mide directamente el precio de la cesta de la compra** ni predice cuánto subirá.

**Respecto a septiembre de 2026:** el indicador subió (3,10 → 3,31; variación +0.21 puntos).

**Continuidad:** hay alerta activa en ambos meses; el tipo de estado pasó de `WATCH` a `EARLY_AGROENERGY_WATCH`.

## Las tres piezas del termómetro

| Componente | Puntaje | Estado | Cambio anual del índice |
|---|---:|---|---:|
| ⚡ Energía | 4,11 / 5 | 🔴 Alta | 89,3 % |
| 🌾 Agricultura | 3,07 / 5 | 🟡 Vigilancia | 7,3 % |
| 🧪 Fertilizantes | 2,49 / 5 | 🟢 Bajo umbral | 6,2 % |

El **cambio anual** compara el índice de este mes con el del mismo mes del año anterior. El **puntaje** no es ese porcentaje: representa cuán inusual es el cambio anual frente a una ventana histórica móvil.

## ¿Por qué podría importarme?

La energía participa en el transporte y la transformación de alimentos; los fertilizantes influyen en algunos costes agrícolas; y las materias primas agrícolas forman parte de la cadena alimentaria. Una presión conjunta puede transmitirse a otros precios, pero no necesariamente ni en la misma proporción.

## ¿Qué ha cambiado?

| Componente | Mes anterior | Mes actual | Cambio (puntos) |
|---|---:|---:|---:|
| ⚡ Energía | 3,89 | 4,11 | +0.214 |
| 🌾 Agricultura | 2,99 | 3,07 | +0.080 |
| 🧪 Fertilizantes | 2,24 | 2,49 | +0.254 |

## ¿Qué debemos vigilar?

- **⚡ Energía:** 🔴 Alta. Puede influir en transporte, maquinaria y procesamiento.
- **🌾 Agricultura:** 🟡 Vigilancia. Refleja tensiones en los índices mundiales de materias primas agrícolas.
- **🧪 Fertilizantes:** 🟢 Bajo umbral. Influye en una parte de los costes de producción agrícola.

## Para quien quiera comprobar los detalles

- **Umbrales del índice total:** vigilancia desde 3,0; rojo desde 3,5.
- **Ponderaciones:** energía 35 %, agricultura 30 % y fertilizantes 35 %.
- **Método:** variaciones logarítmicas interanuales, z-scores móviles de 120 meses (sin usar el mes evaluado en la media histórica), recorte a ±4 σ y transformación sigmoide a 0–5.
- **Prueba de ablación:** retirar un componente significa recalcular la media ponderada con los otros dos; no significa que el componente desaparezca de la economía.

| Prueba matemática | Puntaje del total recalculado |
|---|---:|
| Sin ⚡ Energía | 2,76 |
| Sin 🌾 Agricultura | 3,41 |
| Sin 🧪 Fertilizantes | 3,69 |

## Lo que este informe NO dice

- No anuncia una crisis alimentaria ni pronostica una subida concreta en el supermercado.
- No demuestra por sí solo que una señal anticipará inflación a 6 o 12 meses.
- No sustituye al informe técnico ni a una validación independiente.
- La marca de actualidad se basa en la edad del último mes observado; no verifica si el Banco Mundial revisó valores anteriores.

---

**Fuente:** World Bank Commodity Markets Pink Sheet, índices mensuales.  
[Consultar archivo de origen](https://thedocs.worldbank.org/en/doc/74e8be41ceb20fa0da750cda2f6b9e4e-0050012026/related/CMO-Historical-Data-Monthly.xlsx)  
**Autor del modelo:** Eric de Jesús Rodríguez Mendoza.  
**Informe divulgativo generado automáticamente a partir del CSV técnico de IDE-food LIVE.**
