# Taller: anatomía e ingeniería inversa de archivos ejecutables

**IS753 · Compiladores · Universidad Tecnológica de Pereira**
**Integrantes:** Juan David Cortes, Sebastián Prada, Valentina Lasprilla
**Fecha de entrega:** 20/11/2026
**Formato nativo analizado en profundidad:** PE32+ (Windows) · **Formato gestionado:** Java Class / JAR

---

## 1. Entorno de ejecución

Todas las mediciones nativas se hicieron en la estación Windows descrita abajo. No se usó
Colab ni máquina virtual para el formato nativo, porque Colab produce ELF y el objeto de
análisis de esta pareja es PE32+.

| Componente | Versión utilizada |
|---|---|
| Sistema operativo | Windows 10, build 10.0.19045 (SP0) |
| Arquitectura | AMD64 / x86-64 |
| Compilador C | MinGW-w64 GCC (MSYS2), en `C:\msys64\mingw64\bin\gcc.EXE` — versión: <<<PEGAR SALIDA DE `gcc --version`>>> |
| Inspección binaria | GNU binutils: `objdump`, `nm`, `readelf` (misma instalación de MSYS2) |
| JDK | Oracle JDK 17.0.6, en `C:\Program Files\Java\jdk-17` |
| Python / kernel | <<<PEGAR SALIDA DE `python --version`>>> , Jupyter Notebook |
| Dependencias Python | Solo biblioteca estándar (`pathlib`, `struct`, `subprocess`, `hashlib`, `zipfile`, `re`, `json`, `shutil`, `platform`, `dataclasses`) |

---

## 2. Adaptaciones respecto al enunciado, y su justificación

El enunciado plantea MSVC (`cl.exe`, `dumpbin.exe`) para la rama de Windows. Esta pareja no
disponía de MSVC Build Tools, así que el taller se ejecutó con la cadena MinGW. Las dos
adaptaciones hechas fueron:

1. **Compilación con `gcc` en lugar de `cl`.** MinGW produce igualmente **PE32+ nativo**, que
   es el objeto de análisis; lo que cambia es la cadena de herramientas, no el formato. Se
   verificó con el parser propio en Python: firma `MZ`, `PE\0\0` en 0x80, `Machine` = 0x8664,
   `Magic` = 0x20b (PE32+).
   Banderas usadas: `-O0 -g` para la muestra legible y `-O2` para la optimizada.

2. **Inspección con `objdump` y `nm` en lugar de `dumpbin`.** Equivalencias aplicadas:
   `dumpbin /headers` → `objdump -f` y `objdump -h`; `dumpbin /imports` → `objdump -x`
   (sección *Import Tables*); `dumpbin /disasm` → `objdump -d`; símbolos → `nm`.

3. **JDK invocado por ruta completa.** El `PATH` del sistema solo exponía `java.exe` y
   `javac.exe` a través de la carpeta puente `C:\Program Files\Common Files\Oracle\Java\javapath`,
   que no incluye `javap` ni `jar`. Las celdas de Java se adaptaron para invocar los
   ejecutables del JDK 17 por ruta absoluta. Esto además fija la versión: `major` 61 (Java SE 17).

Consecuencia documentada en el cuaderno: con MinGW los símbolos quedan **incrustados** en el
binario junto con DWARF en secciones `.debug_*`, mientras con MSVC habrían dependido de un
archivo PDB externo. Se contrastó con la entrega de un compañero que sí usó MSVC (Kenneth
Rodríguez): su `sample_O0.exe` tiene 8 secciones y PDB separados; el nuestro, 20 secciones y
símbolos internos.

---

## 3. Estructura del entregable

```
<raiz-del-zip>/
├── README.md                                  este archivo
├── Taller_Formatos_Ejecutables_...ipynb       cuaderno diligenciado y ejecutado
├── fuentes/                                   fuentes propias (reveladas al final)
│   ├── sample.c                               muestra nativa del taller
│   ├── Sample.java                            muestra Java homologa
│   ├── mystery.c                              funcion del reto (version C)
│   └── Mystery.java                           funcion del reto (version Java)
├── binarios/
│   ├── sample_O0.exe  sample_O2.exe           PE32+ sin optimizar y optimizado
│   ├── Sample.class   sample.jar              bytecode y JAR ejecutable
│   ├── java_no_debug/Sample.class             compilado con -g:none
│   ├── java_release_11/Sample.class           compilado con --release 11 (major 55)
│   ├── java_release_17/Sample.class           compilado con --release 17 (major 61)
│   ├── mystery.exe    Mystery.class           binarios del reto
│   └── sample_O0_elf                          muestra ELF64 (ver seccion 6)
├── evidencias/
│   ├── native_evidence_0.txt  objdump -f
│   ├── native_evidence_1.txt  objdump -h  (tabla de secciones)
│   ├── native_evidence_2.txt  objdump -x  (cabeceras, secciones, importaciones, simbolos)
│   ├── native_evidence_3.txt  nm          (tabla de simbolos)
│   ├── native_evidence_4.txt  objdump -d  (desensamblado completo)
│   ├── java_evidence.txt      javap -c -p -s -v Sample
│   └── resultados_referencia.txt           salidas de mystery(x) para x = 0..20
└── reto_mystery_CortesPradaLasprilla.zip     paquete entregado a la otra pareja
                                             (binarios + README, SIN fuente)
```

No se incluyen carpetas de SDK ni del JDK, ni los archivos intermedios de compilación.

---

## 4. Pasos de reproducción

1. Instalar MinGW-w64 (vía MSYS2) y asegurarse de que `gcc`, `objdump` y `nm` estén en el `PATH`.
2. Instalar JDK 17. No es necesario ponerlo en el `PATH`: el cuaderno lo invoca por ruta
   absoluta. Si su JDK está en otra ruta, ajuste la variable `JDK_BIN` en las celdas de Java.
3. Abrir el cuaderno con Jupyter **desde una terminal normal, no como administrador**. Si se
   abre desde un PowerShell elevado, el directorio de trabajo inicial es `C:\Windows\System32`
   y el laboratorio se crearía dentro de una carpeta del sistema.
4. Ejecutar `Kernel → Restart & Run All`. El cuaderno corre completo, 18 celdas de código, sin
   intervención manual. La segunda celda fija el directorio de trabajo en
   `%USERPROFILE%\executable_lab`, independientemente de dónde se haya abierto Jupyter.
5. La última celda es una **auditoría**: reimprime hashes, campos de cabecera, versión del
   class y la conversión de dirección, para contrastarlos con las tablas del cuaderno.

**Advertencia sobre los hashes.** Volver a ejecutar el cuaderno regenera los binarios y
cambia su SHA-256, aunque la fuente y las banderas sean idénticas (ver sección 7). Si se
reejecuta, los hashes de las tablas deben actualizarse con la salida de la celda de auditoría.

---

## 5. Hashes de las muestras entregadas

| Archivo | Bytes | SHA-256 |
|---|---:|---|
| `sample_O0.exe` | 255 409 | `83d357c6af9942371527739e4e8079995c616639b8a8751ebf0721d44539705d` |
| `sample_O2.exe` | 254 296 | `9519e17261d4d47576bf619e0ea0591a53691fde8b573031e31a89e5092609a6` |
| `Sample.class` (`-g`) | 1 307 | `67d288243daa39d60aa28fdecf171b5b57f5999e22191b6a2e11dd78934431bc` |
| `Sample.class` (`-g:none`) | 1 054 | `8a2e6a2f0982b0a786281f4f24a6f82612e60f89df10ee82fcc4f4c052bdff54` |
| `sample.jar` | 1 216 | `4d2b8aeb757f62d4a3908de19fcee72bd0d6899f52bdb816b0961f55f673c207` |

Muestra recibida para el reto, producida por **Kenneth Santiago Rodríguez Ramírez** (MSVC
19.44 sobre Windows 11, JDK 21). No se presenta como medición propia:

| Archivo | SHA-256 |
|---|---|
| `mystery.exe` | `0903c578768fe6ace546eb6313f5c13b68260e581f3cb7deb536a5f65a07403c` |
| `Mystery.class` | `d9d3d08a118fbf14c36675d1b52e571cd5f4d923ded96b071cc2c90aa7b25f5d` |

---

## 6. Celdas que no se ejecutaron, y lo que no se obtuvo

- **Rama `dumpbin` de la inspección nativa (sección 6):** no ejecutada, por ausencia de MSVC.
  Se sustituyó por la rama equivalente con `objdump` y `nm`, documentada en la sección 2.
- **Ramas de Linux y macOS de la misma celda:** no aplicables a esta plataforma.
- **Versión original de las celdas de Java:** fallaba con
  `RuntimeError: Instale o configure en PATH: javap`. Se sustituyó por la versión que invoca
  el JDK por ruta absoluta.
- **Muestra Mach-O 64:** **no obtenida.** No se dispuso de macOS ni de evidencia de otra
  pareja para ese formato. La columna correspondiente de la matriz queda explícitamente
  declarada como no medida; el modelo conceptual se completó desde la fuente primaria
  (`loader.h` de Apple), sin reportar valores inventados.
- **Muestra ELF64:** la misma `sample.c` se compiló y midió en un entorno Linux x86-64 con
  gcc 13.3.0 durante la preparación del taller, **no en la estación Windows**. Se reporta
  con esa procedencia explícita en la matriz comparativa.
- **Sección 9, análisis dinámico:** ampliación opcional, no realizada. La inspección se
  mantuvo estática en todo el taller.

---

## 7. Nota de reproducibilidad

Al recompilar la misma fuente con las mismas banderas, los binarios nativos **cambian de
SHA-256 conservando el tamaño exacto**: `sample_O0.exe` pasó de `d0265afa…` a `18677f24…` y
luego a `83d357c6…`, siempre con 255 409 bytes. El enlazador de MinGW incrusta metadatos de
compilación en la imagen.

En cambio `Sample.class` conserva su hash entre compilaciones, porque `javac` es determinista.

De ahí dos conclusiones que se sostienen con las mediciones del cuaderno: el hash identifica
un artefacto concreto y no una fuente, y la reproducibilidad byte a byte depende de la cadena
de herramientas, no del lenguaje.
