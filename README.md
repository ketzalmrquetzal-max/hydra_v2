# 🐲 HYDRA V2 - Trading AI System

> Sistema de trading automatizado con IA que integra análisis técnico, sentimiento de mercado y ejecución inteligente.

## 📂 Estructura del Proyecto

```
HydraV1/
├── 🚀 hydra_core.py          # Orquestador principal (ejecuta el loop de trading)
├── 📋 requirements.txt        # Dependencias de Python
├── 🔐 .env                    # Credenciales (NO compartir)
├── 📖 README.md               # Este archivo
│
├── 🖥️ frontend/               # Dashboard Web (React-like)
│   └── index.html             # Command Center visual
│
├── ⚙️ backend/                # Núcleo del sistema
│   ├── main.py                # Servidor FastAPI (Dashboard API)
│   ├── app/
│   │   ├── core/              # Configuración y logging
│   │   │   ├── config.py      # Settings del sistema
│   │   │   └── forensic_logger.py
│   │   │
│   │   ├── application/       # Lógica de negocio
│   │   │   ├── risk_manager.py       # El Guardián
│   │   │   ├── execution_service.py  # El Verdugo
│   │   │   └── strategies/
│   │   │       ├── balam_brain.py    # Cerebro estratega
│   │   │       ├── technical_analyst.py
│   │   │       └── evidence_generator.py
│   │   │
│   │   └── infrastructure/    # Conexiones externas
│   │       ├── binance/
│   │       │   ├── mock_exchange.py      # Simulador
│   │       │   └── testnet_connector.py  # Binance Testnet
│   │       │
│   │       ├── sentinel/      # El Centinela (Análisis de mercado)
│   │       │   ├── sentinel_service.py
│   │       │   ├── news_fetcher.py
│   │       │   ├── sentiment_brain.py
│   │       │   └── gemini_http_client.py
│   │       │
│   │       └── telegram/      # Notificaciones
│   │           └── telegram_adapter.py
│   │
│   └── logs/                  # Logs forenses (gitignored)
│
├── 📜 scripts/                # Scripts de utilidad
│   ├── phase3_runner.py       # Menú de testing del Sentinel
│   └── genesis.py             # Script de inicialización
│
├── 🧪 tests/                  # Tests del sistema
│   ├── test_balam.py
│   ├── test_sentinel.py
│   ├── test_telegram.py
│   └── test_phase6.py
│
├── 📚 docs/                   # Documentación
│   ├── FASE3_GUIA.md
│   └── FIX_TELEGRAM_401.md
│
└── 📓 notebooks/              # Jupyter notebooks (análisis)
```

## 🚀 Inicio Rápido

### 1. Activar entorno virtual
```bash
.\venv\Scripts\activate
```

### 2. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 3. Configurar credenciales
Edita `.env` con tus API keys:
- `GEMINI_API_KEY` - Google AI Studio
- `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`
- `BINANCE_TESTNET_API_KEY` y `BINANCE_TESTNET_SECRET`

### 4. Ejecutar

**Dashboard + API:**
```bash
python backend\main.py
```

**Loop de trading automático:**
```bash
python hydra_core.py --cycles 5 --test
```

**Solo Sentinel (análisis de mercado):**
```bash
python scripts\phase3_runner.py
```

## 🐲 Módulos del Sistema

| Módulo | Archivo | Función |
|--------|---------|---------|
| 🛡️ El Guardián | `risk_manager.py` | Protección de capital, kill switch |
| 👁️ El Centinela | `sentinel_service.py` | Análisis de noticias y sentimiento |
| 🧠 Balam | `balam_brain.py` | Decisiones estratégicas |
| ⚔️ El Verdugo | `execution_service.py` | Ejecución de órdenes |
| 📊 Dashboard | `frontend/index.html` | Visualización en tiempo real |
| 📱 Telegram | `telegram_adapter.py` | Notificaciones móviles |

## ⚠️ Seguridad

- **NUNCA** subas `.env` a Git
- Usa **Testnet** antes de dinero real
- El `kill switch` está activo por defecto

---

**Versión:** 2.0  
**Última actualización:** Diciembre 2024
