# Etapa 6.5 — Java/JUnit como prova da arquitetura

A terceira experiência do dia mostrou por que uma base sólida acelera sem eliminar
descobertas. Contratos, run envelope, checkpoint, Docker e evidência neutra puderam
ser reutilizados; Java, Maven, compilação e Surefire ficaram nos adapters da
capability. O core não recebeu branches de ecossistema.

Duas diferenças práticas exigiram correção. A documentação já mostrava uma linha
3.6.0 do Surefire, mas o release estável verificável no Maven Central era 3.5.5; a
imagem passou a usar o artifact publicado. Depois, a conformance revelou que JUnit
não garante a ordem textual dos métodos no XML. A reconciliação correta é por
conjunto único de identidades, não por posição, sem aceitar ausência ou duplicação.

A experiência instalada repetiu o aprendizado da Web UI: uma execução que depende
de `examples/` funciona no checkout e falha no wheel. A fixture Calculator foi
empacotada e comparada byte a byte com a versão pública antes da validação instalada.

O resultado é uma candidata Java pequena e honesta: intenção gravada, plano
revisável, JUnit determinístico, Maven offline, Surefire nativo e fingerprints
estáveis. Ela ainda não é suporte Java geral e não antecipa a validação humana do
Gate 6.
