# Proton IA Guardiã

O Proton pode usar o **Qwen3Guard-Gen-0.6B** como classificador local de segurança para analisar propostas da rede coletiva. O modelo distingue conteúdo `Safe`, `Controversial` e `Unsafe`, e reconhece categorias de risco em vários idiomas. Consulte o [repositório oficial Qwen3Guard](https://github.com/QwenLM/Qwen3Guard) e o [cartão do modelo](https://huggingface.co/Qwen/Qwen3Guard-Gen-0.6B).

## Instalação

Em um ambiente Python com PyTorch instalado:

```bash
pip install -e '.[guardian]'
```

Na primeira análise, os pesos são baixados do Hugging Face. Depois ficam no cache local.

## Analisar propostas pendentes

```bash
proton-collective guard --limit 20
```

O modelo é carregado uma vez por execução e examina até 20 propostas ainda não analisadas. Resultado `Safe` significa apenas que o classificador não detectou uma categoria de risco; ainda exige revisão humana. `Controversial`, `Unsafe` e respostas sem formato reconhecido ficam em quarentena para revisão.

## Limites de segurança

- A Guardiã é um filtro de segurança, não um verificador de fatos nem um detector de malware.
- Uma classificação `Safe` **não aprova** uma proposta, não publica nada e não a torna elegível para treinamento.
- O estado da proposta e `training_eligible` não são alterados pelo classificador.
- A classificação pode errar; conteúdo incerto exige revisão independente.
- O comando não é um serviço 24/7. É uma tarefa manual; execução contínua e hospedagem serão etapas separadas.
- O modelo é executado localmente via Transformers; nenhuma API de IA externa é chamada por este módulo.
