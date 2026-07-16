# Caracterização de filesystem para cleanup — 5.7.1

- **Data:** 2026-07-16
- **Host observado:** Windows 11
- **Python:** 3.13.5
- **Natureza:** caracterização local; não habilita deleção

## Resultado observado

| Primitive | Resultado |
|---|---|
| `Path.is_junction()` | disponível |
| `shutil.rmtree.avoids_symlink_attacks` | falso |
| remoção por `dir_fd` | indisponível |
| `stat` sem seguir symlink | disponível |
| criação de symlink pelo teste sem elevação | indisponível no processo atual |
| criação de junction controlada | disponível |
| inspeção da junction | classificada como `JUNCTION` antes de qualquer remoção |
| apply recursivo anunciado | não |

O perfil resultante é `RECURSIVE_APPLY_DRY_RUN_ONLY`. A presença de `Path.is_junction()` e o comportamento documentado de `rmtree()` em Windows não são suficientes, isoladamente, para provar resistência a troca de target ou ataque por link durante uma remoção recursiva.

## Decisão

- a fatia 5.7.1 implementa apenas inspeção e contratos;
- nenhum arquivo ou diretório é removido pela nova capability;
- o futuro `asef cleanup` permanece dry-run neste perfil até uma estratégia adicional ser implementada e testada;
- symlink, junction, root `.asef`, target externo, arquivo e target ausente são inelegíveis para remoção;
- a caracterização Linux deverá ocorrer na CI antes de qualquer alegação cross-platform.

Uma prova exploratória de revisão criou uma junction dentro de `.asef`, apontando para outro diretório controlado da mesma fixture. A inspeção retornou `JUNCTION`; o target permaneceu existente e inalterado. A fixture foi removida por paths literais após a verificação. Isso prova a detecção local, não a segurança de uma remoção recursiva.

## Limitações

O teste real de symlink foi ignorado porque o processo Windows atual não possui privilégio para criar a fixture. Isso não é contabilizado como prova de segurança. A detecção real de junction no Windows foi observada, mas SEC-004 continuará aberto até integrar essa prova ao runner e comprovar symlink no Linux.

## Atualização da 5.7.5

`asef cleanup` foi implementado preservando `RECURSIVE_APPLY_DRY_RUN_ONLY` neste host. Dry-run inspeciona diretórios e calcula identity/bytes; `--apply` retorna `RECURSIVE_APPLY_UNSUPPORTED` para diretórios, sem remoção. Isso é comportamento seguro e intencional, não capability ausente mascarada.

Arquivos regulares, como backups de log, podem ser removidos após fingerprint completo e revalidação imediata. Containers exigem label `com.asef.managed=true`, criação anterior ao cutoff, ID completo, nova inspeção e remoção por ID exato.

Testes controlados provaram a lógica recursiva com perfil injetado, mudança de identity entre plano/apply, link preservando target externo e overlap run/quality. A alegação real de apply recursivo permanece bloqueada até execução Linux com as primitivas caracterizadas na 5.7.6.

## Prova Linux da 5.7.6

A imagem Python fixada por digest executou os testes em Linux com repositório read-only, rede `none`, capabilities removidas, `no-new-privileges`, limites de CPU/memória/PIDs e `/tmp` efêmero. `characterize_filesystem_safety()` publicou suporte recursivo verdadeiro; uma suite antiga controlada foi removida por apply e um symlink equivalente foi ignorado com preservação integral do target externo.

Essa prova vale para o runtime Linux observado na imagem pinada. Ela não transforma o perfil Windows em suportado para apply recursivo.
