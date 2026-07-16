# Revisão técnica — fatia 5.7.1

- **Data:** 2026-07-16
- **Escopo:** threat model, contratos e política
- **Estado:** aprovada localmente após correção dos findings e validação final

## Escopo revisado

- contratos Security, doctor, retention e cleanup;
- API pública do package;
- fingerprints, counters e hashes derivados;
- contenção e links de filesystem;
- documentação e limites de alegação;
- ausência de implementação antecipada da 5.7.2.

## Findings

### F571-01 — doctor incompleto em relação ao plano

O report expunha apenas `healthy` booleano e checks sem duração/timeout. O plano exige `HEALTHY`, `DEGRADED` e `BLOCKED`, versões do ambiente e timeout por check.

**Correção:** `DoctorAggregateStatus`, duração/timeout, versões ASEF/Python, profile ID e facts allowlisted por check. Qualquer `FAIL` bloqueia; warn/skip degradam.

### F571-02 — fingerprints não reconciliados

Security results e cleanup reports aceitavam qualquer SHA-256 sintaticamente válido. Isso não comprovava estabilidade semântica nem identidade do plano.

**Correção:** fingerprints são recalculados a partir dos fatos sem duração/timestamp. O plan hash usa request, target ref, identidade e bytes estimados; status mutável não entra no digest.

### F571-03 — arrays JSON não estritos

`tuple(value)` poderia aceitar string e transformá-la em caracteres.

**Correção:** parser exige array/lista de strings para fixtures, preconditions e limitations.

### F571-04 — raiz linkada

A inspeção verificava links nos descendentes, mas não rejeitava explicitamente a raiz quando ela própria era symlink/junction.

**Correção:** a raiz linkada é inelegível antes de resolver o target. Uma junction real no Windows foi classificada corretamente e o target permaneceu intacto.

## Observações adicionais

- política de retenção agora congela exatamente 1 MiB + dois backups para logs;
- reports de CI exigem sete dias e sanitização;
- cassette live não pode ser automaticamente publicável;
- debug permanece explícito e sanitizado;
- nenhum executor de remoção, CLI, dataset ou Docker hardening foi adicionado.

## Parecer

Os findings pertenciam à própria 5.7.1 e foram corrigidos sem expandir para a 5.7.2.

Validação final:

- 278 testes descobertos;
- 249 aprovados e 29 opcionais ignorados;
- branch coverage geral de 86,90%;
- `security_contracts.py` com 94,78%;
- prova real de junction Windows aprovada;
- compilação, `git diff --check` e secret scan aprovados.

Parecer: fatia 5.7.1 aprovada localmente. O início da 5.7.2 exige decisão explícita.
