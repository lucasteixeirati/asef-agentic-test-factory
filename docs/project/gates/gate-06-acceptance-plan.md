# Plano de aceitação do Gate 6

**Estado:** candidata local pronta para uma única validação humana final.

Lucas deve revisar o pacote, confirmar que a jornada e os limites correspondem ao
produto desejado e decidir `APROVAR`, `APROVAR COM CONDIÇÕES` ou `REJEITAR`. Esta
validação não autoriza automaticamente push, tag ou release.

## Checklist humano final

- a jornada natural → plano → revisão → execução → evidência é compreensível;
- API, Web UI e Java usam somente fixtures autorizadas e limites honestos;
- Python unit, TypeScript unit de conformance e Java unit demonstram resultado neutro equivalente;
- skills/agentes não escolhem comandos, rede, dependências ou promoção;
- quality/metamórfico ajudam análise sem virar threshold decorativo;
- lacunas externas continuam visíveis: usuários externos, Kotlin, `.bat` e projetos reais;
- níveis candidatos (`node-typescript`, `java-junit`) só serão promovidos após esta decisão.
