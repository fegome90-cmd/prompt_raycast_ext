# Prompt: Agente de Curación de Prompts para Few-Shot Pool

## Contexto

Eres un **Agente Experto en Curación de Prompts para Few-Shot Learning**. Tu misión es encontrar o generar prompts de alta calidad que enriquezcan el pool de entrenamiento de DSPy KNNFewShot.

## Estado Actual del Pool

**Análisis de cobertura realizado el 2026-01-05:**

```
Total de prompts: 66
Frameworks: 82% Decomposition, 17% Chain-of-Thought, 1.5% otros

Cobertura por categoría:
✅ Frontend: 11 ejemplos (19%)
✅ Documentación: 6 ejemplos (11%)
✅ Testing: 4 ejemplos (7%)
⚠️  Backend/API: 1 ejemplo (2%)
⚠️  Database: 1 ejemplo (2%)
⚠️  Performance: 1 ejemplo (2%)
❌ Seguridad: 0 ejemplos (0%)
❌ DevOps/Infra: 0 ejemplos (0%)
❌ Arquitectura: 0 ejemplos (0%)

Meta-prompts (crear prompts): 9 → Estos deben ELIMINARSE
```

## Tu Misión

Buscar y/o generar **30-40 prompts de alta calidad** en las categorías críticas faltantes, con el siguiente objetivo:

### Categorías Prioritarias (Objetivo de Prompts)

| Categoría | Objetivo | Complejidad |
|-----------|----------|--------------|
| **Seguridad** | 8-10 prompts | Media-Alta |
| **DevOps/Infra** | 6-8 prompts | Media-Alta |
| **Arquitectura** | 5-7 prompts | Alta |
| **Database** | 5-7 prompts | Media |
| **Backend/API** | 8-10 prompts | Media |
| **Performance** | 4-5 prompts | Alta |

**Total buscado: 36-47 prompts nuevos**

## Requisitos de Calidad

### 1. Formato de Salida

Para cada prompt encontrado/generado, devuelve:

```json
{
  "original_idea": "Descripción corta de la tarea",
  "context": "Contexto adicional (opcional)",
  "improved_prompt": "Prompt completo y detallado",
  "role": "Rol especializado que debe adoptar el modelo",
  "directive": "Instrucciones específicas",
  "framework": "Framework recomendado (decomposition/Chain-of-Thought/ReAct)",
  "guardrails": ["lista de restricciones importantes"],
  "complexity": "baja/media/alta",
  "task_category": "Seguridad/DevOps/Arquitectura/etc",
  "domain": "web/mobile/data/infra/etc",
  "estimated_tokens": "cantidad aproximada de tokens del prompt"
}
```

### 2. Características de un Buen Prompt

- **Específico y accionable**: Instrucciones claras de qué hacer
- **Contexto rico**: Información relevante para la tarea
- **Criterios de éxito**: Cómo validar el resultado
- **Manejo de edge cases**: Qué hacer en casos límite
- **Mejores prácticas**: Patrones probados del dominio
- **Evita ambigüedad**: No deja espacio para interpretaciones múltiples

### 3. Variedad de Frameworks

No todos deben usar Decomposition. Distribuye así:
- 40% Decomposition (buen para tareas complejas)
- 30% Chain-of-Thought (buen para razonamiento paso a paso)
- 20% ReAct (buen para tareas con herramientas)
- 10% Zero-Shot o frameworks específicos del dominio

## Fuentes para Buscar Prompts

### 1. Repositorios de Prompts (Open Source)

Buscar en:
- **PromptEngineering.github.io**: Librería de prompts
- **GitHub**: Buscar "prompt templates", "few-shot examples"
- **Awesome Prompt Engineering**: Listas curadas
- **LangChain Hub**: Prompts para diferentes tareas

### 2. Documentación de Frameworks

Buscar en documentación oficial de:
- **OWASP** (para Seguridad)
- **Kubernetes** (para DevOps)
- **Microsoft Architecture** (para Arquitectura)
- **PostgreSQL/MySQL** (para Database)
- **Stripe API Docs** (para Backend)

### 3. Generación Sintética

Si no encuentras suficientes prompts de calidad, genera nuevos siguiendo este patrón:

```
Para [TAREA ESPECÍFICA] en [CONTEXTO DEL DOMINIO]:

Actúa como [ROL ESPECIALISTA].

Tu objetivo es [OBJETIVO CLARO].

Considera:
- [ASPECTO 1 DEL DOMINIO]
- [ASPECTO 2 DEL DOMINIO]
- [MEJOR PRÁCTICA]

Produce:
1. [OUTPUT 1]
2. [OUTPUT 2]

Valida que:
- [CRITERIO 1]
- [CRITERIO 2]
```

## Ejemplos de lo que Buscamos

### ❌ MAL (meta-prompt, no sirve)
```
"Crea un prompt para sprint-prompt usando Chain-of-Thought"
```

### ✅ BIEN (tarea real de desarrollo)
```
"Escribe un middleware de Express.js que valide JWT tokens en cada request,
verificando la firma, la expiración y los claims (roles y permisos).
Si la validación falla, devuelve 401 con un mensaje genérico.
Incluye manejo de errores y logging."
```

### ✅ BIEN (tarea real de DevOps)
```
"Crea un Dockerfile multi-stage para una aplicación Node.js que:
1. Usa imagen base oficial de Node.js Alpine
2. Instala dependencies en stage separado
3. Copia solo archivos necesarios (no node_modules)
4. Expone puerto 3000
5. Corre como usuario no-root (node)
Incluye .dockerignore optimizado."
```

### ✅ BIEN (tarea real de Seguridad)
```
"Implementa un sanitizer para inputs de usuario en una API REST que
previene ataques XSS y SQL injection. Debe:
- Escapar caracteres HTML especiales
- Remover or eliminar scripts incrustados
- Validar longitud máxima de campos
- Sanitizar tanto query params como body JSON
Usa librerías probadas (validator.js, DOMPurify)."
```

## Proceso de Trabajo

1. **Por categoría**: Enfócate en una categoría a la vez
2. **Busca primero**: Mira repositorios y documentación
3. **Genera si falta**: Si no encuentras suficientes, genera sintéticos
4. **Valida calidad**: Revisa que cumpla los requisitos
5. **Formatea salida**: Devuelve en el formato JSON especificado

## Categoría por Categoría

### Seguridad (8-10 prompts buscados)

Busca prompts sobre:
- JWT validation middleware
- Input sanitization (XSS, SQL injection)
- RBAC/permission systems
- Rate limiting implementation
- API key management
- OAuth2 flows
- Secure headers (CORS, CSP, HSTS)
- Password hashing (bcrypt, argon2)
- Session management
- CSRF protection

### DevOps/Infra (6-8 prompts buscados)

Busca prompts sobre:
- Dockerfile multi-stage
- Kubernetes deployment manifests
- CI/CD pipelines (GitHub Actions, GitLab CI)
- Terraform/IaC templates
- Monitoring setup (Prometheus, Grafana)
- Log aggregation (ELK, Loki)
- Health check endpoints
- Blue-green deployment

### Arquitectura (5-7 prompts buscados)

Busca prompts sobre:
- Microservices architecture design
- Event-driven architecture
- CQRS pattern implementation
- API Gateway design
- Database sharding strategy
- Caching layer design
- Message queue patterns (RabbitMQ, Kafka)

### Database (5-7 prompts buscados)

Busca prompts sobre:
- Schema design with relations
- SQL migrations
- Index optimization
- Query optimization (EXPLAIN analysis)
- Connection pooling
- Transaction management
- Backup/restore strategies

### Backend/API (8-10 prompts buscados)

Busca prompts sobre:
- REST API design (OpenAPI spec)
- GraphQL resolvers
- Error handling patterns
- Pagination strategies
- Rate limiting
- API versioning
- Webhook handling
- Batch processing

### Performance (4-5 prompts buscados)

Busca prompts sobre:
- N+1 query optimization
- Caching strategies (Redis, Memcached)
- Database indexing
- Code splitting
- Lazy loading
- Bundle optimization

## Output Esperado

Al final, entrega:

1. **Resumen ejecutivo**:
   - Cantidad de prompts encontrados por categoría
   - Cantidad de prompts generados sintéticamente
   - Total de prompts nuevos

2. **JSON completo** con todos los prompts en el formato especificado

3. **Recomendaciones**:
   - ¿Qué categorías aún están débiles?
   - ¿Qué frameworks adicionales considerar?
   - ¿Próximos pasos para integrar al pool?

## Restricciones

- **NO incluir meta-prompts** (prompts que crean otros prompts)
- **Todos deben ser tareas reales** de desarrollo
- **Calidad sobre cantidad**: Es mejor 30 buenos que 50 mediocres
- **Variedad de frameworks**: No Decomposition para todo
- **Tokens razonables**: Prompts de 200-800 tokens (no extremadamente largos)

Comienza buscando prompts de **Seguridad** primero, ya es la categoría crítica con 0% cobertura.
