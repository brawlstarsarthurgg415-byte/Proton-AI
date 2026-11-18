use std::{env, fs::{self, OpenOptions}, io::{self, BufRead, Write}, path::PathBuf, thread, time::{Duration, Instant}};

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
fn repl() -> io::Result<()> {
    banner();
    let stdin=io::stdin();
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
            _ => println!("Ainda estou aprendendo a entender pedidos. Use /help para ver os comandos disponiveis.")
        }
    }
    Ok(())
}
fn main() -> io::Result<()> {
    let args:Vec<String>=env::args().skip(1).collect();
    if args.is_empty() { return repl(); }
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
