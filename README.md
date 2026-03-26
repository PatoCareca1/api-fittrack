# FitTrack API

API REST para análise de composição corporal por visão computacional.

A partir de imagens do usuário (frontal + lateral, opcionalmente dorsal), o sistema
extrai landmarks corporais, calcula medidas antropométricas e estima métricas de
composição corporal com intervalos de confiança — usando equações validadas na
literatura científica.

---

## Stack

- **Python 3.11+** — linguagem principal
- **FastAPI** — framework da API
- **Pydantic v2** — validação e serialização
- **SQLAlchemy 2.x async + Alembic** — ORM e migrações
- **PostgreSQL** — banco de dados
- **MediaPipe** — extração de landmarks corporais
- **OpenCV** — processamento de imagens
- **PyTorch / scikit-learn** — modelos de ML

---

## Pré-requisitos

- Python 3.11+
- [uv](https://github.com/astral-sh/uv) (gerenciador de pacotes)
- PostgreSQL rodando localmente ou via URL remota

---

## Instalação

```bash
# Clonar o repositório
git clone https://github.com/seu-usuario/fittrack-api.git
cd fittrack-api

# Instalar dependências
uv sync

# Copiar e configurar variáveis de ambiente
cp .env.example .env
# edite .env com suas credenciais
```

---

## Configuração

Edite o arquivo `.env` com as variáveis necessárias:

```env
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/fittrack
SECRET_KEY=sua-chave-secreta-aqui
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

Para gerar uma `SECRET_KEY` segura:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Executando

```bash
# Desenvolvimento com hot reload
uv run uvicorn app.main:app --reload

# A API estará disponível em:
# http://localhost:8000
# Documentação interativa: http://localhost:8000/docs
# Schema OpenAPI: http://localhost:8000/openapi.json
```

---

## Endpoints

### Públicos

| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/auth/register` | Criar conta |
| `POST` | `/auth/login` | Autenticar e obter tokens |
| `POST` | `/auth/refresh` | Rotacionar refresh token |
| `POST` | `/analyze` | Análise anônima (sem conta) |
| `GET` | `/health` | Health check |

### Protegidos (requer Bearer token)

| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/history` | Histórico de análises do usuário |
| `GET` | `/analyses/{id}` | Detalhes de uma análise |

---

## Uso — Análise de Composição Corporal

```bash
curl -X POST http://localhost:8000/analyze \
  -F "files=@foto_frontal.jpg;pose=front" \
  -F "files=@foto_lateral.jpg;pose=lateral" \
  -F "height_cm=175" \
  -F "weight_kg=75" \
  -F "age=30" \
  -F "sex=male"
```

**Resposta:**

```json
{
  "analysis_id": "uuid",
  "timestamp": "2025-01-01T00:00:00Z",
  "poses_used": ["front", "lateral"],
  "measurements": {
    "waist": { "value": 82.0, "uncertainty": 1.5, "unit": "cm" },
    "hip":   { "value": 96.0, "uncertainty": 1.5, "unit": "cm" },
    "neck":  { "value": 38.0, "uncertainty": 1.0, "unit": "cm" },
    "arm":   { "value": 32.0, "uncertainty": 1.0, "unit": "cm" },
    "height":{ "value": 175.0, "uncertainty": 0.5, "unit": "cm" }
  },
  "metrics": {
    "body_fat_percentage": {
      "value": 18.5,
      "lower_bound": 15.0,
      "upper_bound": 22.0,
      "method": "navy",
      "confidence": "medium"
    },
    "bri":  { "value": 3.2, "lower_bound": 2.9, "upper_bound": 3.5, "method": "bri", "confidence": "medium" },
    "absi": { "value": 0.077, "lower_bound": 0.073, "upper_bound": 0.081, "method": "absi", "confidence": "medium" },
    "waist_to_height_ratio": { "value": 0.47, "lower_bound": 0.44, "upper_bound": 0.50, "method": "whtr", "confidence": "high" },
    "waist_to_hip_ratio":    { "value": 0.85, "lower_bound": 0.82, "upper_bound": 0.88, "method": "whr", "confidence": "high" }
  },
  "disclaimer": "Esta análise é uma estimativa baseada em visão computacional e não substitui avaliação profissional de saúde."
}
```

---

## Como Funciona

O FitTrack transforma fotos em dados de composição corporal em quatro etapas:

```
Fotos (2–3 poses)
       │
       ▼
┌─────────────────┐
│   pose/         │  MediaPipe extrai 33 landmarks corporais por imagem.
│                 │  Cada ponto tem coordenadas (x, y) normalizadas e
│                 │  score de visibilidade. Pose frontal é obrigatória.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  calibration/   │  Converte landmarks de pixels para centímetros reais
│                 │  usando a altura informada pelo usuário como escala.
│                 │  É o único módulo que conhece a relação px/cm.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  measurements/  │  Calcula circunferências (cintura, quadril, pescoço,
│                 │  braço) e comprimentos de membros a partir dos
│                 │  landmarks calibrados. Retorna Measurement com
│                 │  valor, incerteza e unidade.
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  estimation/    │  Aplica equações científicas validadas sobre as
│                 │  medidas para estimar composição corporal.
│                 │  Retorna BodyMetrics com intervalos de confiança.
└─────────────────┘
```

### Degradação graceful

Se uma pose falhar durante a extração de landmarks, o sistema não retorna erro — retorna resultado parcial com `confidence=low` e warnings descrevendo o que foi afetado. A única exceção é a pose frontal: se ela falhar, a análise é interrompida.

### Por que não IMC?

O IMC é incapaz de distinguir massa magra de gordura corporal. Um atleta com alta massa muscular e um sedentário com obesidade podem ter o mesmo IMC. O FitTrack usa métricas clinicamente mais robustas como métricas primárias, calculando o IMC apenas como referência histórica quando peso e altura são informados.

---

## Base Científica

### Pipeline de visão computacional

Estudos recentes validam a abordagem por foto 2D de smartphone como método confiável de estimativa de composição corporal:

- **Majmudar et al. (2022)** — CNN com fotos frontais e dorsais de smartphone vs DXA (padrão-ouro): MAE de 2.16 ± 1.54%, concordância CCC de 0.94. Superou vários dispositivos de bioimpedância. *npj Digital Medicine.*
- **Alves et al. (2025)** — Estudo com 1.273 adultos comparando AI-2D photo, DXA, skinfolds, ultrassom e bioimpedância. O método AI-2D photo obteve CCC de 0.96–0.98 vs DXA — o melhor resultado entre todos os métodos avaliados. *npj Digital Medicine.*

### Equações de estimativa

#### Percentual de gordura — Navy Method *(prioritário)*

Baseado em circunferências — input natural de visão computacional. Erro padrão (SEE) de ±3–4%.

**Homens:**

```
%G = 495 / (1.0324 − 0.19077 × log₁₀(cintura − pescoço) + 0.15456 × log₁₀(altura)) − 450
```

**Mulheres:**

```
%G = 495 / (1.29579 − 0.35004 × log₁₀(cintura + quadril − pescoço) + 0.22100 × log₁₀(altura)) − 450
```

> Hodgdon JA, Beckett MB. *Prediction of percent body fat for US Navy men and women.* Naval Health Research Center, 1984.

#### Percentual de gordura — Deurenberg *(baseline comparativo)*

Usa IMC, idade e sexo. Calculado em paralelo para comparação. SEE ±3.6%.

```
%G = (1.20 × IMC) + (0.23 × idade) − (10.8 × sexo) − 5.4
```

> Deurenberg P et al. *Body mass index as a measure of body fatness.* British Journal of Nutrition, 1991.

#### Body Roundness Index — BRI

Superior ao IMC na predição de gordura visceral e risco cardiometabólico.

```
BRI = 364.2 − 365.5 × √(1 − ((cintura / 2π)² / (0.5 × altura)²))
```

> Thomas DM et al. *A novel body shape index and body roundness index.* Obesity, 2013.

#### A Body Shape Index — ABSI

Isola o efeito da circunferência da cintura, independente de peso e altura. Preditor independente de mortalidade.

```
ABSI = cintura / (IMC^(2/3) × altura^(1/2))
```

> Krakauer NY, Krakauer JC. *A new body shape index predicts mortality hazard independently of body mass index.* PLOS ONE, 2012.

#### Waist-to-Height Ratio — WHtR

Simples e robusto. WHtR > 0.5 indica risco cardiometabólico elevado em todas as etnias e faixas etárias.

```
WHtR = cintura / altura
```

> Ashwell M et al. *Waist-to-height ratio is a better screening tool than waist circumference and BMI.* Obesity Reviews, 2012.

#### Razão Cintura-Quadril — RCQ

Indicador de distribuição de gordura e risco cardiovascular.

```
RCQ = cintura / quadril
```

> WHO Expert Consultation. *Waist circumference and waist-hip ratio.* 2008.

### Intervalos de confiança

Todas as estimativas retornam `lower_bound` e `upper_bound` (IC 95%). Na Fase 1, os intervalos usam o SEE publicado de cada equação como proxy. Na Fase 2, serão substituídos por propagação de incerteza em cadeia desde o erro de detecção de landmarks até o erro da equação final (ADR-008).

---

## Métricas de Composição Corporal

O FitTrack não usa IMC como métrica principal. Em vez disso, calcula métricas
mais robustas clinicamente:

| Métrica | Descrição | Referência |
|---|---|---|
| **%Gordura (Navy)** | Equação baseada em circunferências | Hodgdon & Beckett, 1984 |
| **%Gordura (Deurenberg)** | Baseline comparativo via IMC | Deurenberg et al., 1991 |
| **BRI** | Body Roundness Index — gordura visceral | Thomas et al., 2013 |
| **ABSI** | A Body Shape Index — preditor de mortalidade | Krakauer & Krakauer, 2012 |
| **WHtR** | Razão cintura-altura — risco cardiovascular | Ashwell et al., 2012 |
| **RCQ** | Razão cintura-quadril | WHO, 2008 |

Todas as estimativas retornam **intervalo de confiança de 95%** — nunca valores
pontuais isolados.

---

## Estrutura do Projeto

```
fittrack-api/
├── app/
│   ├── api/
│   │   ├── routes/          # Endpoints por domínio
│   │   └── dependencies/    # Injeção de dependências (auth, db)
│   ├── core/
│   │   ├── config.py        # Settings via variáveis de ambiente
│   │   ├── exceptions.py    # Exceções do domínio
│   │   └── security.py      # JWT + hashing
│   ├── modules/
│   │   ├── pose/            # Extração de landmarks (MediaPipe)
│   │   ├── calibration/     # Conversão pixels → centímetros
│   │   ├── measurements/    # Medidas antropométricas
│   │   ├── estimation/      # Equações de composição corporal
│   │   └── segmentation/    # Isolamento do corpo — Fase 2
│   ├── models/
│   │   ├── schemas/         # Pydantic — contratos da API
│   │   └── orm/             # SQLAlchemy — tabelas
│   ├── db/
│   │   └── migrations/      # Alembic
│   └── main.py
├── tests/
│   ├── unit/
│   └── integration/
├── docs/
│   ├── teoria/              # Base científica por módulo
│   └── decisoes/            # ADRs
├── notebooks/               # Experimentação científica
├── .env.example
├── pyproject.toml
└── README.md
```

---

## Testes

```bash
# Todos os testes
uv run pytest

# Apenas unitários
uv run pytest tests/unit/ -v

# Com coverage
uv run pytest --cov=app tests/

# Linting
uv run ruff check app/

# Formatação
uv run black --check app/
```

---

## Roadmap

### Fase 1 — Fundação ✅ (em andamento)

- [x] Infraestrutura base (FastAPI, PostgreSQL, JWT)
- [x] Schemas Pydantic centrais
- [x] Módulo estimation completo (Navy, Deurenberg, BRI, ABSI, WHtR, RCQ)
- [x] Stubs funcionais para pose, calibration, measurements
- [ ] Migrações Alembic
- [ ] Documentação teórica (`docs/teoria/`)

### Fase 2 — Refinamento

- [ ] MediaPipe real nos módulos de CV
- [ ] Segmentação com SAM
- [ ] Pose dorsal (3ª perspectiva)
- [ ] Modelo de regressão treinado (NHANES)
- [ ] Propagação de incerteza em cadeia

### Fase 3 — Interface

- [ ] Frontend Nuxt 3 (`fittrack-web`)
- [ ] Dashboard longitudinal
- [ ] Deploy completo

---

## Decisões Arquiteturais

As decisões de design estão documentadas como ADRs em `docs/decisoes/`
e resumidas no `CLAUDE.md` na raiz do projeto.
