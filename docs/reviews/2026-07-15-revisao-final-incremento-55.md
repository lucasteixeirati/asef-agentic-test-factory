# Revisão final — incremento 5.5

- **Data:** 2026-07-15
- **Escopo:** Smoke Dataset executável, determinístico e keyless
- **Parecer final:** aprovado
- **CI:** run `29442732993`, quatro jobs verdes

## Resultado

Os dez casos `SMK-001` a `SMK-010` foram materializados, validados antes da primeira run e executados pelo comando público `asef smoke`. Duas repetições no Docker real produziram 20 matches, zero mismatch e zero runner error. Encerramentos esperados como espera humana, suspeita de defeito, budget, infraestrutura e policy contam como matches somente quando todos os fatos tipados coincidem.

O dataset efetivo teve SHA-256 `c37834768ad1d2e457e30197a86766f631a49a5441e1ca1a02c7171c1e38019d`. O fingerprint de cada caso permaneceu igual entre as duas repetições. Run IDs, timestamps, duração, paths absolutos, stdout bruto e identidade local da imagem não participam dessa comparação.

## Findings e correções

1. O SMK-006 inicialmente planejado como sintaxe inválida não alcançaria o Docker. A fixture final usa import inexistente sintaticamente válido, produz `TEST_ERROR`, consome uma correção e passa sem relaxar a policy.
2. A primeira suíte real encontrou nomes temporários longos demais para o Windows. Eles foram encurtados mantendo escrita atômica, paths finais e IDs públicos; regressões do store e execuções posteriores passaram.
3. O hash efetivo precisava cobrir todos os arquivos autorizados pelo contexto, não somente os refs declarados diretamente nos casos. O loader agora resolve o contexto, valida vínculo com o SUT e inclui todo o `read_scope`; uma regressão prova que alterar uma fonte adicional muda o hash.
4. A publicação de reports sob `.asef` exige habilitar arquivos ocultos no upload da CI. O job faz secret scan antes do upload, exige arquivos presentes e publica somente `suite.json` e `suite.md` por sete dias.

## Evidências locais

- core: 221 testes descobertos, 197 executados e 24 opcionais ignorados;
- branch coverage global: 85%;
- Docker: 15 descobertos, 14 aprovados e um skip conhecido de symlink por privilégio do Windows;
- Smoke Docker: 10/10 e 20/20 keyless;
- wheel `0.1.0a3`: build isolado, instalação em target limpo e Smoke 10/10;
- secret scan: source, wheel e evidências aprovados;
- `git diff --check`: aprovado.

## Limitações preservadas

O dataset é público, curado, pequeno e não estatístico. Ele mede conformidade com dez expectativas versionadas e não compara modelos, não cria ranking e não sustenta alegação de benchmark. Coverage/mutation permanecem no 5.6; Security Dataset e retenção no 5.7; consolidação da experiência no 5.8.

## Parecer

Não há finding aberto no incremento. O commit funcional `06cc892` foi publicado e os jobs públicos `core`, `framework-spikes`, `docker-security` e `alpha-smoke` aprovaram a CI `29442732993`. O incremento 5.5 está concluído. O Gate 5 continua aberto porque os incrementos 5.6 a 5.9 e os demais critérios ainda não foram encerrados.
