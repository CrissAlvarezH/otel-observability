# Descripción
Proyecto a modo de ejercicio para utilizar Open Telemetry en un sistema distribuido.

# Diseño
El sistema tiene 4 aplicaciones
1. **Frontend:** Encargado de presnetar la UI y permitir seleccionar archivos desde la maquina cliente y subirlos a S3
2. **Files Service:** Es el backend que se comunica con S3 para generar urls prefirmadas y tambien guardar en la base de datos los archivos subidos
3. **Auth Service:** Es un sistema de autenticación muy simplificado para este ejercicio el cual solo consiste en validar tokens preguardados en un tabla de la base de datos
4. **Load Pipeline:** Es el encargado de tomar los mensajes de la cola que representan archivos subidos a S3 y cargar la data contenida en ellos hacia una tabla de un warehouse en Redshift

Y cuenta con los siguientes componentes en su arquitectura (orientada a aws)
1. **EC2 Instances:** Donde corren los servicios (API Rest) "Files Service" y "Auth Service"
2. **RDS:** Base de datos
3. **S3:** Donde se guardarán los archivos enviados desde el Frontend
4. **SQS:** Cola para archivos guardados en S3
5. **Lambda:** Donde estará desplegado el Load Pipeline
6. **RedShift:** Warehouse serverless para cargar la data de los archivos

# Proceso

<img src="https://github.com/CrissAlvarezH/otel-observability/blob/main/docs/images/entire_process_diagram.png"/>


# Correr el proyecto

### 1. Configurar aws cli

Instalar [aws cli](https://aws.amazon.com/es/cli/) en la maquina cliente y configurar las credenciales de acceso a aws con los permisos necesarios para crear los recursos de la infraestructura.

### 2. Crear el stack de infraestructura

```bash
make setup
```

El anterior comando creará los recursos necesarios en aws para el proyecto, el nombre del stack es `otel-observability`.

> **Importante:**
> Es necesario esperar a que el stack se cree completamente antes de continuar con el siguiente paso, para esto se puede ejecutar el comando `make status` que mostrará el estado del stack cada 2 segundos, cuando el estado sea `CREATE_COMPLETE` prosigue con el siguiente paso.

### 3. Desplegar los servicios y aplicaciones
```bash
make deploy
```
El anterior comando se conectará a las instancias EC2 creadas en el paso anterior y desplegará las aplicaciones de `frontend`, `files service` y `auth service` construyendo imagenes docker pada cada una en sus respectivas instancias.
Una vez terminado el deploy verás en la console las urls de acceso a cada una de las aplicaciones.
Ejemplo:

```bash
Frontend: http://34.0.10.10/
Files Service: http://34.0.10.10/docs
Auth Service: http://34.0.10.10/docs
```

## Comandos de utilidad

1. `make destroy`: Destruye el stack de infraestructura
2. `make get-ip app=<app>`: Obtiene la ip publica de una instancia EC2
3. `make output`: Obtiene los outputs del stack de infraestructura (guardados en *outputs.json*)
4. `make connect app=<app>`: Conecta a una instancia EC2 y le permite ejecutar comandos
5. `make logs app=<app>`: Obtiene los logs de una aplicación
6. `make status`: Obtiene el estado del stack de infraestructura

> Valores validos para `<app>`: `frontend`, `files-service`, `auth-service`
