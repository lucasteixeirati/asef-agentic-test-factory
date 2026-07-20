# Mapa de fontes do livro

Este mapa evita reconstrução retrospectiva e não transforma o índice provisório em obrigação arquitetural.

| Capítulo provisório | Fontes já disponíveis | Maturidade |
|---|---|---|
| 1. Por que um engenheiro de qualidade decidiu construir com IA | Marco Zero; nota de concepção; relato dos 15 anos em QA | base narrativa |
| 2. Determinismo, probabilidade e confiança | ADR-001; estratégia de avaliação; structured output | evidência parcial |
| 3. O marco zero e a fábrica de software | `concepcao/`; timeline; journal do Marco Zero | forte |
| 4. O reposicionamento como fábrica de testes | nota de concepção; visão e escopo | forte |
| 5. Conceber com IA sem terceirizar decisões | revisão externa; rejeição da ADR-007; decisões humanas | forte |
| 6. O primeiro workflow e suas restrições | plano da Etapa 4; WF-001; WS-001 a WS-007 | forte |
| 7. Contratos, estado e evidências | contratos 1.1; ADRs; evidence model; observabilidade; `AlphaRunReport 1.0.0`; envelope genérico de capability run e bundle state/manifest da 6.3.2 | forte |
| 8. Segurança para executar código gerado | EXP-002; Docker tests; sandbox policy; Security 12/12; doctor; retention/cleanup; provas Windows/Linux do 5.7; conformance API networkless da 6.3.2; política fail-closed e threat model de DNS rebinding da 6.3.3; threat model, Chromium não-root e controles adversariais da 6.4; Java/Maven offline não-root e source JUnit compilado deterministicamente na 6.5 | forte para fixtures locais; execução contra alvos externos permanece não implementada |
| 9. Como testar componentes não determinísticos | cassettes; structured output; retries; mutation pilot; adapter live e budget real do 5.4; geração API live contabilizada e OpenAPI delimitador da 6.3.3; coverage/mutation do SUT no 5.6; fingerprints e repetição Web UI da 6.4.5 | forte para providers e fixtures limitados |
| 10. Experimentos com modelos, prompts e frameworks | EXP-001 a EXP-006; Lesson 001 | forte |
| 11. A primeira execução por outra pessoa | instalação limpa e walkthrough frio do 5.8; protocolo externo `1.0.1`; `v0.1.0a7` e postflight; sessão interna I01 assistida; experiência Web UI instalada fora do checkout na 6.4.6; QE externo ainda ausente | autovalidação técnica documentada; capítulo permanece incompleto até uso externo real |
| 12. Falhas, retrabalho e decisões revertidas | journals das Etapas 3 e 4; ADR-007; auditoria do wheel; sete findings do 5.3; hardening de contexto e budget do 5.4; corrida pós-click de popup na 6.4.5; pin Surefire ainda não publicado e ordem não determinística do XML descobertos na 6.5 | forte |
| 13. Evolução baseada em evidências | ADR-004, ADR-007, ADR-008, ADR-009; checkpoints; revisões 5.3/5.4; Smoke 20/20; quality capabilities; reports; avaliação I01; envelope de run compartilhado por API, Web UI e Java; conformance Web UI 18/18, Java repetida e unit TypeScript/TAP acrescentado pelo Gate 6 | forte até a candidata Gate 6; independência externa pendente |
| 14. Open source e comunidade | publicação GitHub; contribuição, adapter guide, código de conduta, templates e experiência pública do 5.8; feedback comunitário ainda ausente | base pública pronta; participação externa pendente |
| 15. Impacto da IA na velocidade e qualidade | baseline do Dia 2; atualização do Dia 3; nota do Dia 6; retrospectiva Etapa 5; nota do Dia 9 com aproximadamente 39 horas, interações menos frequentes e mais longas, confiança e retomada após desligamento | forte como relato contemporâneo; não é telemetria controlada |
| 16. O que eu faria diferente | Lesson 002; Lesson 003; retrospectivas; nota do Dia 9: planejamento detalhado primeiro e maior autonomia da IA dentro de objetivo, aceite e regras explícitas | voz autoral disponível; síntese de capítulo ainda ausente |

## Lacunas atuais

- experiência de um usuário externo real, quando ocorrer;
- percepção após as futuras automações úteis de Web, API, `.bat`, Java e Kotlin;
- contagem de interações após o Dia 5, deliberadamente não tratada como telemetria;
- transformação das fontes em rascunhos efetivos dos 16 capítulos.
