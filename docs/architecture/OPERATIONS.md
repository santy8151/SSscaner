# Operación antes de datos reales

El Compose es un banco local. Pendiente: separar propietario de esquema y rol runtime PostgreSQL, migraciones, RLS por transacción, TLS, cookie/IdP y CSRF cuando aplique, límites distribuidos, rotación de secretos, monitorización y backups.

## Backup y restauración

Propuesta: `pg_dump -Fc` con identidad de backup que pueda leer todas las empresas; guardar dentro del contenedor y copiar con `docker compose cp` para evitar corrupción de binarios por redirección PowerShell. Cifrar antes de guardar fuera del host, retención acordada, registrar actor/fecha/hash. No poner credenciales en comandos ni repositorio.

Restaurar con `pg_restore` en base de prueba vacía. Verificar recuentos de todas las empresas, relaciones, hashes de especificaciones y sesiones. Medir RPO/RTO. Esta fase no instala backups programados ni afirma haber probado restauración PostgreSQL.

Crear el esquema inicial no migra tablas existentes. Los próximos cambios requieren migraciones versionadas antes de reutilizar datos. No borrar la base del usuario para solucionar incompatibilidades.
