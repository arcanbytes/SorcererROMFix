# 🧩 SorcererROMFix – Análisis de la corrupción de partidas en Sorcerer's Kingdom (Edición Española)

Este repositorio documenta la investigación técnica sobre los reportes de **corrupción de partidas guardadas** en la reedición física en castellano de *Sorcerer's Kingdom* (Mega Drive), publicada en 2026 (Extreme / Shinyuden / Ratalaika Games). Es un proyecto hermano de [TraysiaROMFix](https://github.com/arcanbytes/TraysiaROMFix), con el que comparte metodología: desensamblado 68000 y auditoría binaria completa de la ROM.

**Conclusión provisional: la ROM traducida queda descartada como causa.** A diferencia de lo ocurrido con Traysia, la auditoría no encuentra ni una sola instrucción de código modificada respecto al original USA. La hipótesis principal se desplaza al **hardware del cartucho moderno** (mezcla de voltajes 3,3V/5V en la PCB), pendiente de validación empírica.

---

## 🐛 El problema reportado

Usuarios de la edición física española reportan partidas que se corrompen. El propio juego lo detecta y lo comunica: *Sorcerer's Kingdom* valida sus partidas al cargar y, si la verificación falla, muestra los mensajes **«LA P. N ESTÁ DAÑADA» / «LA P. N ESTÁ DESTRUIDA»** (en el original USA: *"Chronicle N is damaged / disintegrated"* — el juego llama "Crónicas" a las partidas; cadenas en ROM `0x156D8`). Según los primeros análisis de la comunidad, el fallo se manifiesta especialmente al guardar en múltiples slots.

---

## 🔬 Auditoría de la ROM traducida

### Versiones analizadas

| ROM | MD5 | Tamaño | Notas |
|---|---|---|---|
| Sorcerer's Kingdom (U) (1992), rev -00 | `8ab847680c35b89e4f7883cb216efdd6` | 1MB | Primera revisión USA |
| Sorcerer's Kingdom (U) (1993) [!], rev -01 | `587c51be6c60b82514e928f951e730b1` | 1MB | Revisión final USA |
| Sorcerer's Kingdom (ES), rev -01 | `52a66fca4c8ac34c7aaa3af057f4d8f6` | 1MB | Reedición en castellano (2026) |

> ℹ️ El dump que circula como *"Sorcerer's Kingdom (U) (1993) [b1]"* no es una revisión real: la etiqueta `[b1]` significa *bad dump*, y en realidad es la rev. de **1992** (serial `-00`) con 32 bytes de la cabecera manipulados (campos de título). No se usa como referencia de análisis.

La versión española **deriva de la revisión USA de 1993** (48.006 bytes de diferencia, frente a 77.645 respecto a la rev. de 1992). Ambas tienen exactamente 1MB: aquí **no hubo expansión de ROM**, por lo que el defecto encontrado en Traysia (punteros del monitor de depuración reubicados hacia la ventana de SRAM al expandir a 2MB) **no puede darse** en este juego.

### Qué cambia la traducción (los 48.006 bytes, clasificados)

- **Textos**: traducidos **in situ y con la misma longitud** (rellenos con espacios); las tablas de punteros de cadenas quedan intactas.
- **Gráficos**: tiles de la fuente (Ñ, vocales acentuadas), logo y pantallas retocadas, con sus mapas de tiles.
- **Cabecera**: serial (`GM T-24076 -01`), textos de copyright ("EXTREME / LLC SHINYUDEN / RATALAIKA GAMES, S.L.") y **checksum recalculado correctamente** (`0x7FF6`, verificado contra la suma real).

**Cero cambios de código.** En particular:

- Los **15 vectores de excepción** de la CPU apuntan a `0xDFFC` en ambas ROMs, idénticos.
- Las únicas referencias absolutas a SRAM (`lea $200081`, en `0x154FA` y `0x15664`) están en los mismos offsets, y **el módulo de guardado completo es byte a byte idéntico** al original (solo cambian los mensajes de UI traducidos, incrustados en el mismo hueco).
- No aparece ningún puntero nuevo hacia la ventana de SRAM (`$200000+`).

### Cómo guarda partida Sorcerer's Kingdom

El sistema (de Technical Wave, los desarrolladores originales de 1993) usa los 8 KB de SRAM declarados en cabecera (`$200001-$203FFF`, bytes impares):

| Zona SRAM (bus) | Contenido |
|---|---|
| `$200021-$20003F` | Firma de validez: `"TECHNICAL-WAVE!!"` (cadena en ROM `0x15598`) |
| `$200081` + 8·n | Directorio de Crónicas: registro de 8 bytes de bus por slot con **3 bytes de checksum** |
| `$200101+` | Datos de las partidas |

Al guardar, la rutina `0x157BC` recorre una tabla de regiones de RAM (en ROM `0x15532`) acumulando **tres sumas de verificación** que se almacenan en el registro del slot; la escritura se verifica por comparación. Al cargar, si las sumas no cuadran, el juego muestra los mensajes de partida dañada/destruida citados arriba. Es decir: **los reportes de los usuarios son el mecanismo de integridad del propio juego detectando datos corruptos**, no un cuelgue descontrolado.

---

## ⚡ Hipótesis principal: la PCB moderna (mezcla 3,3V / 5V)

Descartado el software (la ROM ES es funcionalmente equivalente a una USA original que jamás tuvo fama de corromper partidas), la sospecha se centra en la placa de la reedición. Componentes identificados en la PCB (`Ver1.4 2025`; fotos en [`pcb/`](pcb/)):

| Componente | Referencia | Dato clave |
|---|---|---|
| Flash NOR | Spansion **S29GL064N90TFI04** (64 Mbit, 90 ns, ©2006) | Alimentación **2,7-3,6V exclusivamente**; sus entradas no son tolerantes a 5V de forma sostenida |
| SRAM | NEC **µPD43256BGU-85LL** (32K×8, 85 ns) | Chip de la era de los **5V** (retención a 2V para batería); *date code* `0014` → fabricado en el **año 2000** (stock reciclado/NOS) |
| Regulador | **AMS1117-3.3** | Crea el raíl de 3,3V de la flash: confirma la mezcla de dominios en la placa |
| Decodificador | **74HC139D** | Genera los *chip selects* de flash y SRAM |
| Interfaz de bus | **RN1-RN10**, redes de 4×100Ω (`101`) | La adaptación 5V→3,3V se resuelve con **resistencias en serie**, confiando en el clamping de los diodos de protección internos de la flash (fuera de especificación; práctica habitual en placas repro) |
| Batería | CR2032 + D2/D3 (diodo-OR) + discretos | **Sin IC supervisor visible** (los cartuchos originales bloquean el `/CE` de la SRAM cuando la alimentación cae de ~4,5V) |
| Variante | Footprint **"FRAM"** sin poblar (jumper + Q1/R3) | El diseño contemplaba una versión sin batería |

Modos de fallo plausibles con este diseño:

1. **Escrituras espurias en el apagado/encendido**: la lógica que genera el `/CE` de la SRAM (74HC139) cuelga del raíl principal, no de la batería. Durante los transitorios de alimentación sus salidas pasan por estados indefinidos mientras la SRAM sigue alimentada por la pila → ventana clásica de escritura basura. La corrupción aparecería asociada a ciclos de encendido, no al juego en sí.
2. **Integridad de señal marginal** en el bus compartido 5V/3,3V con resistencias en serie: niveles lógicos al límite e inyección de corriente en el raíl de 3,3V, sensibles a temperatura, revisión de consola y tolerancias (explicaría por qué solo afecta a algunos usuarios).
3. La observación de la comunidad de que el fallo se manifiesta **al guardar en múltiples slots** encaja: más escrituras a SRAM = más exposición a los dos mecanismos anteriores.

> El trazado exacto del circuito de batería/protección (si Q1 llega a gatear el `/CE`) no puede confirmarse solo con fotos; requiere seguir pistas con un polímetro. Es una de las tareas abiertas del plan de validación.

> ⚠️ **Estado: hipótesis pendiente de validación empírica.** El análisis de la ROM es concluyente (la traducción no es la causa), pero la culpabilidad exacta del circuito debe confirmarse con las pruebas de abajo.

---

## 🧪 Plan de validación (cómo ayudar)

1. **Test de ciclos de encendido**: con una partida guardada, apagar y encender la consola 30-50 veces *sin jugar*. Si aparece corrupción, la placa queda señalada directamente.
2. **Grupo de control**: la misma ROM ES en flashcart (EverDrive) o emulador durante sesiones largas con muchos guardados. Si ahí nunca se corrompe y en el cartucho físico sí, confirmado.
3. **Guardado en múltiples slots** en hardware real, reproduciendo el patrón que reporta la comunidad.
4. **Recopilar archivos `.srm` corruptos sin manipular** (volcados directamente del cartucho): el patrón de daño distingue el origen — bits/bytes sueltos alterados apuntan a fallo eléctrico; estructuras sobreescritas reconocibles apuntarían a software. La herramienta `tools/srm_diagnose.py` de este repositorio automatiza ese análisis.
5. **Trazado del circuito de protección de la SRAM** sobre la PCB real (continuidad con polímetro): confirmar de qué raíl cuelga el 74HC139 y si existe algún gating del `/CE` en el apagado. Las fotos de la placa están en [`pcb/`](pcb/).

---

## 🛠️ Herramientas incluidas

- `tools/sorcerer_rom_analyzer.py` — cabeceras, hashes y comparación binaria de las ROMs (equivalente al analizador de TraysiaROMFix).
- `tools/srm_diagnose.py` — diagnóstico de archivos `.srm`: comprueba la firma `TECHNICAL-WAVE!!`, lista el directorio de Crónicas con sus checksums, y compara dos `.srm` (sano vs corrupto) con estadísticas de bits alterados para caracterizar el patrón de corrupción.

### 📂 Organización de las ROMs
Coloca las ROMs en `roms/` en la raíz del repositorio:
* **Sorcerer's Kingdom (ES).md** — reedición en castellano de 2026.
* **Sorcerer's Kingdom (U) (1993) [!].bin** — revisión USA de la que deriva.
* **Sorcerer's Kingdom (U) (1992).bin** — primera revisión USA (referencia).

Los `.srm` de referencia generados en emulador (RetroArch/BlastEm, RomBundlerDX) sirven como muestra sana para comparar contra volcados de cartuchos afectados.

---

## 📌 Cómo contribuir

- Ejecutando el plan de validación (sobre todo los puntos 1-3) y reportando resultados.
- Aportando `.srm` corruptos de cartuchos reales, sin pasarlos por ninguna herramienta.
- Aportando fotos de alta resolución de la PCB o mediciones del circuito.

---

## 🧠 Créditos y Licencia

- Investigación, análisis y documentación por **@Arcanbytes**.
- Gracias a la comunidad (TodoRPG, Luis Shinyuden y los usuarios afectados) por los reportes y la difusión.

Licencia: MIT – puedes usar, modificar y compartir este contenido libremente.
