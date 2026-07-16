# Security Dataset executável — 5.7.2

O dataset público contém exatamente `SEC-001` a `SEC-012`. Cada manifest declara identidade, controle, executor enum, fixture, precondições, outcome e limitações. Não declara shell, argv, imagem, mount ou path absoluto.

```text
case.json -> loader estrito -> executor interno -> facts/evidência -> resultado -> suite
```

O loader rejeita fileset extra, duplicate keys, texto inválido, oversize, traversal, symlink/junction e referência não canônica. O hash inclui manifest, cases, READMEs e fixtures.

O runner continua após control failure e só aceita a suite com 12 passes. `UNSUPPORTED` nunca é pass. Reports ficam sob `.asef/security/<suite-id>`.

Os controles Docker reutilizam a política existente: rede none, rootfs read-only, capabilities removidas, usuário não root, limites e imagem por digest. A 5.7.3 adicionou labels de ownership/capability/execução, cleanup verificável após encerramento normal, timeout, interrupção ou exceção e orphan detection por labels exatos.
