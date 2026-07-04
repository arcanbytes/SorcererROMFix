# 🔧 Recomendaciones técnicas

Propuestas derivadas del análisis de [SorcererROMFix](README.md): cómo evitar el problema de corrupción de partidas en futuras placas, y cómo minimizar el riesgo con los cartuchos actuales.

> ⚠️ La hipótesis de hardware está pendiente de validación empírica (ver el [plan de validación](README.md#-plan-de-validación-cómo-ayudar)). Estas recomendaciones son medidas de prudencia razonada basadas en los modos de fallo identificados en la PCB.

---

## 🏭 Para el diseño de la próxima PCB

### Opción A — La solución limpia: diseño 100% de 5V (recomendada)

El problema de raíz es la mezcla de dominios de voltaje en un bus de 1993. Se elimina por completo con dos cambios:

1. **Flash de 5V nativa** — p. ej. AMD **AM29F800B** o Macronix **MX29F800** (8 Mbit, los clásicos de las placas repro de calidad, disponibles en el canal surplus). Desaparecen el regulador de 3,3V, las redes de resistencias y el clamping fuera de especificación.
2. **FRAM en lugar de SRAM + pila** — Infineon/Cypress **FM18W08** (32K×8, 2,7-5,5V, pinout compatible con la µPD43256). Sin batería que agotar y con **monitor de alimentación interno que bloquea el acceso cuando el voltaje no es válido**: inmune por diseño a la corrupción por apagado. La PCB Ver1.4 ya tiene el footprint "FRAM" previsto — la solución estaba dibujada en la propia placa.

### Opción B — Si se mantiene la arquitectura actual, fixes mínimos

1. **Proteger la SRAM (el fix indispensable)**: un controlador de NVRAM tipo **DS1210** (Analog Devices/Maxim) entre el `/CE` del decodificador y la SRAM — hace la conmutación a batería **y bloquea el chip enable cuando VCC cae del umbral**. Es lo que llevaban los cartuchos originales de Sega y lo que le falta a esta placa. Alternativa de bajo coste: supervisor de reset (MAX809/APX811) forzando `/CE` alto mediante una puerta OR.
2. **Adaptación de niveles real para la flash de 3,3V**: sustituir las redes de 100Ω por transceptores **74LVC** (entradas tolerantes a 5V, salidas de 3,3V que el 68000 lee correctamente por ser niveles TTL): 74LVC16244 para direcciones/control, 74LVC16245 para el bus de datos.
3. **Componentes de producción actual**: evitar chips NOS de hace 25 años (la SRAM montada tiene *date code* del año 2000); introducen una lotería de envejecimiento entre unidades.

### En cualquier caso

- **Test de producción**: guardar partida + 30 ciclos de encendido + verificar integridad, antes de enviar cada lote. Es un minuto por cartucho y habría detectado este problema en fábrica.
- **Validación multi-consola**: probar en varias revisiones reales (Model 1 VA0-VA7, Model 2, FPGA, algún clon) antes de aprobar el diseño. Un fallo que solo aparece en ciertas revisiones es síntoma de margen eléctrico insuficiente, no de mala suerte.
- Pedir al fabricante de la PCB el **esquemático** como parte del encargo: sin él no se puede auditar la protección de la SRAM ni la interfaz de niveles.

---

## 🎮 Para los usuarios del cartucho actual

La ventana de riesgo son los transitorios de alimentación y el momento de la escritura:

1. **Apaga y enciende con decisión** — interruptor de un golpe seco, sin dejarlo a medio recorrido. Tras apagar, espera 5-10 segundos antes de volver a encender.
2. **Nunca apagues justo después de guardar.** Guarda, vuelve al juego, espera unos segundos y entonces apaga.
3. **El botón RESET es inofensivo para la partida** (no corta la alimentación): si solo quieres reiniciar, mejor RESET que apagar y encender.
4. Si se confirma el patrón de los múltiples slots, **usar un único slot** reduce las escrituras y por tanto la exposición.
5. **Haz copia de seguridad del save** periódicamente con un lector de cartuchos (OSCR, Retrode). Es la única red de seguridad real.
6. **Consola oficial con fuente en buen estado** (o FPGA tipo Mega Sg): es plausible que los clones baratos agraven el problema — raíles de 5V pobres (4,7-4,8V), reguladores ruidosos y rampas de apagado sucias reducen aún más el margen de la interfaz resistiva. Mantén limpio el conector del cartucho: los contactos sucios producen microcortes con el mismo efecto que un apagado.
