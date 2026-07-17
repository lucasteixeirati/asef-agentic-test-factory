# Relato — planejamento do incremento 5.9

- **Data:** 2026-07-17
- **Estado:** plano aprovado; fatia 5.9.1 autorizada e concluída localmente
- **Dependência:** 5.8 concluído e publicado em `v0.1.0a6`

O levantamento confirmou que o 5.9 deve fechar evidências, não criar uma nova frente funcional. G5-19 é o único critério explicitamente parcial; os demais precisam ser revalidados e consolidados em pacote próprio. O walkthrough frio do 5.8 não substitui a sessão de um QE externo real.

O desenho adotou seis fatias e separou preflight, avaliação externa, remediação, retrospectiva e decisão. Participante ausente produz bloqueio; IA ou mantenedor não podem simular a evidência. Consentimento, anonimização e coleta mínima entram no contrato antes da sessão.

A inspeção também encontrou frases desatualizadas no quickstart e na matriz canônica de suporte, que ainda tratavam `v0.1.0a5` como última release. A reconciliação editorial acompanha este planejamento, e a primeira fatia deverá adicionar uma proteção automatizada contra nova divergência.

Uma `0.1.0a7` não é resultado obrigatório. Ela só será proposta se finding externo exigir alteração material no package ou nas instruções da jornada. CI, participante e parecer técnico não aprovam o Gate; a decisão final permanece com Lucas e autoriza, no máximo, planejar a Etapa 6.
