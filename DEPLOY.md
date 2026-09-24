# Deploy (AWS Lightsail + domínio no Hostinger)

Frontend (Vue, buildado como estático) e backend (Node) ficam atrás do
**Caddy**, que serve os arquivos estáticos, faz proxy de `/api/*` pro
backend e provisiona HTTPS automaticamente (Let's Encrypt) — só precisa
de um domínio apontando pro IP do servidor.

O backend chama o modelo BLIP fine-tuned via um processo Python
persistente (`model/src/serve.py`) — por isso precisa de um servidor de
verdade (não serverless) com pelo menos 2GB de RAM.

## 1. Criar a instância na AWS

**Lightsail** (mais simples que EC2 puro pra esse caso — preço fixo, IP
estático incluso, firewall já vem numa UI simples):

1. [lightsail.aws.amazon.com](https://lightsail.aws.amazon.com/) → **Create instance**.
2. Plataforma: **Linux/Unix** → Blueprint: **OS Only → Ubuntu 24.04 LTS**.
3. Plano: pelo menos o de **$10/mês (2 GB RAM, 2 vCPU, 60GB SSD)** — o de
   $5 (1GB) não tem folga pro modelo carregado + Node + Caddy juntos.
4. Depois de criado: aba **Networking** → **Attach static IP** (fica de
   graça enquanto a instância existir) e libera as portas **80** e **443**
   (HTTP/HTTPS) além da **22** (SSH, geralmente já vem liberada).

## 2. Apontar o domínio (no Hostinger)

No hPanel do Hostinger → **Domínios → [seu domínio] → DNS/Nameservers** →
adiciona/edita um registro:

| Tipo | Nome | Aponta para |
|---|---|---|
| A | `@` (ou o subdomínio que quiser, ex: `livros`) | IP estático da instância Lightsail |

Propagação pode levar de minutos a algumas horas.

## 3. Instalar Docker na instância

Conecta via SSH (Lightsail tem um terminal no navegador, ou use seu
cliente SSH com a chave baixada na criação da instância):

```sh
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# desloga e loga de novo (ou `newgrp docker`) pro grupo valer
```

## 4. Clonar o repo e subir o checkpoint treinado

```sh
git clone https://github.com/Pedrocanoas/tcc.git
cd tcc
mkdir -p model/checkpoints/best
```

O checkpoint (`model/checkpoints/best/`, ~1GB) é gitignored — não vem no
`git clone`. Copia do seu PC pro servidor via `scp` (rode isso na sua
máquina, não no servidor):

```sh
scp -r model/checkpoints/best ubuntu@<ip-da-instancia>:~/tcc/model/checkpoints/
```

## 5. Configurar o domínio e subir

Na instância, dentro de `~/tcc`:

```sh
echo "DOMAIN=seu-dominio.com" > .env
docker compose up -d --build
```

Primeira subida demora um pouco (build instala torch CPU, ~700MB). Depois:

```sh
docker compose logs -f        # acompanhar os dois serviços
docker compose ps             # ver se subiu certo
```

Acesse `https://seu-dominio.com` — o Caddy deve ter provisionado o
certificado sozinho (só funciona com o DNS já propagado e as portas 80/443
liberadas).

## Atualizando depois de um `git push`

```sh
cd ~/tcc
git pull
docker compose up -d --build
```

## Troubleshooting

- **Caddy não consegue HTTPS**: confirma que o DNS já propagou
  (`dig seu-dominio.com` deve devolver o IP da instância) e que as portas
  80/443 estão liberadas no firewall da Lightsail.
- **Backend reinicia em loop / OOM**: instância com menos de 2GB de RAM
  não aguenta o modelo carregado — sobe de plano.
- **Erro "python não encontrado" no backend**: confirma que
  `model/checkpoints/best/` tem os arquivos certos (`model.safetensors`,
  `config.json` etc.) — sem checkpoint, `serve.py` cai pro modelo base do
  Hugging Face (funciona, mas sem o fine-tuning).
