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
5. **RedShift:** Warehouse serverless para cargar la data de los archivos

# Proceso

<img src="https://github.com/CrissAlvarezH/otel-observability/blob/main/docs/images/entire_process_diagram.png"/>
