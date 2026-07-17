# Revisão técnica — fatia 5.8.5

- **Data:** 2026-07-17
- **Estado:** aprovada localmente
- **Escopo:** checker documental, package audit, experiência instalada e job `public-experience`

## Findings corrigidos

1. Links e claims públicos dependiam de inspeção ad hoc. Um checker offline passou a validar documentos, anchors, versão, CLI, paths, placeholders e fontes canônicas com findings tipados.
2. Não existia uma reconciliação instalada única de stdout, state, manifest, report, schema e Markdown. O novo auditor falha fechado e só materializa a superfície publicável depois de nove checks.
3. Doctor exigia a imagem quality no caminho demo, contrariando o plano que constrói somente pytest. Quality agora é opcional (`WARN/DEGRADED` quando ausente); pytest permanece bloqueante.
4. O quickstart não dizia que o wheel não incorpora a imagem Docker. O build local da imagem pytest e a opcionalidade da imagem quality ficaram explícitos.
5. Os seis jobs existentes não cobriam a experiência pública completa. Foi adicionado um sétimo job independente, keyless e sem navegação externa.
6. A primeira captura local adicionou BOM aos JSONs de stdout. O auditor recusou a entrada; a captura foi normalizada para UTF-8 sem BOM e a mesma run passou, preservando strict JSON.

## Evidências

- checker: 117 arquivos, 103 links e zero findings;
- workflow YAML válido: sete jobs, 12 steps no novo job;
- wheel final: `a5f2af5a12e60c4fabb9ea0d78dcc8b51cc699897dfce16451318eefd6d99314`;
- sdist final: `916aa116d11145ebd03e3fcdf49644cace8bfb47d60ace083244625b8a2afbbf`;
- wheel instalado com `--no-deps` em venv/diretório temporários fora do checkout;
- doctor instalado: `DEGRADED/READY` apenas com imagem pytest obrigatória;
- demo instalada: `SUCCEEDED/ACCEPTED`, report schema `1.0.0`;
- auditor final: nove de nove checks aprovados, incluindo schema empacotado e hashes do manifest;
- secret scan verde para scripts, workflow, dist e `.asef` instalada;
- zero containers com label `com.asef.managed=true` após a run;
- 344 testes aprovados, 33 skips opcionais e branch coverage de 85,34%;
- `git diff --check` aprovado.

## Limitações

Os artifacts usam metadata `0.1.0a5` apenas porque a mudança de versão pertence à 5.8.6; eles não substituem os artifacts publicados dessa release. O job foi validado por composição YAML e pelos mesmos passos localmente, mas ainda não foi executado no GitHub Actions. Smoke 20/20, Security 12/12 e quality mantêm as evidências publicadas anteriores e serão reavaliados na revisão/candidata.

## Parecer

A 5.8.5 atende localmente os critérios 29 e 30 e está aprovada. A experiência instalada possui uma prova reproduzível e uma superfície de publicação mínima. A conclusão não autoriza 5.8.6, commit, push, CI, versão, candidata, release ou Gate 5.
