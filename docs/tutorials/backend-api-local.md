# Tutorial experimental — backend API local

Esta é a fatia experimental 6.3 em desenvolvimento. Ela comprova intenção natural gravada, contrato, revisão humana, runtime, política, execução e relatório para um plano REST declarativo.

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

O modo atual usa uma resposta gravada e reproduzível. Ele demonstra a fronteira linguagem natural → saída tipada sem chamada externa. O resumo retorna um `run_id`. Revise `.asef/api/plans/generated-plan.json`; somente depois retome a mesma run:

```powershell
.\.venv\Scripts\asef.exe api --run-id RUN_ID_RETORNADO --allow-port 8765
```

O comando preserva state, manifest, plano, resultado e relatórios sob `.asef/runs/RUN_ID` e retorna um resumo JSON em stdout. `ACCEPTED` significa somente que as assertions do plano passaram nessa execução local. Provider live ainda não está exposto; budgets de modelo, tokens, requests e duração já fazem parte da run, mas custo live e retries ainda precisam de integração específica.

Também existe uma prova Docker autocontida em `tooling/api-fixture`: fixture e executor rodam no mesmo container com rede externa desligada. O adapter cotidiano ainda executa no host contra loopback; alcançar um serviço real a partir do container exigirá uma política de rede dedicada e será uma fatia posterior.

Não substitua a fixture por um site público. Acesso público não é autorização, e esta subfatia rejeita hosts externos por contrato.
