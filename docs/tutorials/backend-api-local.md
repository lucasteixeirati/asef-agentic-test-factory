# Tutorial experimental — backend API local

Esta é a primeira subfatia da 6.3. Ela comprova contrato, política, execução e relatório para um plano REST declarativo. A geração do plano por linguagem natural ainda não faz parte desta subfatia.

## Limites

- somente origem HTTP em endereço literal de loopback;
- porta informada simultaneamente no plano e na allowlist do comando;
- `GET`, `HEAD` e `OPTIONS` por padrão;
- sem redirects, proxies, credenciais persistidas ou headers de transporte controlados pelo plano;
- limite de cenários, timeout, payload e resposta;
- servidor fictício incluído no repositório.

## Executar

Em um terminal, inicie exclusivamente a fixture local:

```powershell
.\.venv\Scripts\python.exe examples\api\fixture_server.py
```

Em outro terminal, gere primeiro um plano revisável a partir da intenção em linguagem natural:

```powershell
.\.venv\Scripts\asef.exe api-generate --requirement "Verifique que a API local informa que está saudável" --base-url http://127.0.0.1:8765 --allow-port 8765
```

O modo atual usa uma resposta gravada e reproduzível. Ele demonstra a fronteira linguagem natural → saída tipada sem chamada externa. Revise `.asef/api/plans/generated-plan.json`; somente depois execute:

```powershell
.\.venv\Scripts\asef.exe api --plan .asef\api\plans\generated-plan.json --allow-port 8765
```

O comando grava JSON e Markdown sob `.asef/api` e retorna um resumo JSON em stdout. `ACCEPTED` significa somente que as assertions do plano passaram nessa execução local. Provider live ainda não está exposto nesta subfatia porque o orçamento monetário e a evidência da chamada precisam ser integrados ao contrato da run.

Não substitua a fixture por um site público. Acesso público não é autorização, e esta subfatia rejeita hosts externos por contrato.
