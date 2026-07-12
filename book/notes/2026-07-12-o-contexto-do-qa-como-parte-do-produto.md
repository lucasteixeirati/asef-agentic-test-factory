# Nota contemporânea — O contexto do QA como parte do produto

- **Data:** 2026-07-12
- **Origem:** percepção do autor durante a preparação para publicação
- **Estado:** matéria-prima editorial

## A mudança de perspectiva

Ao revisar as skills futuras — web, backend, mobile, unitários, mutation e performance — o autor identificou que saber executar uma técnica não basta. A fábrica precisa conhecer o contexto profissional no qual a técnica será aplicada: quem é o QA, quais sistemas acompanha, quais repositórios existem, quais fluxos são críticos e quais limites a equipe impõe.

Essa percepção amplia o projeto. A unidade central deixa de ser apenas “um agente que gera testes” e passa a ser uma execução de Quality Engineering contextualizada. Skills, MCPs e LLMs são capacidades disponíveis; o contexto validado e a decisão humana determinam quais delas fazem sentido.

## Experiência profissional como requisito

O ponto não surgiu de uma limitação de framework. Surgiu da experiência do autor com equipes reais de tecnologia. Duas pessoas podem solicitar “crie testes de API” e precisar de soluções completamente diferentes devido a criticidade, arquitetura, compliance, maturidade da suíte, ambientes e responsabilidades.

Esse é um exemplo de conhecimento tácito de QA transformado em arquitetura explícita. Em vez de guardar tudo na cabeça do especialista ou em um prompt longo, o projeto passou a planejar documentos versionados sobre QA, equipe, sistemas, repositórios, skills, MCPs e política de modelos.

## Novo risco

Mais contexto também cria risco. Documentos podem acumular secrets, dados pessoais, URLs privadas ou permissões excessivas. O primeiro contrato passou a rejeitar secrets literais, validar referências e separar leitura de escrita. O objetivo não é coletar o máximo de informação, mas fornecer o mínimo contexto necessário para uma decisão de qualidade explicável.

## Tese para acompanhar

Uma fábrica de testes agêntica robusta talvez dependa menos da quantidade de agentes e mais da qualidade do contexto, das fronteiras de autorização e das evidências que conectam uma decisão ao ambiente real da equipe.
