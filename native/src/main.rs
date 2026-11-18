use std::{env, fs::{self, OpenOptions}, io::{self, Write}, path::PathBuf, thread, time::{Duration, Instant, SystemTime, UNIX_EPOCH}};

const VERSION: &str = "0.3.0";
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
    ("Pensamento critico", "Afirmações devem ser avaliadas por evidencias, autoria, data e fontes independentes."),
];

fn data_dir() -> PathBuf { env::var_os("PROTON_HOME").map(PathBuf::from).unwrap_or_else(|| PathBuf::from("data")) }
fn ensure_data() -> io::Result<PathBuf> { let p=data_dir(); fs::create_dir_all(&p)?; Ok(p) }
fn help() { println!("Proton-AI {VERSION} — comandos nativos\n\nUSO:\n  proton help                  Mostra esta ajuda\n  proton version               Mostra a versao\n  proton status                Mostra o estado local\n  proton learn <texto>         Guarda uma anotacao\n  proton ask <termos>          Procura na memoria\n  proton memory                Lista anotacoes\n  proton study [opcoes]        Inicia sessao de estudos\n\nESTUDO:\n  proton study --hours 15 --interval 60\n  --hours HORAS       Duracao (padrao 15)\n  --interval SEGUNDOS Pausa entre revisoes (padrao 60)\n\nOs dados ficam em ./data ou em PROTON_HOME. O estudo atual percorre um
curriculo introdutorio e salva checkpoints; nao treina pesos de rede neural."); }
fn read_memory() -> io::Result<String> { let p=ensure_data()?.join("memory.txt"); Ok(fs::read_to_string(p).unwrap_or_default()) }
fn learn(text: &str) -> io::Result<()> { if text.trim().is_empty() { println!("Informe um texto depois de proton learn."); return Ok(()); } let p=ensure_data()?.join("memory.txt"); let mut f=OpenOptions::new().create(true).append(true).open(p)?; writeln!(f,"{}",text.replace('\n'," ").replace('\r'," "))?; println!("Proton: anotacao salva na memoria local."); Ok(()) }
fn ask(q: &str) -> io::Result<()> { let q=q.to_lowercase(); let mut found=0; for line in read_memory()?.lines() { if q.split_whitespace().any(|w| line.to_lowercase().contains(w)) { println!("• {line}"); found+=1; } } if found==0 { println!("Ainda nao encontrei isso na memoria local."); } Ok(()) }
fn memory() -> io::Result<()> { let data=read_memory()?; if data.trim().is_empty(){println!("Memoria vazia.");}else{print!("{data}");} Ok(()) }
fn status() -> io::Result<()> { let d=ensure_data()?; let m=d.join("memory.txt"); let count=fs::read_to_string(m).unwrap_or_default().lines().count(); let p=d.join("study_progress.txt"); let progress=fs::read_to_string(p).unwrap_or_else(|_|"Nenhuma sessao iniciada".into()); println!("Proton-AI {VERSION}\nMemoria: {count} anotacoes\nCheckpoint: {}\nDiretorio: {}",progress.trim(),d.display()); Ok(()) }
fn study(args: &[String]) -> io::Result<()> { let mut hours=15.0_f64; let mut interval=60_u64; let mut i=0; while i<args.len(){match args[i].as_str(){"--hours"=>{i+=1;hours=args.get(i).and_then(|v|v.parse().ok()).unwrap_or(0.0);},"--interval"=>{i+=1;interval=args.get(i).and_then(|v|v.parse().ok()).unwrap_or(60);},_=>{println!("Opcao desconhecida: {}",args[i]);return Ok(());}}i+=1;} if !hours.is_finite()||hours<=0.0{println!("--hours precisa ser maior que zero.");return Ok(());} let d=ensure_data()?; let cp=d.join("study_progress.txt"); let start=Instant::now(); let total=Duration::from_secs_f64(hours*3600.0); let mut index=fs::read_to_string(&cp).ok().and_then(|s|s.trim().parse::<usize>().ok()).unwrap_or(0)%LESSONS.len(); println!("Proton Study: {hours} horas. Ctrl+C interrompe; cada licao salva um checkpoint."); println!("Modo curricular offline: isto nao treina pesos de uma rede neural."); while start.elapsed()<total { let (subject,lesson)=LESSONS[index]; println!("Estudando [{subject}]: {lesson}"); index=(index+1)%LESSONS.len(); fs::write(&cp,index.to_string())?; let elapsed=start.elapsed(); if elapsed>=total {break;} thread::sleep(Duration::from_secs(interval).min(total-elapsed)); } println!("Sessao concluida. Progresso salvo em {}",cp.display()); Ok(()) }
fn main() -> io::Result<()> { let args:Vec<String>=env::args().skip(1).collect(); let cmd=args.first().map(String::as_str).unwrap_or("help"); match cmd {"help"|"--help"|"-h"=>help(),"version"|"--version"=>println!("Proton-AI {VERSION}"),"status"=>status()?,"learn"=>learn(&args[1..].join(" "))?,"ask"=>ask(&args[1..].join(" "))?,"memory"=>memory()?,"study"=>study(&args[1..])?,_=>{eprintln!("Comando desconhecido: {cmd}\nUse: proton help");}} Ok(()) }
