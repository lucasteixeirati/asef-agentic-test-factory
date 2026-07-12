# EXP-006 — Containers multilíngues e overhead do Docker Desktop

- **Data:** 2026-07-12
- **Status:** baseline de executor aprovada
- **Ambiente:** Windows, Docker Desktop/WSL2

## Perguntas

1. Python, Node/TypeScript e Java conseguem iniciar sob a mesma política de container?
2. Qual é o overhead aproximado de criar um container Python efêmero para um comando mínimo?

## Perfis por digest

| Perfil | Imagem | Resultado |
|---|---|---|
| `python-pytest` | `python@sha256:399b...f4b0` | Aprovado |
| `node-typescript` | `node@sha256:16e2...c3e2` | Aprovado |
| `java-junit` | `eclipse-temurin@sha256:1ff7...dc76` | Aprovado |

Todos executaram o comando de versão com 1 CPU, 256 MiB, 64 PIDs, rede desabilitada, usuário não root, rootfs/workspace read-only e timeout de 20 segundos.

## Medição de overhead

Comando mínimo equivalente, após um warm-up, sete amostras intercaladas:

| Métrica | Resultado |
|---|---:|
| Processo Python local — mediana | 39,67 ms |
| Container Python — mediana | 341,65 ms |
| Razão observada | 8,61x |

## Interpretação

O overhead absoluto observado foi de aproximadamente 302 ms para inicialização e descarte de um container mínimo. A razão é alta porque o trabalho medido é quase vazio; em suítes reais, a proporção deverá cair. O resultado favorece agrupar comandos seguros dentro de uma execução controlada quando isso não enfraquecer isolamento ou evidências.

## Limitações

- não é benchmark universal;
- apenas sete amostras em uma máquina;
- containers Node e Java provaram compatibilidade do executor, não toolchains completos;
- builds, testes, coverage e mutation permanecem sem conformance multilíngue;
- limites adequados para workloads Java e Node ainda precisam ser calibrados com projetos representativos.

## Conclusão

O executor e a política comum são portáveis no recorte de inicialização. Os perfis permanecem `baseline`, não “suportados”. A arquitetura pode preparar TypeScript e Java desde já sem antecipar alegações end-to-end.
