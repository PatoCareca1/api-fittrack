# FitTrack

> Análise de composição corporal por visão computacional.

FitTrack estima métricas corporais como percentual de gordura, razão
cintura-quadril e distribuição de massa a partir de imagens, utilizando
visão computacional e equações antropométricas validadas na literatura científica.

---

## Como funciona

1. O usuário envia uma imagem (frente e/ou lateral)
2. O sistema extrai landmarks corporais via estimativa de pose
3. A silhueta é segmentada para cálculo de medidas
4. Medidas antropométricas são calculadas a partir dos landmarks
5. Equações científicas estimam a composição corporal
6. O resultado é retornado com as métricas e suas referências científicas

---

## Base Científica

As estimativas são fundamentadas em equações validadas na literatura:

- Deurenberg et al. (1991) — estimativa de percentual de gordura via IMC
- Jackson e Pollock (1978) — estimativa de densidade corporal
- WHO (2008) — classificação por razão cintura-quadril

O projeto não substitui avaliações clínicas. As estimativas têm caráter
informativo e educacional.

---

## Stack

- Python 3.11+
- FastAPI
- MediaPipe
- OpenCV
- SAM (Segment Anything Model)
- PyTorch

---

## Estrutura do Projeto

    fittrack/
    ├── app/
    │   ├── api/
    │   ├── core/
    │   ├── modules/
    │   │   ├── pose/
    │   │   ├── segmentation/
    │   │   ├── measurements/
    │   │   └── estimation/
    │   └── main.py
    ├── docs/
    │   ├── teoria/
    │   └── decisoes/
    ├── tests/
    ├── notebooks/
    └── pyproject.toml

---

## Documentação

A documentação teórica de cada módulo está em docs/teoria/.
As decisões arquiteturais estão registradas em docs/decisoes/.

---

## Status

Em desenvolvimento ativo — Fase 1 (API Core)

---

## Autor

Lucas — Cientista da Computação em formação, desenvolvedor backend.
