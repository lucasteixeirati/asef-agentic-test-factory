# Revisão — publicação e postflight `v0.1.0a7`

- **Data:** 2026-07-18
- **Tag:** `v0.1.0a7`
- **Commit:** `79fbeb0dbbef39799801b86cebd59f8b55edaa0a`
- **Parecer:** `READY` para o checkpoint humano da 5.9.3
- **Gate 5:** pendente

A CI pré-tag `29647693611` aprovou os sete jobs. A tag anotada e a pré-release foram publicadas somente depois desse resultado. Wheel e sdist oficiais foram baixados novamente da página da release e seus tamanhos e hashes coincidiram com os artifacts auditados antes da publicação.

O sdist remoto passou no checker com 128 arquivos e 109 links sem findings. O wheel remoto instalou sem dependências fora do checkout e reportou `0.1.0a7`. A imagem pytest foi reconstruída do sdist publicado. Doctor terminou `DEGRADED/READY` com 12 checks; demo `SUCCEEDED/ACCEPTED`; auditor 9/9; cleanup `DRY_RUN_COMPLETE`; scanner verde; zero containers gerenciados.

`PREFLIGHT-F-001` está resolvido porque a documentação imutável da `v0.1.0a7` identifica corretamente a release e o package. Kit e checklist podem ficar `READY`. Isso não inicia a sessão, não contata participante e não aprova o Gate 5; a 5.9.3 depende de autorização humana explícita.
