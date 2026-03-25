# CLAUDE.md — FitTrack

## Visão Geral do Projeto

FitTrack é um sistema de análise de composição corporal por visão computacional.
A partir de imagens do usuário, o sistema extrai landmarks corporais, calcula
medidas antropométricas e estima métricas de composição corporal como percentual
de gordura, utilizando equações validadas na literatura científica.

O objetivo de longo prazo é evoluir para um sistema completo de acompanhamento
físico, ajudando pessoas a entenderem sua composição corporal e encontrarem
seu físico ideal de forma acessível e não invasiva.

---

## Arquitetura

O projeto segue arquitetura modular e escalável. Cada módulo tem responsabilidade
única e não conhece detalhes internos dos outros. A comunicação entre módulos
se dá por interfaces bem definidas via schemas Pydantic.

    fittrack/
    ├── app/
    │   ├── api/
    │   │   ├── routes/          # Endpoints FastAPI organizados por domínio
    │   │   └── dependencies/    # Dependências injetáveis (auth, db, etc.)
    │   ├── core/
    │   │   ├── config.py        # Configurações via variáveis de ambiente
    │   │   └── exceptions.py    # Exceções customizadas do domínio
    │   ├── modules/
    │   │   ├── pose/            # Extração de landmarks corporais (MediaPipe)
    │   │   ├── segmentation/    # Segmentação e isolamento do corpo (SAM)
    │   │   ├── measurements/    # Cálculo de medidas antropométricas
    │   │   └── estimation/      # Estimativa de composição corporal
    │   ├── models/
    │   │   └── schemas/         # Schemas Pydantic de entrada e saída
    │   └── main.py              # Entrypoint da aplicação
    ├── docs/
    │   ├── teoria/              # Fundamentos científicos de cada módulo
    │   └── decisoes/            # Registro de decisões arquiteturais (ADRs)
    ├── tests/                   # Testes unitários e de integração
    ├── notebooks/               # Experimentação e validação científica
    ├── .env.example
    ├── pyproject.toml
    └── README.md

---

## Stack Tecnológica

- Python 3.11+
- FastAPI — framework da API
- Pydantic v2 — validação e serialização de dados
- MediaPipe — extração de pose e landmarks corporais
- OpenCV — processamento de imagens
- SAM (Segment Anything Model) — segmentação corporal
- PyTorch — modelos de deep learning
- scikit-learn — modelos de regressão e utilitários de ML
- Black — formatação de código
- Ruff — linting
- Pytest — testes

---

## Padrões de Código

### Geral

- Tipagem estática em todas as funções e métodos
- Docstrings no padrão Google Style em toda função pública
- Máximo 80 caracteres por linha
- Funções com responsabilidade única
- Sem comentários óbvios — o código deve se explicar

### Exemplo de padrão esperado

    def calculate_waist_to_hip_ratio(
        waist_circumference: float,
        hip_circumference: float,
    ) -> float:
        """Calcula a razão cintura-quadril (RCQ).

        Args:
            waist_circumference: Circunferência da cintura em centímetros.
            hip_circumference: Circunferência do quadril em centímetros.

        Returns:
            Razão cintura-quadril como valor float.

        Raises:
            ValueError: Se qualquer medida for menor ou igual a zero.

        References:
            WHO (2008). Waist circumference and waist-hip ratio:
            report of a WHO expert consultation.
        """
        if waist_circumference <= 0 or hip_circumference <= 0:
            raise ValueError("Measurements must be greater than zero.")

        return waist_circumference / hip_circumference

### Imports

Ordenados em três blocos separados por linha em branco:

1. Biblioteca padrão
2. Bibliotecas de terceiros
3. Módulos internos do projeto

---

## Convenções de Commit

Padrão: tipo(escopo): descrição em inglês, imperativo, sem ponto final

Tipos aceitos:

- feat — nova funcionalidade
- fix — correção de bug
- docs — documentação
- refactor — refatoração sem mudança de comportamento
- test — adição ou correção de testes
- chore — configuração, dependências, tooling

Exemplos:
    feat(pose): add mediapipe landmark extraction
    docs(teoria): add anthropometric equations reference
    refactor(measurements): extract circumference calculation to helper
    test(estimation): add unit tests for deurenberg equation
    chore: configure ruff and black in pyproject.toml

---

## Base Científica

### Módulo de Estimativa — Equações de Referência

#### Percentual de Gordura — Equação de Deurenberg (1991)

Validada para adultos, utiliza IMC, idade e sexo.

    %Gordura = (1.20 × IMC) + (0.23 × idade) − (10.8 × sexo) − 5.4

Onde sexo = 1 para homens, 0 para mulheres.

Referência: Deurenberg P, Weststrate JA, Seidell JC. Body mass index as a
measure of body fatness: age and sex-specific prediction formulas.
British Journal of Nutrition, 1991.

#### Percentual de Gordura — Jackson e Pollock (1978) adaptado

Originalmente baseado em dobras cutâneas, utilizaremos circunferências
extraídas via visão computacional como proxy.

Referência: Jackson AS, Pollock ML. Generalized equations for predicting
body density of men. British Journal of Nutrition, 1978.

#### Razão Cintura-Quadril (RCQ)

Indicador de distribuição de gordura e risco cardiovascular.

    RCQ = circunferência da cintura (cm) / circunferência do quadril (cm)

Referência: WHO Expert Consultation, 2008.

#### IMC

    IMC = peso (kg) / altura² (m)

---

## Roadmap de Desenvolvimento

### Fase 1 — API Core (atual)

- [ ] Estrutura base do projeto
- [ ] Módulo de pose (extração de landmarks)
- [ ] Módulo de segmentação
- [ ] Módulo de medidas antropométricas
- [ ] Módulo de estimativa (equações)
- [ ] Endpoints REST da API
- [ ] Documentação teórica paralela

### Fase 2 — Refinamento

- [ ] Validação das estimativas com datasets públicos
- [ ] Modelo de regressão treinado com dados antropométricos
- [ ] Testes de integração
- [ ] Autenticação e rate limiting

### Fase 3 — Interface

- [ ] Frontend web
- [ ] Visualização dos landmarks e medidas
- [ ] Dashboard de acompanhamento ao longo do tempo

---

## Ambiente de Desenvolvimento

- OS: Arch Linux
- IDE: Antigravity
- Gerenciador de pacotes: pip + pyproject.toml (ou uv, a definir)

---

## Sessões de Desenvolvimento

Ao final de cada sessão:

1. Atualizar este arquivo com decisões tomadas e progresso
2. Gerar commit com todas as mudanças da sessão
3. O commit final da sessão sempre inclui docs: update CLAUDE.md

---

*Última atualização: Março 2026 — Sessão 01 — Estrutura inicial e fundamentos*
