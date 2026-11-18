# Proton Brain 3B MoE — projeto

## Meta escolhida

- Total nominal: aproximadamente 3,15 bilhões de parâmetros.
- Arquitetura: Transformer decoder-only com Mixture of Experts.
- Roteamento: top-2 entre 8 especialistas em cada bloco MoE.
- Destino: Android, com pesos quantizados em 4 bits como meta de implantação.
- Sem API de IA externa.

## Perfil de arquitetura

O perfil executável de referência está em `configs/proton-3b-moe-android.json`:

| Campo | Valor |
|---|---:|
| Vocabulário | 32.000 tokens |
| Contexto | 2.048 tokens |
| Camadas | 16 |
| Dimensão oculta | 2.048 |
| Cabeças de atenção | 16 |
| Especialistas por camada | 8 |
| Especialistas ativados por token | 2 |
| Dimensão intermediária por especialista | 3.584 |

Estimativa aproximada de parâmetros: 3,15B, incluindo embeddings compartilhados. O valor exato deve ser conferido pelo contador após implementação de toda a arquitetura e pode variar com futuras mudanças.

## O que já está implementado

`proton/moe.py` contém uma implementação PyTorch funcional e configurável de:
- embedding de tokens e posições;
- atenção causal;
- RMSNorm;
- especialistas SwiGLU;
- roteador top-k esparso;
- perda auxiliar de balanceamento de carga;
- estatísticas de quantos tokens foram enviados a cada especialista.

Os testes usam uma configuração minúscula para verificar forward, backward, roteamento e validação. Eles **não** instanciam o perfil 3B.

## Limite importante do Android

O arquivo de configuração é um alvo de arquitetura, não um modelo treinado ou pronto para instalar. 3B pesos em 4 bits ocupam aproximadamente 1,5 GB em armazenamento bruto, antes de metadados, alinhamento, KV cache, ativações, buffers e runtime. Mesmo com top-2, os pesos dos oito especialistas precisam estar acessíveis ao runtime. Portanto MoE reduz computação por token, mas não elimina o custo de armazenar os especialistas.

Não treine nem carregue o perfil 3B completo em um celular nesta etapa. O caminho seguro é:
1. testar a arquitetura pequena em CPU;
2. implementar tokenizer BPE e pipeline de dados licenciado;
3. treinar em hardware com memória e GPU adequadas;
4. validar qualidade em benchmarks independentes;
5. quantizar e converter para um runtime móvel, por exemplo avaliando ExecuTorch;
6. medir RAM, latência, bateria e temperatura no aparelho Android exato.

## Estado honesto

O código atual é um núcleo MoE experimental inicial. Não é um assistente conversacional treinado, não tem conhecimento amplo por padrão e não deve ser descrito como um modelo 3B pronto. O perfil 3B ainda exige tokenizer, treino, dados, avaliação, quantização e integração móvel.
