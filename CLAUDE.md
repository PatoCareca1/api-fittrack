# CLAUDE.md — FitTrack

## Visão Geral do Projeto

FitTrack é um sistema de análise de composição corporal por visão computacional.
A partir de imagens do usuário (2 ou 3 perspectivas), o sistema extrai landmarks
corporais, calcula medidas antropométricas e estima métricas de composição corporal
utilizando equações validadas na literatura científica.

O objetivo é oferecer uma ferramenta acessível, não invasiva e cientificamente
embasada para que qualquer pessoa interessada em saúde possa entender sua composição
corporal e acompanhar sua evolução ao longo do tempo.

O produto é composto por uma API (FastAPI) e uma interface web completa (Nuxt 3),
com autenticação, persistência de dados e dashboard de acompanhamento longitudinal.

---

## Arquitetura Geral

O projeto é dividido em dois repositórios independentes com deploy separado:

```
fittrack/
├── fittrack-api/        # Backend — FastAPI
└── fittrack-web/        # Frontend — Nuxt 3
```

### fittrack-api

```
fittrack-api/
├── app/
│   ├── api/
│   │   ├── routes/              # Endpoints organizados por domínio
│   │   │   ├── auth.py          # Registro, login, refresh
│   │   │   ├── analysis.py      # Upload de imagens e disparo de análise
│   │   │   └── history.py       # Histórico de análises do usuário
│   │   └── dependencies/        # Dependências injetáveis (auth, db, etc.)
│   │       ├── auth.py          # get_current_user (JWT)
│   │       └── database.py      # get_db (sessão async)
│   ├── core/
│   │   ├── config.py            # Configurações via variáveis de ambiente
│   │   ├── exceptions.py        # Exceções customizadas do domínio
│   │   └── security.py          # Hashing de senha, criação/validação de JWT
│   ├── modules/
│   │   ├── pose/                # Extração de landmarks (MediaPipe)
│   │   ├── segmentation/        # Isolamento do corpo (SAM)
│   │   ├── calibration/         # Conversão de pixels para centímetros
│   │   ├── measurements/        # Cálculo de medidas antropométricas
│   │   └── estimation/          # Estimativa de composição corporal
│   ├── models/
│   │   ├── schemas/             # Schemas Pydantic (request/response)
│   │   └── orm/                 # Modelos SQLAlchemy (tabelas do banco)
│   ├── db/
│   │   └── migrations/          # Migrações Alembic
│   └── main.py                  # Entrypoint da aplicação
├── tests/
│   ├── unit/
│   └── integration/
├── notebooks/                   # Experimentação e validação científica
├── docs/
│   ├── teoria/                  # Fundamentos científicos por módulo
│   └── decisoes/                # Registro de decisões arquiteturais (ADRs)
├── .env.example
├── pyproject.toml
└── README.md
```

### fittrack-web

```
fittrack-web/
├── pages/
│   ├── index.vue                # Landing page pública (SSR — indexável)
│   ├── auth/
│   │   ├── login.vue
│   │   └── register.vue
│   └── app/
│       ├── analyze.vue          # Upload de imagens e resultado
│       └── history.vue          # Dashboard longitudinal
├── components/
│   ├── analysis/                # Componentes do fluxo de análise
│   └── charts/                  # Visualizações de histórico
├── composables/                 # Lógica reutilizável (useAnalysis, useAuth)
├── stores/                      # Pinia — estado global
├── services/                    # Chamadas à API (axios)
├── types/                       # Tipos TypeScript espelhando os schemas da API
├── nuxt.config.ts
└── README.md
```

---

## Stack Tecnológica

### Backend (fittrack-api)

| Tecnologia | Uso |
|---|---|
| Python 3.11+ | Linguagem principal |
| FastAPI | Framework da API REST |
| Pydantic v2 | Validação e serialização de dados |
| SQLAlchemy 2.x async | ORM e queries ao banco |
| Alembic | Migrações do banco de dados |
| PostgreSQL | Banco de dados principal |
| python-jose + passlib | JWT e hashing de senha |
| MediaPipe | Extração de pose e landmarks |
| OpenCV | Processamento de imagens |
| SAM (Segment Anything) | Segmentação corporal |
| PyTorch | Modelos de deep learning |
| scikit-learn | Regressão e utilitários de ML |
| Black | Formatação de código |
| Ruff | Linting |
| Pytest + pytest-asyncio | Testes |

### Frontend (fittrack-web)

| Tecnologia | Uso |
|---|---|
| Nuxt 3 | Framework Vue com SSR/SSG |
| Vue 3 | UI reativa |
| TypeScript | Tipagem estática |
| Pinia | Gerenciamento de estado |
| Axios | Requisições HTTP |
| TailwindCSS | Estilização |
| Chart.js / Vue-ChartJS | Visualizações de dados |

### Infraestrutura

| Componente | Tecnologia |
|---|---|
| Backend deploy | Railway / Render / VPS |
| Frontend deploy | Vercel / Netlify |
| Banco de dados | PostgreSQL gerenciado (Supabase ou Railway) |

---

## Módulos do Backend — Responsabilidades

### `pose/`

Extrai os 33 landmarks corporais usando MediaPipe Pose. Recebe uma imagem
processada (segmentada ou original) e retorna coordenadas normalizadas com
score de visibilidade por ponto. Não conhece unidades físicas — opera em
espaço de pixel normalizado.

### `segmentation/`

Isola o corpo humano do fundo usando SAM. Recebe a imagem original e os
landmarks como prompt de segmentação. Retorna a imagem com fundo removido.
Módulo opcional — o pipeline funciona sem ele com degradação de precisão.

### `calibration/`

Converte coordenadas de landmarks normalizados para centímetros reais.
Usa a altura informada pelo usuário como referência de escala. É o único
módulo que conhece a relação pixel/cm — todos os outros operam nos
outputs dele.

### `measurements/`

Calcula medidas antropométricas a partir dos landmarks calibrados:
circunferências (cintura, quadril, pescoço, braço), comprimentos de
membros e razões entre segmentos. Retorna sempre valores com unidade
e estimativa de incerteza.

### `estimation/`

Aplica equações científicas validadas sobre as medidas antropométricas
para estimar composição corporal. Retorna sempre intervalos de confiança,
nunca valores pontuais isolados. Contém as implementações das equações
de referência e, futuramente, o modelo de regressão treinado.

---

## Schemas Pydantic — Estrutura Central

### Input

```python
class PoseCapture(str, Enum):
    FRONT = "front"
    LATERAL = "lateral"
    DORSAL = "dorsal"
 
class BiologicalSex(str, Enum):
    MALE = "male"
    FEMALE = "female"
 
class AnalysisRequest(BaseModel):
    images: dict[PoseCapture, bytes]   # mínimo: FRONT + LATERAL
    height_cm: float
    weight_kg: float
    age: int
    sex: BiologicalSex
 
    @property
    def has_dorsal(self) -> bool:
        return PoseCapture.DORSAL in self.images
```

### Output

```python
class Estimate(BaseModel):
    """Estimativa com intervalo de confiança de 95%."""
    value: float
    lower_bound: float
    upper_bound: float
    method: str
    confidence: Literal["high", "medium", "low"]
    notes: list[str] = []
 
class BodyMetrics(BaseModel):
    body_fat_percentage: Estimate
    lean_mass_kg: Estimate
    fat_mass_kg: Estimate
    bri: Estimate           # Body Roundness Index
    absi: Estimate          # A Body Shape Index
    waist_to_height_ratio: Estimate
    waist_to_hip_ratio: Estimate
 
class Measurement(BaseModel):
    """Medida física com incerteza (ADR-003)."""
    value: float
    uncertainty: float  # desvio padrão em cm
    unit: str = "cm"
 
class AnthropometricMeasurements(BaseModel):
    waist: Measurement
    hip: Measurement
    neck: Measurement
    arm: Measurement
    height: Measurement
 
class AnalysisResult(BaseModel):
    analysis_id: str
    user_id: str | None     # None para análises anônimas
    timestamp: datetime
    measurements: AnthropometricMeasurements
    metrics: BodyMetrics
    poses_used: list[PoseCapture]
    disclaimer: str = (
        "Esta análise é uma estimativa baseada em visão computacional "
        "e não substitui avaliação profissional de saúde."
    )
```

---

## Base Científica

### Métricas Primárias (substituem IMC)

#### Body Roundness Index — BRI (Thomas et al., 2013)

Usa cintura e altura. Superior ao IMC na predição de gordura visceral.

```
BRI = 364.2 − 365.5 × √(1 − ((cintura / 2π)² / (0.5 × altura)²))
```

Referência: Thomas DM et al. *A novel body shape index and body roundness index*,
Obesity, 2013.

#### A Body Shape Index — ABSI (Krakauer & Krakauer, 2012)

Isola o efeito da cintura, controlando peso e altura. Preditor de mortalidade.

```
ABSI = circunferência_cintura / (IMC^(2/3) × altura^(1/2))
```

Referência: Krakauer NY, Krakauer JC. *A new body shape index predicts mortality
hazard independently of body mass index*, PLOS ONE, 2012.

#### Waist-to-Height Ratio — WHtR

Simples e robusto. WHtR > 0.5 indica risco cardiometabólico elevado.

```
WHtR = circunferência_cintura (cm) / altura (cm)
```

Referência: Ashwell M et al. *Waist-to-height ratio is a better screening
tool than waist circumference and BMI*, Obesity Reviews, 2012.

#### Razão Cintura-Quadril — RCQ (WHO, 2008)

```
RCQ = circunferência_cintura (cm) / circunferência_quadril (cm)
```

### Percentual de Gordura — Equações de Referência

#### Equação de Deurenberg (1991) — Baseline

Validada para adultos. Usa IMC (calculado a partir de peso e altura informados).

```
%Gordura = (1.20 × IMC) + (0.23 × idade) − (10.8 × sexo) − 5.4
```

Sexo: 1 para homens, 0 para mulheres. Erro ±3.6%.

Referência: Deurenberg P et al. *Body mass index as a measure of body fatness:
age and sex-specific prediction formulas*, British Journal of Nutrition, 1991.

#### Navy Method (Hodgdon & Beckett, 1984) — Prioritário na Fase 1

Baseado em circunferências. Mais adequado para inputs de visão computacional.

**Homens:**

```
%Gordura = 495 / (1.0324 − 0.19077 × log10(cintura − pescoço) + 0.15456 × log10(altura)) − 450
```

**Mulheres:**

```
%Gordura = 495 / (1.29579 − 0.35004 × log10(cintura + quadril − pescoço) + 0.22100 × log10(altura)) − 450
```

Referência: Hodgdon JA, Beckett MB. *Prediction of percent body fat for US
Navy men and women*, Naval Health Research Center, 1984.

### Validação Científica da Abordagem por Imagem

Estudos recentes validam a estimativa de composição corporal por foto 2D:

- Majmudar et al. (2022) — CNN com fotos de smartphone vs DXA: MAE 2.16 ± 1.54%,
  CCC 0.94 (*npj Digital Medicine*).
- Alves et al. (2025) — AI-2D photo em 1273 adultos: CCC 0.96–0.98 vs DXA,
  superando bioimpedância (*npj Digital Medicine*).

---

## Padrões de Código

### Geral

- Tipagem estática em todas as funções e métodos
- Docstrings no padrão Google Style em toda função pública
- Máximo 80 caracteres por linha
- Funções com responsabilidade única
- Sem comentários óbvios — o código deve se explicar
- Todo output de estimativa deve incluir intervalo de confiança — nunca valor pontual isolado

### Exemplo de padrão esperado

```python
def calculate_navy_body_fat(
    waist_cm: float,
    neck_cm: float,
    height_cm: float,
    sex: BiologicalSex,
    hip_cm: float | None = None,
) -> Estimate:
    """Estima percentual de gordura pelo método da Marinha dos EUA.
 
    Args:
        waist_cm: Circunferência da cintura em centímetros.
        neck_cm: Circunferência do pescoço em centímetros.
        height_cm: Altura em centímetros.
        sex: Sexo biológico do indivíduo.
        hip_cm: Circunferência do quadril em centímetros.
            Obrigatório para sexo feminino.
 
    Returns:
        Estimate com valor central e intervalo de confiança de 95%.
 
    Raises:
        ValueError: Se medidas inválidas ou hip_cm ausente para mulheres.
 
    References:
        Hodgdon JA, Beckett MB. Prediction of percent body fat for US
        Navy men and women. Naval Health Research Center, 1984.
    """
    if sex == BiologicalSex.FEMALE and hip_cm is None:
        raise ValueError("hip_cm is required for female sex.")
 
    # cálculo...
 
    return Estimate(
        value=body_fat,
        lower_bound=body_fat - 3.5,
        upper_bound=body_fat + 3.5,
        method="navy",
        confidence="medium",
    )
```

### Imports

Ordenados em três blocos separados por linha em branco:

1. Biblioteca padrão
2. Bibliotecas de terceiros
3. Módulos internos do projeto

---

## Banco de Dados

### Tabelas Principais

```
users
  id            UUID PK
  email         VARCHAR UNIQUE NOT NULL
  password_hash VARCHAR NOT NULL
  created_at    TIMESTAMPTZ DEFAULT now()
 
analyses
  id            UUID PK
  user_id       UUID FK → users.id (nullable — análises anônimas)
  created_at    TIMESTAMPTZ DEFAULT now()
  poses_used    VARCHAR[]
  height_cm     FLOAT
  weight_kg     FLOAT
  age           INTEGER
  sex           VARCHAR
  measurements  JSONB
  metrics       JSONB
```

Nota: `measurements` e `metrics` armazenados como JSONB permitem
evolução do schema sem migrações frequentes nas fases iniciais.

---

## Autenticação

- JWT stateless (access token + refresh token)
- Access token: 30 minutos
- Refresh token: 7 dias, rotacionado a cada uso
- Dependência `get_current_user` injetável em rotas protegidas
- Rotas públicas: `POST /auth/register`, `POST /auth/login`, `POST /analyze` (análise anônima)
- Rotas protegidas: `GET /history`, `GET /analyses/{id}`

---

## Convenções de Commit

Padrão: `tipo(escopo): descrição em inglês, imperativo, sem ponto final`

Tipos aceitos:

- `feat` — nova funcionalidade
- `fix` — correção de bug
- `docs` — documentação
- `refactor` — refatoração sem mudança de comportamento
- `test` — adição ou correção de testes
- `chore` — configuração, dependências, tooling

Exemplos:

```
feat(pose): add mediapipe landmark extraction
feat(calibration): implement pixel-to-cm conversion via height reference
feat(estimation): add navy method with confidence interval
docs(teoria): add BRI and ABSI reference equations
refactor(measurements): extract circumference calculation to helper
test(estimation): add unit tests for navy method edge cases
chore: configure ruff and black in pyproject.toml
```

---

## Roadmap de Desenvolvimento

### Fase 1 — Fundação (atual)

- [x] Repositórios criados (`fittrack-api`, `fittrack-web`)
- [x] `pyproject.toml` com dependências e configuração de ferramentas
- [x] Schemas Pydantic centrais (`AnalysisInput`, `AnalysisResult`, `Estimate`, `Measurement`)
- [x] Módulo de autenticação — esqueleto funcional (register, login, refresh, JWT)
- [x] Banco de dados — PostgreSQL + SQLAlchemy async (tabelas `users`, `analyses`)
- [x] Módulo `calibration` — conversão pixel → cm via altura (stub funcional)
- [x] Módulo `pose` — extração de landmarks (stub com dados realistas)
- [x] Módulo `measurements` — circunferências e razões antropométricas (stub funcional)
- [x] Módulo `estimation` — Navy Method + Deurenberg + BRI + ABSI + WHtR + RCQ (completo)
- [x] Endpoints REST: `POST /analyze`, `POST /auth/register`, `POST /auth/login`
- [x] Alembic — migrações do banco de dados
- [ ] Documentação teórica paralela em `docs/teoria/`

### Fase 2 — Refinamento

- [ ] Módulo `segmentation` com SAM
- [ ] Suporte completo à 3ª pose (dorsal) — fusão de medidas
- [ ] Modelo de regressão treinado (datasets públicos: NHANES, outros)
- [ ] Validação das estimativas vs DXA em datasets públicos
- [ ] Endpoint `GET /history` e `GET /analyses/{id}`
- [ ] Testes de integração
- [ ] Rate limiting

### Fase 3 — Interface

- [ ] Landing page pública (Nuxt 3 — SSR)
- [ ] Fluxo de upload com instrução de pose ao usuário
- [ ] Visualização dos landmarks e medidas sobre a imagem
- [ ] Dashboard longitudinal de acompanhamento
- [ ] Deploy completo (API + frontend + banco)

---

## Ambiente de Desenvolvimento

- OS: Arch Linux
- IDE: Antigravity
- Gerenciador de pacotes: uv (preferido por velocidade) + pyproject.toml

---

## Sessões de Desenvolvimento

Ao final de cada sessão:

1. Atualizar este arquivo com decisões tomadas e progresso
2. Gerar commit com todas as mudanças da sessão
3. O commit final da sessão sempre inclui `docs: update CLAUDE.md`

### 31/03/2026 - Configuração do Alembic
- Alembic configurado com engine async
- `alembic.ini` na raiz, `script_location = app/db/migrations`
- `env.py` lê `settings.database_url`, importa Base e todos os modelos ORM
- Migração inicial criada manualmente: tabelas `users` e `analyses`
- Fase 1 concluída

---

## Decisões Arquiteturais Registradas

### ADR-001 — Separação de repositórios (api / web)

**Decisão:** dois repositórios independentes com deploy separado.
**Motivo:** deploys independentes, escalabilidade separada, padrão da indústria.
**Alternativa descartada:** monorepo ou FastAPI servindo o build do Vue.

### ADR-002 — IMC substituído por BRI / ABSI / WHtR

**Decisão:** IMC não é métrica primária. BRI, ABSI e WHtR são apresentados
em conjunto como métricas principais.
**Motivo:** IMC não distingue massa magra de gordura; as três métricas
são complementares e mais robustas clinicamente.
**Alternativa descartada:** manter IMC como métrica central.

### ADR-003 — Intervalo de confiança obrigatório em toda estimativa

**Decisão:** nenhum valor de composição corporal é retornado sem `lower_bound`
e `upper_bound`. O tipo `Estimate` é obrigatório.
**Motivo:** estimativas pontuais sem incerteza são cientificamente incorretas
e podem induzir decisões de saúde equivocadas.

### ADR-004 — Suporte nativo a 2 ou 3 poses desde o início

**Decisão:** `AnalysisRequest.images` é um dict com chave `PoseCapture`.
O sistema aceita FRONT + LATERAL (mínimo) ou adiciona DORSAL.
**Motivo:** evita refatoração quando a 3ª pose for habilitada.
A 3ª pose será feature de Fase 2, mas o contrato da API já a suporta.

### ADR-005 — Autenticação desde a Fase 1 (esqueleto funcional)

**Decisão:** JWT + tabela `users` + PostgreSQL implementados na Fase 1,
mesmo que o dashboard longitudinal seja Fase 3.
**Motivo:** adicionar auth depois exige mudança de assinatura de endpoints
e refatoração de schemas. Custo zero de refatoração se feito agora.

### ADR-006 — Navy Method como equação prioritária na Fase 1

**Decisão:** Navy Method é a equação principal para `body_fat_percentage`.
Deurenberg é calculado em paralelo como baseline de comparação.
**Motivo:** Navy Method usa circunferências diretamente — input natural
de visão computacional. Deurenberg usa IMC e depende de peso informado.

### ADR-007 — Separação entre schema HTTP e schema de domínio

**Decisão:** o endpoint `POST /analyze` recebe `UploadFile` + `Form` fields
(camada HTTP). Internamente, constrói-se `AnalysisInput` com imagens como
`np.ndarray` (camada de domínio). `AnalysisRequest` do design original vira
schema interno, não schema de API.
**Motivo:** `bytes` em Pydantic/JSON não funciona para imagens. Multipart é
o padrão HTTP para upload de arquivos. Separar camadas evita acoplamento.

### ADR-008 — Intervalo de confiança: SEE publicado na Fase 1

**Decisão:** Fase 1 usa Standard Error of Estimate (SEE) publicado como proxy
para intervalos de confiança (±3.5% Navy, ±3.6% Deurenberg). Propagação de
incerteza em cadeia (landmark → calibração → medida → equação) é Fase 2.
**Motivo:** propagação completa exige dados reais de landmarks para validar.
A arquitetura já suporta evolução sem refatoração — campos `uncertainty` em
`Measurement` e `lower_bound`/`upper_bound` em `Estimate` estão presentes.
**Alternativa adiada:** propagação Gaussiana completa quando houver dados.

### ADR-009 — Migração inicial criada manualmente

**Decisão:** a migração inicial foi criada via `alembic revision` + conteúdo manual baseado nos modelos ORM, sem `--autogenerate`.
**Motivo:** `--autogenerate` requer conexão ativa com o banco. Em ambiente de desenvolvimento sem PostgreSQL rodando, a migração manual é equivalente e garante rastreabilidade no git.
**Consequência:** ao rodar `alembic upgrade head` pela primeira vez em ambiente com banco disponível, validar que as tabelas criadas batem com os modelos ORM.
