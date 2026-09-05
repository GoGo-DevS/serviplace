# Verificación automatizada de ServiPlace. La corren LOS DOS agentes.
#
# Es el paso del medio del loop: Claude implementa -> ESTO -> Codex revisa.
# Sin él, Codex tendría que reproducir a mano cada criterio en cada ciclo y
# tres vueltas no alcanzarían.
#
#   .\verificar.ps1            todo
#   .\verificar.ps1 -Rapido    salta la parte del navegador (sin levantar server)
#
# Cada bloque imprime el identificador del criterio de TASK.md (A1, B3, D2…)
# para que REVIEW.md pueda citarlo. Sale con código 1 si algo falla, así que
# sirve tal cual como puerta.
#
# La salida cruda queda en verificacion.txt.

param([switch]$Rapido)

$ErrorActionPreference = 'Continue'
Set-Location $PSScriptRoot

$py = Join-Path (Split-Path $PSScriptRoot -Parent) 'venv\Scripts\python.exe'
if (-not (Test-Path $py)) { $py = Join-Path $PSScriptRoot 'venv\Scripts\python.exe' }
if (-not (Test-Path $py)) { Write-Host 'No encuentro el intérprete de Python.' -ForegroundColor Red; exit 2 }

# Python 3.13 arranca su REPL nuevo cuando cree tener consola y, llamado desde
# PowerShell, revienta con "WinError 0: la operación se completó correctamente"
# ANTES de ejecutar nada. `manage.py check` pasaba perfecto por otra vía: el
# fallo era del entorno, no del proyecto. Sin esto, la verificación reportaría
# defectos que no existen — y un verificador que miente es peor que ninguno.
$env:PYTHON_BASIC_REPL = '1'
$env:PYTHONIOENCODING = 'utf-8'

$log = Join-Path $PSScriptRoot 'verificacion.txt'
"ServiPlace — verificación $(Get-Date -Format 'dd-MM-yyyy HH:mm:ss')" | Set-Content $log -Encoding utf8

$fallos = @()
function Bloque([string]$titulo) {
  Write-Host ''
  Write-Host "── $titulo " -ForegroundColor Cyan -NoNewline
  Write-Host ('─' * [Math]::Max(0, 58 - $titulo.Length)) -ForegroundColor DarkGray
  "`n== $titulo ==" | Add-Content $log -Encoding utf8
}
function Correr([string]$cid, [string]$que, [string[]]$args) {
  $salida = & $py @args 2>&1
  $salida | Add-Content $log -Encoding utf8
  if ($LASTEXITCODE -eq 0) {
    Write-Host "  [PASS] $cid  $que" -ForegroundColor Green
  } else {
    Write-Host "  [FAIL] $cid  $que" -ForegroundColor Red
    ($salida | Select-Object -Last 6) | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
    $script:fallos += "$cid ($que)"
  }
}

# ── A: el proyecto está sano ───────────────────────────────────────────────
Bloque 'A · El proyecto arranca'
Correr 'A1' 'manage.py check' @('manage.py', 'check')
Correr 'A2' 'migraciones al día' @('manage.py', 'makemigrations', '--check', '--dry-run')

# ── B/C: las pruebas de Django ─────────────────────────────────────────────
# Corren sobre una base de test descartable; nunca tocan db.sqlite3.
Bloque 'B/C · Pruebas (seguridad, autorización, datos)'
$antes = Get-Date
$salida = & $py manage.py test --verbosity 2 2>&1
$salida | Add-Content $log -Encoding utf8
$resumen = $salida | Select-String -Pattern '^(Ran|OK|FAILED)' | ForEach-Object { $_.ToString() }
$cuantas = ($salida | Select-String -Pattern '^Ran (\d+) test' | ForEach-Object { $_.Matches[0].Groups[1].Value })
if ($LASTEXITCODE -eq 0) {
  if ([int]($cuantas | Select-Object -First 1) -eq 0) {
    Write-Host '  [FAIL] B/C  la suite corre pero NO HAY NI UNA PRUEBA' -ForegroundColor Red
    Write-Host '         Una suite vacía siempre pasa: no es evidencia de nada.' -ForegroundColor DarkGray
    $fallos += 'B/C (suite vacía)'
  } else {
    Write-Host "  [PASS] B/C  $($resumen -join ' · ')" -ForegroundColor Green
  }
} else {
  Write-Host "  [FAIL] B/C  $($resumen -join ' · ')" -ForegroundColor Red
  ($salida | Select-String -Pattern '^(FAIL|ERROR):' | Select-Object -First 8) | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
  $fallos += 'B/C (pruebas)'
}
Write-Host "         ($([int]((Get-Date) - $antes).TotalSeconds)s)" -ForegroundColor DarkGray

# ── B6: check --deploy con DEBUG=False ─────────────────────────────────────
Bloque 'B6 · Configuración de producción'
$env:DEBUG = 'False'
$env:ALLOWED_HOSTS = 'serviplace.cl'
# La clave tiene que ser larga y variada o `check --deploy` la marca (W009) y
# el fallo sería del verificador, no del proyecto. No es una clave real: nunca
# sale de este proceso.
$env:SECRET_KEY = 'verificacion-J7xQ2m-Kp9vLw4Tz-Rb8Nc3Hd6Yf1Sg5Aj0Ue-no-es-la-real'
# Y un DATABASE_URL de mentira: settings aborta a propósito si arranca en
# producción con SQLite (en Render se borra en cada deploy). Esa guarda está
# BIEN; sin esta línea el verificador la interpretaba como un defecto.
$env:DATABASE_URL = 'postgres://verificacion:x@localhost:5432/verificacion'
$salida = & $py manage.py check --deploy --fail-level ERROR 2>&1
$salida | Add-Content $log -Encoding utf8
if ($LASTEXITCODE -eq 0) {
  $w = ($salida | Select-String -Pattern '^\?:').Count
  Write-Host "  [PASS] B6  sin errores con DEBUG=False ($w advertencia(s) menores)" -ForegroundColor Green
} else {
  Write-Host '  [FAIL] B6  check --deploy arroja errores' -ForegroundColor Red
  ($salida | Select-String -Pattern '^\?:' | Select-Object -First 6) | ForEach-Object { Write-Host "         $_" -ForegroundColor DarkGray }
  $fallos += 'B6 (check --deploy)'
}
Remove-Item Env:DEBUG, Env:ALLOWED_HOSTS, Env:SECRET_KEY, Env:DATABASE_URL -ErrorAction SilentlyContinue

# ── C1/C2: nada falso publicado ────────────────────────────────────────────
# Va acá y no en las pruebas porque mira la base REAL, no una de test: es la
# que se va a publicar.
Bloque 'C · Datos publicados'
$salida = & $py -c @'
import os, django, sys
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()
from directory.models import Provider
malos = []
act = Provider.objects.filter(is_active=True)
falsos = act.filter(whatsapp_number__startswith='5691111')
if falsos.exists():
    malos.append(f'C1: {falsos.count()} activos con telefono sintetico 5691111')
sin = act.filter(source_name='') | act.filter(source_url='')
if sin.exists():
    malos.append(f'C2: {sin.distinct().count()} activos sin source_name o source_url')
print(f'  {act.count()} prestadores activos')
for m in malos:
    print('  ' + m)
sys.exit(1 if malos else 0)
'@ 2>&1
$salida | Add-Content $log -Encoding utf8
$salida | ForEach-Object { Write-Host "  $_" -ForegroundColor DarkGray }
if ($LASTEXITCODE -eq 0) { Write-Host '  [PASS] C1 C2  nada sintético ni sin fuente está publicado' -ForegroundColor Green }
else { Write-Host '  [FAIL] C1/C2' -ForegroundColor Red; $fallos += 'C1/C2 (datos publicados)' }

# ── A3/A4/C3/D/E: el navegador ─────────────────────────────────────────────
if ($Rapido) {
  Bloque 'Navegador'
  Write-Host '  [SALTADO] -Rapido: no se midieron A3, A4, C3, D1-D4, E1-E3' -ForegroundColor Yellow
  '  SALTADO por -Rapido' | Add-Content $log -Encoding utf8
} else {
  Bloque 'A3 A4 C3 D E · Navegador real (390 y 1440 px)'
  $puerto = 8021
  Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -like "*runserver*$puerto*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
  $srv = Start-Process -FilePath $py -ArgumentList 'manage.py', 'runserver', "$puerto", '--noreload' `
                       -WindowStyle Hidden -WorkingDirectory $PSScriptRoot -PassThru
  # Se espera a que conteste de verdad, no un sleep fijo: en una máquina
  # cargada 3 segundos no alcanzan y la medición fallaría por eso.
  $vivo = $false
  foreach ($i in 1..20) {
    Start-Sleep -Milliseconds 700
    try { Invoke-WebRequest -UseBasicParsing "http://127.0.0.1:$puerto/" -TimeoutSec 4 | Out-Null; $vivo = $true; break } catch {}
  }
  if (-not $vivo) {
    Write-Host '  [FAIL] el servidor de prueba no respondió' -ForegroundColor Red
    $fallos += 'navegador (servidor no arrancó)'
  } else {
    $salida = & $py 'verificacion\medir_navegador.py' "http://127.0.0.1:$puerto" 2>&1
    $codigo = $LASTEXITCODE
    $salida | Add-Content $log -Encoding utf8
    $salida | ForEach-Object {
      $c = if ($_ -match '\[FAIL\]|\[ERROR\]') { 'Red' } elseif ($_ -match '\[PASS\]') { 'Green' } else { 'DarkGray' }
      Write-Host "$_" -ForegroundColor $c
    }
    if ($codigo -ne 0) { $fallos += 'navegador (D/E)' }
  }
  if ($srv -and -not $srv.HasExited) { Stop-Process -Id $srv.Id -Force -ErrorAction SilentlyContinue }
}

# ── Veredicto ──────────────────────────────────────────────────────────────
Write-Host ''
Write-Host ('═' * 62) -ForegroundColor DarkGray
if ($fallos.Count -eq 0) {
  Write-Host ' VERIFICACIÓN COMPLETA: todo lo medible de TASK.md pasa.' -ForegroundColor Green
  Write-Host ' Esto NO es un PASS del ciclo: el veredicto lo da Codex en REVIEW.md.' -ForegroundColor DarkGray
  "`nRESULTADO: todo pasa" | Add-Content $log -Encoding utf8
  exit 0
}
Write-Host " VERIFICACIÓN: $($fallos.Count) bloque(s) fallando" -ForegroundColor Red
$fallos | ForEach-Object { Write-Host "   · $_" -ForegroundColor Red }
Write-Host " Detalle crudo en verificacion.txt" -ForegroundColor DarkGray
"`nRESULTADO: fallan $($fallos -join ', ')" | Add-Content $log -Encoding utf8
exit 1
