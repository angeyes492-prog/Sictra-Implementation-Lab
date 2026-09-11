# Bloque 3 — plantilla oficial y admisión de dominios para shadow run v0.1

**Estado:** `USER-APPROVED TEMPLATE SCHEMA / NOT YET EXPORTED AS XLSX`.

## Plantilla oficial `Accounts`

La primera fila debe conservar exactamente estos encabezados, en este orden:

| Columna | Encabezado Excel | Requerido | Uso permitido |
|---|---|---:|---|
| A | `Account ID` | sí | identidad estable de la cuenta dentro del tenant |
| B | `Official Website` | sí | URL HTTPS oficial, sin query, fragment o credenciales |
| C | `Company Name` | no | declaración operativa para revisión; nunca fact automático |
| D | `Source Reference` | no | referencia humana del origen de la fila |

No deben añadirse `Tenant`, `Purpose`, emails, teléfonos, nombres de personas,
contraseñas, tokens ni columnas ocultas. Tenant y propósito se ligan fuera del
archivo; las columnas adicionales se rechazan por diseño.

Ejemplo válido:

```text
Account ID | Official Website             | Company Name     | Source Reference
ACME-001   | https://www.example.com/     | Example Company  | approved-list-001
```

## Admisión de dominios

La delegación de aprobación cubre el esquema de plantilla y la evaluación
técnica de una URL declarada. No convierte al sistema en selector autónomo de
prospectos. Para cada cuenta, la lista debe identificar la empresa o su URL
oficial; el flujo verifica que:

1. la URL sea HTTPS canónica y esté en la fila aceptada;
2. el revisor humano vincule explícitamente tenant, archivo, hash, fila, cuenta
   y fingerprint antes de la consulta;
3. el crawler sólo siga el dominio y subdominios aprobados, respetando
   `robots.txt`, límites y cuarentena;
4. el resultado sea un dossier shadow y no contacto, CRM write o afirmación de
   hechos.

Una URL encontrada fuera de la fila —por búsqueda general, anuncio, directorio
o red social— no se convierte en dominio objetivo sin introducirla primero en
un lote revisable. Esto mantiene auditabilidad y evita investigar empresas no
incluidas en el alcance del usuario.

## Próximo acto operativo permitido

Cuando el runtime de hojas esté disponible, se exportará esta plantilla como
`.xlsx`. Después podrá importarse una copia con cuentas reales explícitamente
seleccionadas por el usuario para un shadow run sin CRM ni delivery.
