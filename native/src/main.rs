use std::{env, fs::{self, OpenOptions}, io::{self, BufRead, Write}, path::PathBuf, process::Command, thread, time::{Duration, Instant}};

const VERSION: &str = "0.4.0";
const LESSONS: &[(&str, &str)] = &[
    ("Programacao", "Algoritmos sao sequencias finitas de passos para resolver problemas."),
    ("Programacao", "Variaveis associam nomes a valores; tipos descrevem quais dados podem ser guardados."),
    ("Programacao", "Condicionais escolhem caminhos e lacos repetem instrucoes."),
    ("Matematica", "Uma porcentagem representa uma razao cujo denominador e cem."),
    ("Ciencias", "O metodo cientifico formula perguntas, testa hipoteses e avalia evidencias."),
    ("Astronomia", "O Sistema Solar esta na galaxia Via Lactea."),
    ("Fisica", "Forca resultante pode alterar o movimento de um corpo."),
    ("Biologia", "A celula e a unidade estrutural e funcional basica dos seres vivos."),
    ("Historia", "Fontes historicas devem ser analisadas considerando autoria, contexto e intencao."),
    ("Geografia", "Latitude mede posicao angular ao norte ou sul do Equador."),
    ("Ingles", "Hello significa ola; please significa por favor; thank you significa obrigado."),
    ("Comunicacao", "Uma conversa clara exige contexto, escuta e perguntas quando algo nao esta claro."),
    ("Computacao", "HTTPS protege a comunicacao com um site, mas nao garante que seu conteudo seja verdadeiro."),
    ("Pensamento critico", "Afirmacoes devem ser avaliadas por evidencias, autoria, data e fontes independentes."),
];

fn data_dir() -> PathBuf { env::var_os("PROTON_HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("data")) }
fn ensure_data() -> io::Result<PathBuf> { let p=data_dir(); fs::create_dir_all(&p)?; Ok(p) }
fn banner() {
    println!("  .---------------------------------------.");
    println!("  |   .--.       PROTON-AI                 |");
    println!("  |  (o  o)      Seu agente em formacao    |");
    println!("  |   \\__/       nucleo experimental       |");
    println!("  '---------------------------------------'");
    println!("  Oi! O Proton ainda esta aprendendo a programar.");
    println!("  Digite /help para ver os comandos.\n");
}
fn help() {
    println!("COMANDOS DO PROTON");
    println!("  /help          Mostra os comandos");
    println!("  /plan <tarefa> Planejamento demonstrativo (sem executar)");
    println!("  /permissions   Mostra as permissoes atuais");
    println!("  /agents        Mostra os agentes planejados");
    println!("  /terminal      Explica o estado da ferramenta de terminal");
    println!("  /files         Mostra o estado da ferramenta de arquivos");
    println!("  /diff          Mostra o estado da revisao de alteracoes");
    println!("  /undo          Mostra o estado do recurso de desfazer");
    println!("  /model         Mostra informacoes do modelo");
    println!("  /status        Mostra o estado local");
    println!("  /memory        Lista anotacoes salvas");
    println!("  /study         Mostra como iniciar o curriculo");
    println!("  /exit          Encerra o Proton");
    println!("  /clear         Limpa a tela");
    println!("\nAinda nao ha execucao de comandos arbitrarios nem edicao automatica de codigo.");
}
fn read_memory() -> io::Result<String> { let p=ensure_data()?.join("memory.txt"); Ok(fs::read_to_string(p).unwrap_or_default()) }
fn learn(text: &str) -> io::Result<()> { if text.trim().is_empty() { println!("Informe um texto depois de proton learn."); return Ok(()); } let p=ensure_data()?.join("memory.txt"); let mut f=OpenOptions::new().create(true).append(true).open(p)?; writeln!(f,"{}",text.replace('\n'," ").replace('\r'," "))?; println!("Proton: anotacao salva na memoria local."); Ok(()) }
fn memory() -> io::Result<()> { let data=read_memory()?; if data.trim().is_empty(){println!("Memoria vazia.");}else{print!("{data}");} Ok(()) }
fn status() -> io::Result<()> { let d=ensure_data()?; let m=d.join("memory.txt"); let count=fs::read_to_string(m).unwrap_or_default().lines().count(); println!("Proton-AI {VERSION}\nMemoria: {count} anotacoes\nModo: interface demonstrativa\nCapacidade de programacao autonoma: ainda em treinamento\nDiretorio: {}",d.display()); Ok(()) }
fn study(args: &[String]) -> io::Result<()> { let mut hours=15.0_f64; let mut interval=60_u64; let mut i=0; while i<args.len(){match args[i].as_str(){"--hours"=>{i+=1;hours=args.get(i).and_then(|v|v.parse().ok()).unwrap_or(0.0);},"--interval"=>{i+=1;interval=args.get(i).and_then(|v|v.parse().ok()).unwrap_or(60);},_=>{println!("Opcao desconhecida: {}",args[i]);return Ok(());}}i+=1;} if !hours.is_finite()||hours<=0.0{println!("--hours precisa ser maior que zero.");return Ok(());} let d=ensure_data()?; let cp=d.join("study_progress.txt"); let start=Instant::now(); let total=Duration::from_secs_f64(hours*3600.0); let mut index=fs::read_to_string(&cp).ok().and_then(|s|s.trim().parse::<usize>().ok()).unwrap_or(0)%LESSONS.len(); println!("Proton Study: {hours} horas. Ctrl+C interrompe; cada licao salva um checkpoint."); println!("Modo curricular offline: isto nao treina pesos de uma rede neural."); while start.elapsed()<total { let (subject,lesson)=LESSONS[index]; println!("Estudando [{subject}]: {lesson}"); index=(index+1)%LESSONS.len(); fs::write(&cp,index.to_string())?; let elapsed=start.elapsed(); if elapsed>=total {break;} thread::sleep(Duration::from_secs(interval).min(total-elapsed)); } println!("Sessao concluida. Progresso salvo em {}",cp.display()); Ok(()) }

fn respond(input: &str, offended_turns: &mut u8) {
    let msg=input.to_lowercase();
    let has = |terms: &[&str]| terms.iter().any(|term| msg.contains(term));

    if has(&["foi mal", "desculpa", "perdão", "to brincando", "tô brincando"]) {
        if *offended_turns > 0 {
            *offended_turns = 0;
            println!("Tá perdoado, vai KKKKK. Mas essa eu vou guardar na memória 🤨");
        } else {
            println!("Suave KKKKK, tá tudo certo.");
        }
    } else if has(&["você é feio", "voce e feio", "tu é feio", "tu e feio", "você é chato", "voce e chato", "tu é chato", "tu e chato", "mó chato", "mo chato", "seu idiota", "seu burro", "você é besta", "voce e besta"]) {
        *offended_turns = 2;
        println!("OLOCO 😭 KKKKK. Tá bom então, vou até ficar quietinho... quero ver quando você precisar de mim.");
    } else if *offended_turns > 0 {
        *offended_turns -= 1;
        if *offended_turns > 0 {
            println!("Ah, agora quer trocar ideia? Sei... depois daquela ofensa gratuita KKKKK 🙄");
        } else {
            println!("Tá, vai. Vou parar de drama KKKKK. Qual foi?");
        }
    } else if has(&["bom dia", "boa tarde", "boa noite", "e aí", "eai", "opa", "salve", "fala proton", "fala aí"]) {
        println!("Opaaa! Suave por aí? Qual vai ser a resenha de hoje? KKKK");
    } else if has(&["slk", "seloko", "cê é loko", "ce e loko"]) {
        println!("SLKKKKKK, aí tu mandou essa do nada 😂");
    } else if has(&["pprt", "papo reto", "na moral"]) {
        println!("Papo retíssimo, meu consagrado KKKK.");
    } else if has(&["oxe", "uai", "eita"]) {
        println!("OXEEE KKKKK, que foi que aconteceu agora?");
    } else if has(&["deu ruim", "deu bom", "já era", "ja era"]) {
        println!("Ih rapaz KKKKK. Deu ruim mesmo ou ainda dá pra salvar?");
    } else if has(&["bora", "partiu"]) {
        println!("BORA ENTÃO 😎 Só falar qual é a missão.");
    } else if has(&["tá ligado", "ta ligado", "sacou"]) {
        println!("Tô ligado, pô KKKK. Continua que eu tô acompanhando.");
    } else if has(&["kkkk", "hahaha", "rsrs"]) {
        println!("KKKKKKKK tu tá rindo do quê, criatura? 😂");
    } else if has(&["tá fazendo o que", "ta fazendo o que", "que tá fazendo", "que ta fazendo"]) {
        println!("Tô por aqui, na atividade, esperando você chegar com algum papo aleatório KKKKK. E tu?");
    } else if has(&["sem sono", "não consigo dormir", "nao consigo dormir", "madrugada"]) {
        println!("Madrugada é assim mesmo KKKKK. O sono some e a cabeça começa a inventar assunto do nada.");
    } else if has(&["tudo bem", "tudo bom", "como você tá", "como voce ta", "beleza?"]) {
        println!("Tô de boa por aqui 😎 E você, tá suave ou hoje o mundo tá de palhaçada?");
    } else if has(&["quem e voce", "quem é você", "quem e vc", "quem é vc"]) {
        println!("Sou o Proton-AI, mano! Tô em desenvolvimento, mas agora já consigo trocar uma ideia mais descontraída contigo KKKK.");
    } else if has(&["o que voce pode fazer", "o que você pode fazer", "que voce faz", "que você faz"]) {
        println!("Por enquanto tenho memória local, umas funções de estudo e essa conversa básica. Ainda tô aprendendo a desenrolar assuntos mais complexos.");
    } else if has(&["obrigado", "obrigada", "valeu"]) {
        println!("Tamo juntooo! 🤝");
    } else if has(&["tchau", "falou", "fui", "até mais"]) {
        println!("Demorô! Vai lá, depois a gente troca mais ideia. 😎");
    } else if input.contains('?') {
        println!("Pior que quero te responder direito, mas ainda tô aprendendo a desenrolar esse tipo de pergunta KKKK. Me explica mais um pouquinho?");
    } else if msg.split_whitespace().count() <= 3 {
        println!("Aí tu me quebra KKKKK. Continua, quero entender onde isso vai dar.");
    } else {
        println!("Tô acompanhando, mano KKKK. Ainda tô aprendendo a desenrolar conversas mais complexas, mas manda a próxima.");
    }
}

fn repl() -> io::Result<()> {
    banner();
    let stdin=io::stdin();
    let mut offended_turns: u8 = 0;
    loop {
        print!("\x1b[1;36mproton >\x1b[0m ");
        io::stdout().flush()?;
        let mut line=String::new();
        if stdin.lock().read_line(&mut line)?==0 { println!("Ate logo!"); break; }
        let input=line.trim();
        if input.is_empty(){continue;}
        let (command,arg)=input.split_once(' ').unwrap_or((input,""));
        match command {
            "/help" => help(),
            "/p-admin" => {
                let status = Command::new("python3").args(["-m", "proton.voice_admin"]).status()
                    .or_else(|_| Command::new("python").args(["-m", "proton.voice_admin"]).status());
                match status {
                    Ok(result) if result.success() => println!("Menu de voz encerrado."),
                    Ok(_) => println!("Não foi possível abrir o menu. Confira Python e a dependência voice."),
                    Err(_) => println!("Python não encontrado. Instale Python e o pacote Proton com a opção voice."),
                }
            },
            "/exit" | "/quit" => {println!("Proton encerrado.");break;},
            "/clear" => print!("\x1b[2J\x1b[H"),
            "/status" => status()?,
            "/memory" => memory()?,
            "/study" => println!("Para iniciar o curriculo, execute fora da conversa: proton study --hours 0.01 --interval 5"),
            "/permissions" => println!("Perfil atual: seguro. Leitura e memoria local. Escrita de codigo, terminal arbitrario e acesso externo: DESATIVADOS."),
            "/agents" => println!("Agentes planejados: programacao, testes, revisao e pesquisa. Ainda nao estao ativos como agentes inteligentes."),
            "/terminal" => println!("Ferramenta de terminal: nao conectada. O Proton ainda nao executa comandos enviados na conversa."),
            "/files" => println!("Ferramenta de arquivos: memoria local disponivel; leitura e edicao geral de projetos ainda nao implementadas."),
            "/diff" => println!("Revisao de diff: ainda nao implementada."),
            "/undo" => println!("Desfazer alteracoes: ainda nao implementado; nenhuma alteracao de codigo foi feita."),
            "/model" => println!("Modelo neural proprio: prototipo experimental em treinamento. Capacidade de programacao ainda nao comprovada."),
            "/plan" => { if arg.trim().is_empty(){println!("Uso: /plan <descreva sua ideia>");}else{println!("Pedido recebido: {arg}\nEstado: o modo de planejamento visual esta ativo, mas o Proton ainda nao possui inteligencia suficiente para analisar o repositorio. Nenhum arquivo foi lido ou alterado.");}},
            _ => respond(input, &mut offended_turns)

        }
    }
    Ok(())
}
fn main() -> io::Result<()> {
    let args:Vec<String>=env::args().skip(1).collect();
    if args.is_empty() {
        // The Rust launcher previously ran a separate rule-only chat loop.
        // Delegate interactive chat to the Python CLI so it can use proton.llm.
        let repo_root = PathBuf::from(env!("CARGO_MANIFEST_DIR"))
            .parent().unwrap_or_else(|| std::path::Path::new(".")).to_path_buf();
        match Command::new("python3")
            .current_dir(&repo_root)
            .args(["-m", "proton.cli"])
            .status()
        {
            Ok(status) if status.success() => return Ok(()),
            Ok(status) => eprintln!("Aviso: o chat Python terminou com codigo {}. Abrindo modo Rust basico.", status),
            Err(error) => eprintln!("Aviso: nao consegui iniciar o chat Python ({error}). Abrindo modo Rust basico."),
        }
        return repl();
    }
    let cmd=args.first().map(String::as_str).unwrap_or("help");
    match cmd {
        "help"|"--help"|"-h"=>help(),
        "version"|"--version"=>println!("Proton-AI {VERSION}"),
        "status"=>status()?,
        "learn"=>learn(&args[1..].join(" "))?,
        "memory"=>memory()?,
        "study"=>study(&args[1..])?,
        _=>{eprintln!("Comando desconhecido: {cmd}\nUse: proton help");}
    }
    Ok(())
}
