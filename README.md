# Descripción
Proyecto a modo de ejercicio para utilizar Open Telemetry en un sistema distribuido.

# Diseño
El sistema tiene 4 aplicaciones
1. **Frontend:** Interfaz de usuario que permite seleccionar archivos desde la máquina local y subirlos a S3
2. **Files Service:** Servicio que se comunica con S3 para generar URLs prefirmadas y almacenar la metadata de los archivos subidos en la base de datos
3. **Auth Service:** Sistema de autenticación simplificado que valida tokens pre-almacenados en una tabla de la base de datos
4. **Load Pipeline:** Procesa mensajes de la cola que representan archivos subidos a S3 y carga sus datos en una tabla del warehouse Redshift

Y cuenta con los siguientes componentes en su arquitectura (orientada a aws)
1. **EC2 Instances:** Instancias donde se ejecutan el Frontend y los servicios (API Rest) Files Service y Auth Service
2. **DynamoDB:** Base de datos NoSQL para almacenar la metadata de los archivos subidos
3. **S3:** Servicio de almacenamiento donde se guardan los archivos enviados desde el Frontend
4. **SQS:** Servicio de colas para gestionar los archivos guardados en S3
5. **Lambda:** Servicio serverless donde se despliega el Load Pipeline
6. **CodeBuild:** Servicio para construir el lambda function para la app Load Pipeline
7. **RedShift:** Data warehouse serverless para el análisis de los datos de los archivos

# Proceso

<img src="https://github.com/CrissAlvarezH/otel-observability/blob/main/docs/images/entire_process_diagram.png"/>


# Correr el proyecto

### 1. Configurar aws cli

Instalar [aws cli](https://aws.amazon.com/es/cli/) en la maquina cliente y configurar las credenciales de acceso a aws con los permisos necesarios para crear los recursos de la infraestructura.

### 2. Configurar variables de entorno (Opcional)

Si deseas cambiar los valores por defecto (descritos a continuacion) puedes hacerlo creando un archivo `.env` en la raiz del proyecto, basado en el archivo `.env.example`:
#### Valores por defecto
- `AWS_REGION`: `us-east-1`
- `S3_BUCKET_NAME`: `otel-files-service`


### 3. Crear el stack de infraestructura

```bash
make setup
```

El anterior comando creará todos los recursos necesarios en aws para el proyecto, en CloudFormation el nombre del stack es `otel-observability`.

> **Importante:**
> Espera hasta que el stack se cree completamente antes de continuar. Usa `make status` para monitorear el progreso. Cuando el estado sea `CREATE_COMPLETE`, puedes proceder.

> **Nota:**
> Por simplicidad se utiliza la VPC por defecto para crear el Redshift Serverless Workgroup, asegurate de tener una en la region especificada.

### 4. Desplegar aplicaciones
```bash
make deploy
```
El anterior comando se conectará a las instancias EC2 creadas en el paso anterior y desplegará las aplicaciones de `frontend`, `files service` y `auth service` construyendo imagenes docker pada cada una en sus respectivas instancias. Ademas, lanzara un projecto de CodeBuild para empaquetar y desplegar el lambda `load-pipeline`.
Una vez terminado el deploy verás en la console las urls de acceso a cada una de las aplicaciones.
Ejemplo:

```bash
Frontend: http://34.0.10.10/
Files Service: http://34.0.10.10/docs
Auth Service: http://34.0.10.10/docs
```

## A tener en cuenta
2. Redshift: usuario `otel`, contraseña `OtelObservability123`

## Comandos de utilidad

1. `make destroy`: Destruye el stack de infraestructura
2. `make get-ip app=<app>`: Obtiene la ip publica de una instancia EC2
3. `make output`: Obtiene los outputs del stack de infraestructura (guardados en *outputs.json*)
4. `make connect app=<app>`: Conecta a una instancia EC2 y le permite ejecutar comandos
5. `make logs app=<app>`: Obtiene los logs de una aplicación
6. `make status`: Obtiene el estado del stack de infraestructura
7. `make info`: Obtiene información de las aplicaciones desplegadas (region, bucket name, ips, etc)

> Valores validos para `<app>`: `frontend`, `files-service`, `auth-service`

### Datasets de ejemplo
- [ExploreToM (Hugging Face) 31MB](https://huggingface.co/datasets/facebook/ExploreToM/blob/main/ExploreToM-data-sample.csv)
