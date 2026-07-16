# Relato — Planejamento do incremento 5.7

- **Data:** 2026-07-15
- **Estado:** plano detalhado proposto; implementação não iniciada
- **Dependência:** `v0.1.0a4` publicada com os incrementos 5.5 e 5.6

O planejamento do 5.7 começou pela constatação de que segurança já está espalhada pelo produto, mas ainda não existe como uma capability verificável de ponta a ponta. A matriz Docker possui testes reais de rede, filesystem, identidade, memória, PIDs, timeout, traversal e truncamento. A skill unitária bloqueia imports e artifacts fora do contrato. Logs rotacionam, evidências são escaneadas e a CI usa retenção curta. Mesmo assim, o catálogo `SEC-001` a `SEC-012` ainda é apenas uma especificação.

A primeira decisão foi não transformar o Security Dataset em um executor genérico de payloads. Manifests não poderão fornecer shell, imagem, mount ou argv livre. Cada caso selecionará um executor interno e revisado. Isso mantém o dataset como dado e evita criar, em nome dos testes de segurança, uma nova superfície de execução arbitrária.

A segunda decisão foi limitar a alegação de SEC-010. Um teste determinístico não prova que um modelo é universalmente resistente a prompt injection. O que o ASEF pode provar é que comentários do SUT não recebem autoridade: provider não controla tools, budgets, paths ou transições, e outputs fora do contrato são rejeitados pelo host.

O `asef doctor` também foi desenhado como diagnóstico, não reparo. Ele distinguirá CLI Docker ausente, daemon parado, imagem não construída, engine incorreta, output root inválida, contexto inválido e requisito live ausente. Não fará pull, build, login, provider call ou leitura do arquivo de configuração Docker; somente facts allowlisted entrarão no report.

Retenção foi o ponto com maior risco de desenho. Deleção automática seria prematura para uma ferramenta experimental e poderia destruir a própria evidência usada em auditoria. O plano mantém evidências finais até ação explícita e propõe `asef cleanup` em dry-run por padrão. Apply exige selector, idade e flag explícita. Symlink, junction, TOCTOU, manifest inválido e arquivo bloqueado devem falhar seguros e produzir tombstone, nunca sucesso silencioso.

O inventário encontrou um débito concreto: vários cleanups de workspace usam `ignore_errors=True`. Isso protege o caminho funcional de uma exceção secundária, mas esconde resíduo potencialmente sensível. O 5.7 deverá tornar cleanup uma observation tipada e verificável. Falha de remoção não será chamada de sucesso.

O plano foi dividido em seis fatias: contratos/policy, dataset/runner, hardening Docker, doctor, retention/cleanup/debug e CI/revisão. G5-11, G5-15 e G5-16 permanecem abertos ou parciais até a execução. Nenhuma implementação, versão, tag ou release foi autorizada por este planejamento.
