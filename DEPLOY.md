# Guía de Acceso Remoto y Despliegue

Para permitir que "cualquiera con usuario y contraseña pueda usar el sistema sin necesidad de estar conectado a la misma red", existen dos opciones principales:

## Opción 1: Ngrok (Más fácil, para pruebas o uso temporal)
Ngrok crea un túnel seguro desde tu computadora a internet.

1.  **Descargar Ngrok**: Ve a [ngrok.com](https://ngrok.com) y regístrate (es gratis). Descarga el ejecutable.
2.  **Instalar**: Descomprime el archivo.
3.  **Autenticar**: Ejecuta el comando que te da ngrok en su dashboard (ej: `ngrok config add-authtoken TU_TOKEN`).
4.  **Iniciar el túnel**:
    Con tu sistema corriendo en el puerto 8000 (`uvicorn main:app --reload`), abre otra terminal y ejecuta:
    ```bash
    ngrok http 8000
    ```
5.  **Compartir**: Ngrok te dará una URL pública (ej: `https://a1b2-c3d4.ngrok-free.app`).
    - Comparte esa URL con los usuarios.
    - Ellos entrarán a `https://.../static/login.html` para usar el sistema.

> **Nota**: En la versión gratuita, la URL cambia cada vez que reinicias ngrok.

## Opción 2: Despliegue en la Nube (Permanente)
Para una solución profesional, se recomienda usar un servicio como **Render** o **Railway**.

### Guía Paso a Paso para Render.com (Gratis/Barato)

El proyecto ya está configurado para desplegarse automáticamente.

1.  **Subir a GitHub**:
    - Asegúrate de que todo tu código (incluyendo `Procfile`, `requirements.txt`, `runtime.txt`) esté en un repositorio de GitHub.

2.  **Crear servicio en Render**:
    - Crea una cuenta en [render.com](https://render.com).
    - Haz clic en **"New +"** -> **"Web Service"**.
    - Conecta tu repositorio de GitHub.

3.  **Configuración del Web Service**:
    - **Name**: Elige un nombre (ej: `agenda-medica`).
    - **Region**: La más cercana (ej: Ohio o Frankfurt).
    - **Branch**: `main` (o la rama donde esté tu código).
    - **Root Directory**: Déjalo vacío (o `.` si lo pide).
    - **Runtime**: `Python 3`.
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `gunicorn main:app -k uvicorn.workers.UvicornWorker` (Render debería detectarlo automáticamente gracias al `Procfile`).

4.  **Variables de Entorno (Environment Variables)**:
    - Haz clic en "Advanced" o ve a la pestaña "Environment" después de crear.
    - Agrega:
        - `PYTHON_VERSION`: `3.10.12`
        - `SECRET_KEY`: Genera una clave segura y pégala aquí.

5.  **Base de Datos (PostgreSQL)**:
    - En el dashboard de Render, haz clic en **"New +"** -> **"PostgreSQL"**.
    - Ponle un nombre (ej: `agenda-db`).
    - Copia la **Internal Database URL** (empieza con `postgres://...`).
    - Vuelve a tu Web Service -> Environment.
    - Agrega una variable llamada `DATABASE_URL` y pega la URL que copiaste.

6.  **Finalizar**:
    - Render desplegará tu aplicación.
    - Te dará una URL permanente (ej: `https://agenda-medica.onrender.com`).
    - Al entrar, verás el login. ¡Listo!

> **Importante**: La base de datos en la nube estará vacía. Deberás crear el primer usuario (Admin) usando la API o conectándote a la base de datos.
