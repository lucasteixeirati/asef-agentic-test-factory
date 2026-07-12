# WF-001 — Modelo de estado compartilhado

## Princípio

O estado armazenará fatos e referências a artefatos, evitando texto formatado ou objetos específicos de frameworks. Cada atualização deverá ser tipada, versionada e atribuída a uma etapa.

## Estrutura conceitual

| Campo | Tipo conceitual | Obrigatório | Descrição |
|---|---|---:|---|
| `schema_version` | string | Sim | Versão do contrato de estado |
| `run_id` | UUID | Sim | Identificador da execução |
| `workflow_id` | string | Sim | `WF-001` |
| `workflow_version` | string | Sim | Versão executada |
| `status` | enum | Sim | Estado atual |
| `created_at` | datetime UTC | Sim | Criação da run |
| `updated_at` | datetime UTC | Sim | Última transição |
| `request` | reference | Sim | Input validado e imutável |
| `sut_manifest` | reference | Após inspeção | Perfil, arquivos e hashes permitidos |
| `requirement_analysis` | reference | Após análise | Comportamentos, restrições e ambiguidades |
| `risk_assessment` | reference | Após risco | Riscos e prioridades |
| `test_design` | reference | Após design | Cenários, oracles e rastreabilidade |
| `test_artifacts` | reference[] | Após geração | Artefatos por tentativa |
| `static_validation` | reference[] | Após validação | Resultados por tentativa |
| `executions` | reference[] | Após execução | Resultados normalizados |
| `evaluation` | reference | Após avaliação | Conclusões e evidências |
| `human_decisions` | reference[] | Opcional | Decisões append-only |
| `attempts` | map | Sim | Contadores por categoria |
| `budgets` | object | Sim | Limites e consumo atual |
| `policy_snapshot` | reference | Sim | Política imutável da run |
| `errors` | reference[] | Opcional | Falhas classificadas |
| `events_cursor` | string | Sim | Último evento consistente |
| `final_report` | reference | Terminal | Relatório Markdown/estruturado |

## Regras

- campos produzidos por uma etapa não serão modificados retroativamente; novas tentativas criam novas versões;
- referências usam hash e localização autorizada;
- nenhum secret é persistido no estado;
- conteúdo volumoso fica em artefatos, não no estado;
- o estado deve ser serializável sem SDK de provider ou framework;
- timestamps usam UTC;
- transições inválidas devem falhar antes de efeitos colaterais;
- estado e eventos precisam permitir reconstruir a sequência da run.

## Controle de concorrência

- atualização requer versão esperada do estado;
- somente uma transição de controle pode ser confirmada por vez;
- tarefas paralelas, quando futuras, gravam resultados separados e são reconciliadas por nó determinístico;
- decisões humanas usam identificador único para impedir reaplicação.

## Checkpoints propostos

Checkpoint após:

- validação do input;
- inspeção do SUT;
- análise do requisito;
- design aprovado;
- geração de cada tentativa;
- validação estática;
- execução;
- decisão humana;
- avaliação;
- relatório final.

O mecanismo concreto de persistência será escolhido nos spikes. O contrato não dependerá dele.

