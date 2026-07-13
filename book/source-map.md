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
| 7. Contratos, estado e evidências | contratos 1.1; ADRs; evidence model; observabilidade | forte |
| 8. Segurança para executar código gerado | EXP-002; Docker tests; sandbox policy | forte para baseline |
| 9. Como testar componentes não determinísticos | cassettes; structured output; retries; mutation pilot | parcial |
| 10. Experimentos com modelos, prompts e frameworks | EXP-001 a EXP-006; Lesson 001 | forte |
| 11. A primeira execução por outra pessoa | instalação limpa automatizada; usuário externo real ainda ausente | incompleta |
| 12. Falhas, retrabalho e decisões revertidas | journals das Etapas 3 e 4; ADR-007; auditoria do wheel | forte |
| 13. Evolução baseada em evidências | ADR-004, ADR-007, ADR-008; checkpoints | parcial |
| 14. Open source e comunidade | publicação GitHub; feedback comunitário ainda ausente | inicial |
| 15. Impacto da IA na velocidade e qualidade | baseline de 10 horas/150 interações; dias por etapa | desatualizada após Dia 2 |
| 16. O que eu faria diferente | lessons e retrospectivas; exige distância temporal | aberta |

## Lacunas que exigem voz do autor

- percepção atual de velocidade após o walking skeleton;
- confiança antes e depois dos testes adversariais;
- reação à falha do wheel fora do checkout;
- custo cognitivo de revisar código e documentação produzidos rapidamente;
- decisões que Lucas considera mais representativas de sua experiência de QA.
