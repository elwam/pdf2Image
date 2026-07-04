@echo off
setlocal EnableExtensions

set "IMAGE_NAME=pdf2image"
set "CONTAINER_NAME=pdf2image_container"
set "HOST_PORT=9005"
set "CONTAINER_PORT=8000"

pushd "%~dp0"

echo [1/5] Verificando Docker...
where docker >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker no esta instalado o no esta en el PATH.
    echo Instala/abre Docker Desktop e intenta de nuevo.
    popd
    exit /b 1
)

docker info >nul 2>nul
if errorlevel 1 (
    echo ERROR: Docker no esta corriendo.
    echo Abre Docker Desktop y espera a que el motor este listo.
    popd
    exit /b 1
)

echo [2/5] Deteniendo contenedor anterior si existe...
docker rm -f "%CONTAINER_NAME%" >nul 2>nul

echo [3/5] Construyendo imagen %IMAGE_NAME%...
docker build -t "%IMAGE_NAME%" .
if errorlevel 1 (
    echo ERROR: Fallo la construccion de la imagen.
    popd
    exit /b 1
)

echo [4/5] Levantando contenedor %CONTAINER_NAME%...
docker run -d --restart unless-stopped --name "%CONTAINER_NAME%" -p %HOST_PORT%:%CONTAINER_PORT% "%IMAGE_NAME%"
if errorlevel 1 (
    echo ERROR: No se pudo levantar el contenedor.
    echo Revisa si el puerto %HOST_PORT% ya esta ocupado.
    popd
    exit /b 1
)

echo [5/5] Esperando respuesta de la API...
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='SilentlyContinue'; $url='http://localhost:%HOST_PORT%/'; for ($i=1; $i -le 30; $i++) { try { $r=Invoke-WebRequest -UseBasicParsing -Uri $url -TimeoutSec 2; if ($r.StatusCode -ge 200 -and $r.StatusCode -lt 500) { exit 0 } } catch { Start-Sleep -Seconds 1 } }; exit 1"
if errorlevel 1 (
    echo ADVERTENCIA: El contenedor inicio, pero la API no respondio aun.
    echo Revisa logs con: docker logs %CONTAINER_NAME%
) else (
    echo API disponible en: http://localhost:%HOST_PORT%
    echo Swagger UI:       http://localhost:%HOST_PORT%/docs
)

popd
endlocal
