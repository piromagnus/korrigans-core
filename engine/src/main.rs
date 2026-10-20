use std::collections::BTreeMap;
use std::env;
use std::fs::{self, File};
use std::io::{self, Read};
use std::path::{Path, PathBuf};
use std::time::UNIX_EPOCH;

// =========================================================================
// Pure Rust standard library SHA-256 implementation (FIPS 180-4)
// =========================================================================

struct Sha256 {
    state: [u32; 8],
    count: u64,
    buffer: [u8; 64],
}

const K: [u32; 64] = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5,
    0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3,
    0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc,
    0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7,
    0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3,
    0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5,
    0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208,
    0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2,
];

impl Sha256 {
    fn new() -> Self {
        Self {
            state: [
                0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a,
                0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19,
            ],
            count: 0,
            buffer: [0u8; 64],
        }
    }

    fn update(&mut self, mut data: &[u8]) {
        let buf_idx = (self.count & 0x3f) as usize;
        self.count += data.len() as u64;

        if buf_idx > 0 {
            let space = 64 - buf_idx;
            if data.len() >= space {
                self.buffer[buf_idx..64].copy_from_slice(&data[..space]);
                self.transform(&self.buffer.clone());
                data = &data[space..];
            } else {
                self.buffer[buf_idx..buf_idx + data.len()].copy_from_slice(data);
                return;
            }
        }

        while data.len() >= 64 {
            let mut block = [0u8; 64];
            block.copy_from_slice(&data[..64]);
            self.transform(&block);
            data = &data[64..];
        }

        if !data.is_empty() {
            self.buffer[..data.len()].copy_from_slice(data);
        }
    }

    fn transform(&mut self, block: &[u8; 64]) {
        let mut w = [0u32; 64];
        for i in 0..16 {
            w[i] = u32::from_be_bytes([
                block[4 * i],
                block[4 * i + 1],
                block[4 * i + 2],
                block[4 * i + 3],
            ]);
        }
        for i in 16..64 {
            let s0 = w[i - 15].rotate_right(7) ^ w[i - 15].rotate_right(18) ^ (w[i - 15] >> 3);
            let s1 = w[i - 2].rotate_right(17) ^ w[i - 2].rotate_right(19) ^ (w[i - 2] >> 10);
            w[i] = w[i - 16].wrapping_add(s0).wrapping_add(w[i - 7]).wrapping_add(s1);
        }

        let mut a = self.state[0];
        let mut b = self.state[1];
        let mut c = self.state[2];
        let mut d = self.state[3];
        let mut e = self.state[4];
        let mut f = self.state[5];
        let mut g = self.state[6];
        let mut h = self.state[7];

        for i in 0..64 {
            let s1 = e.rotate_right(6) ^ e.rotate_right(11) ^ e.rotate_right(25);
            let ch = (e & f) ^ ((!e) & g);
            let temp1 = h.wrapping_add(s1).wrapping_add(ch).wrapping_add(K[i]).wrapping_add(w[i]);
            let s0 = a.rotate_right(2) ^ a.rotate_right(13) ^ a.rotate_right(22);
            let maj = (a & b) ^ (a & c) ^ (b & c);
            let temp2 = s0.wrapping_add(maj);

            h = g;
            g = f;
            f = e;
            e = d.wrapping_add(temp1);
            d = c;
            c = b;
            b = a;
            a = temp1.wrapping_add(temp2);
        }

        self.state[0] = self.state[0].wrapping_add(a);
        self.state[1] = self.state[1].wrapping_add(b);
        self.state[2] = self.state[2].wrapping_add(c);
        self.state[3] = self.state[3].wrapping_add(d);
        self.state[4] = self.state[4].wrapping_add(e);
        self.state[5] = self.state[5].wrapping_add(f);
        self.state[6] = self.state[6].wrapping_add(g);
        self.state[7] = self.state[7].wrapping_add(h);
    }

    fn finalize(mut self) -> String {
        let bit_count = self.count * 8;
        let buf_idx = (self.count & 0x3f) as usize;

        let mut pad = [0u8; 128];
        pad[0] = 0x80;
        let pad_len = if buf_idx < 56 {
            56 - buf_idx
        } else {
            120 - buf_idx
        };

        for i in 0..8 {
            pad[pad_len + i] = ((bit_count >> (56 - i * 8)) & 0xff) as u8;
        }

        self.update(&pad[..pad_len + 8]);

        let mut hex = String::with_capacity(64);
        for &s in &self.state {
            for b in s.to_be_bytes() {
                hex.push_str(&format!("{:02x}", b));
            }
        }
        hex
    }
}

fn compute_sha256(path: &Path) -> io::Result<String> {
    let mut file = File::open(path)?;
    let mut hasher = Sha256::new();
    let mut buf = [0u8; 65536];
    loop {
        let n = file.read(&mut buf)?;
        if n == 0 {
            break;
        }
        hasher.update(&buf[..n]);
    }
    Ok(hasher.finalize())
}

// =========================================================================
// Frontmatter & Markdown parsing
// =========================================================================

#[derive(Debug, Clone)]
struct Frontmatter {
    fields: BTreeMap<String, String>,
}

impl Frontmatter {
    fn get(&self, key: &str) -> Option<&str> {
        self.fields.get(key).map(|s| s.as_str())
    }
}

fn parse_frontmatter(content: &str) -> Option<Frontmatter> {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return None;
    }
    let after_start = &trimmed[3..];
    let end_idx = after_start.find("\n---")?;
    let fm_text = &after_start[..end_idx];

    let mut fields = BTreeMap::new();
    for line in fm_text.lines() {
        let l = line.trim();
        if l.is_empty() || l.starts_with('#') {
            continue;
        }
        if let Some((k, v)) = l.split_once(':') {
            let key = k.trim().to_string();
            let mut val = v.trim();
            // Strip trailing comments
            if let Some((clean_val, _)) = val.split_once(" #") {
                val = clean_val.trim();
            }
            // Strip quotes
            let val_str = if (val.starts_with('"') && val.ends_with('"'))
                || (val.starts_with('\'') && val.ends_with('\''))
            {
                if val.len() >= 2 {
                    &val[1..val.len() - 1]
                } else {
                    val
                }
            } else {
                val
            };
            fields.insert(key, val_str.to_string());
        }
    }
    Some(Frontmatter { fields })
}

// =========================================================================
// Confidence Score Calculation
// =========================================================================

struct Confidence {
    score: i32,
    level: String,
    reasons: Vec<String>,
}

fn calculate_task_confidence(task_dir: &Path, meta: Option<&Frontmatter>) -> Confidence {
    let status = meta
        .and_then(|f| f.get("status"))
        .unwrap_or("todo")
        .to_lowercase();
    let blocking = meta.and_then(|f| f.get("blocking")).map(|b| {
        let b = b.trim();
        b == "true" || b == "1" || (b.starts_with('[') && b.contains('"'))
    }).unwrap_or(false);

    let card_file = task_dir.join("card.md");
    let has_card = card_file.is_file() && fs::metadata(&card_file).map(|m| m.len() > 0).unwrap_or(false);

    let (score, reasons) = match status.as_str() {
        "todo" => {
            let s = if !blocking { 90 } else { 50 };
            (s, vec!["Contract pending implementation".to_string()])
        }
        "done" => {
            let s = if has_card { 95 } else { 75 };
            (s, vec!["Task completed with confirmed deliverables".to_string()])
        }
        "to-review" => {
            let s = if has_card { 90 } else { 55 };
            (s, vec!["Complete delivery submitted for review".to_string()])
        }
        "in-progress" => {
            let s = if has_card { 70 } else { 45 };
            (s, vec!["In progress".to_string()])
        }
        _ => {
            (40, vec!["Pending arbitration".to_string()])
        }
    };

    let level = if score >= 80 {
        "high"
    } else if score >= 50 {
        "medium"
    } else {
        "low"
    }.to_string();

    Confidence {
        score,
        level,
        reasons,
    }
}

// =========================================================================
// JSON Utilities
// =========================================================================

fn escape_json(s: &str) -> String {
    let mut out = String::with_capacity(s.len() + 16);
    for c in s.chars() {
        match c {
            '"' => out.push_str("\\\""),
            '\\' => out.push_str("\\\\"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\x08' => out.push_str("\\b"),
            '\x0c' => out.push_str("\\f"),
            c if (c as u32) < 0x20 => {
                out.push_str(&format!("\\u{:04x}", c as u32));
            }
            c => out.push(c),
        }
    }
    out
}

// =========================================================================
// Subcommand: tasks
// =========================================================================

fn run_tasks(workspace: &Path) -> io::Result<()> {
    let tasks_dir = workspace.join("tasks");
    if !tasks_dir.is_dir() {
        println!("[]");
        return Ok(());
    }

    let mut charters: Vec<PathBuf> = Vec::new();

    // Check direct tasks/T-NNNN.../charter.md
    if let Ok(entries) = fs::read_dir(&tasks_dir) {
        for entry in entries.flatten() {
            let p = entry.path();
            if p.is_dir() {
                let name = p.file_name().unwrap_or_default().to_string_lossy();
                let charter = p.join("charter.md");
                if name.starts_with("T-") && charter.is_file() {
                    charters.push(charter);
                } else if !name.starts_with('.') {
                    // Check subproject tasks: tasks/<project>/T-NNNN.../charter.md
                    if let Ok(sub_entries) = fs::read_dir(&p) {
                        for sub_entry in sub_entries.flatten() {
                            let sub_p = sub_entry.path();
                            if sub_p.is_dir() {
                                let sub_name = sub_p.file_name().unwrap_or_default().to_string_lossy();
                                let sub_charter = sub_p.join("charter.md");
                                if sub_name.starts_with("T-") && sub_charter.is_file() {
                                    charters.push(sub_charter);
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    charters.sort();

    let mut json_items = Vec::new();

    for charter in charters {
        let task_folder = charter.parent().unwrap();
        let rel_charter = charter.strip_prefix(workspace).unwrap_or(&charter).to_string_lossy().to_string();
        let rel_folder = task_folder.strip_prefix(workspace).unwrap_or(task_folder).to_string_lossy().to_string();

        let content = fs::read_to_string(&charter).unwrap_or_default();
        let fm = parse_frontmatter(&content);

        let folder_name = task_folder.file_name().unwrap_or_default().to_string_lossy();
        let task_id = fm
            .as_ref()
            .and_then(|f| f.get("id"))
            .map(|s| s.to_string())
            .unwrap_or_else(|| {
                if folder_name.starts_with("T-") && folder_name.len() >= 6 {
                    folder_name[..6].to_string()
                } else {
                    folder_name.to_string()
                }
            });

        let card_path = task_folder.join("card.md");
        let card_present = card_path.is_file() && fs::metadata(&card_path).map(|m| m.len() > 0).unwrap_or(false);

        let evidence_dir = task_folder.join("evidence");
        let evidence_count = if evidence_dir.is_dir() {
            fs::read_dir(&evidence_dir)
                .map(|entries| entries.filter_map(|e| e.ok()).filter(|e| e.path().is_file()).count())
                .unwrap_or(0)
        } else {
            0
        };

        let conf = calculate_task_confidence(task_folder, fm.as_ref());

        let title = fm.as_ref().and_then(|f| f.get("title")).unwrap_or("");
        let task_type = fm.as_ref().and_then(|f| f.get("type")).unwrap_or("code");
        let status = fm.as_ref().and_then(|f| f.get("status")).unwrap_or("todo");
        let project = fm.as_ref().and_then(|f| f.get("project")).unwrap_or("");
        let priority = fm.as_ref().and_then(|f| f.get("priority")).unwrap_or("");
        let difficulty = fm.as_ref().and_then(|f| f.get("difficulty")).unwrap_or("");
        let blocking = fm.as_ref().and_then(|f| f.get("blocking")).unwrap_or("");
        let waiting_on = fm.as_ref().and_then(|f| f.get("waiting_on")).unwrap_or("");

        let mut fm_entries = Vec::new();
        if let Some(ref f) = fm {
            for (k, v) in &f.fields {
                fm_entries.push(format!("\"{}\":\"{}\"", escape_json(k), escape_json(v)));
            }
        }

        let reasons_json = conf
            .reasons
            .iter()
            .map(|r| format!("\"{}\"", escape_json(r)))
            .collect::<Vec<_>>()
            .join(",");

        let item = format!(
            concat!(
                "{{",
                "\"id\":\"{}\",",
                "\"path\":\"{}\",",
                "\"folder\":\"{}\",",
                "\"title\":\"{}\",",
                "\"type\":\"{}\",",
                "\"status\":\"{}\",",
                "\"project\":\"{}\",",
                "\"priority\":\"{}\",",
                "\"difficulty\":\"{}\",",
                "\"blocking\":\"{}\",",
                "\"waiting_on\":\"{}\",",
                "\"card_present\":{},",
                "\"evidence_count\":{},",
                "\"confidence_score\":{},",
                "\"confidence_level\":\"{}\",",
                "\"confidence_reasons\":[{}],",
                "\"frontmatter\":{{{}}}",
                "}}"
            ),
            escape_json(&task_id),
            escape_json(&rel_charter),
            escape_json(&rel_folder),
            escape_json(title),
            escape_json(task_type),
            escape_json(status),
            escape_json(project),
            escape_json(priority),
            escape_json(difficulty),
            escape_json(blocking),
            escape_json(waiting_on),
            card_present,
            evidence_count,
            conf.score,
            escape_json(&conf.level),
            reasons_json,
            fm_entries.join(",")
        );
        json_items.push(item);
    }

    println!("[{}]", json_items.join(",\n"));
    Ok(())
}

// =========================================================================
// Subcommand: scan
// =========================================================================

struct ScannedFile {
    path: String,
    size: u64,
    mtime_ns: u128,
    sha256: String,
    frontmatter: Option<Frontmatter>,
    confidence: Option<Confidence>,
}

fn walk_dir(
    dir: &Path,
    root: &Path,
    prefix: &str,
    results: &mut Vec<ScannedFile>,
) -> io::Result<()> {
    if !dir.is_dir() {
        return Ok(());
    }

    let entries = fs::read_dir(dir)?;
    for entry in entries.flatten() {
        let path = entry.path();
        let name = path.file_name().unwrap_or_default().to_string_lossy();

        if name.starts_with('.')
            || name == "node_modules"
            || name == "target"
            || name == "__pycache__"
            || name == "dist"
            || name == "build"
        {
            continue;
        }

        if path.is_dir() {
            walk_dir(&path, root, prefix, results)?;
        } else if path.is_file() {
            let meta = match fs::metadata(&path) {
                Ok(m) => m,
                Err(_) => continue,
            };
            let size = meta.len();
            let mtime_ns = meta
                .modified()
                .ok()
                .and_then(|t| t.duration_since(UNIX_EPOCH).ok())
                .map(|d| d.as_nanos())
                .unwrap_or(0);

            let rel = path.strip_prefix(root).unwrap_or(&path).to_string_lossy();
            let display_path = if prefix.is_empty() {
                rel.to_string()
            } else {
                format!("{}/{}", prefix, rel)
            };

            let sha = compute_sha256(&path).unwrap_or_default();

            let (fm, conf) = if path.extension().map(|e| e == "md").unwrap_or(false) {
                let content = fs::read_to_string(&path).unwrap_or_default();
                let f = parse_frontmatter(&content);
                let c = if display_path.ends_with("/charter.md") || display_path == "charter.md" {
                    let parent = path.parent().unwrap_or(dir);
                    Some(calculate_task_confidence(parent, f.as_ref()))
                } else {
                    None
                };
                (f, c)
            } else {
                (None, None)
            };

            results.push(ScannedFile {
                path: display_path,
                size,
                mtime_ns,
                sha256: sha,
                frontmatter: fm,
                confidence: conf,
            });
        }
    }
    Ok(())
}

fn run_scan(workspace: &Path, core: Option<&Path>) -> io::Result<()> {
    let mut files = Vec::new();
    walk_dir(workspace, workspace, "", &mut files)?;

    if let Some(c) = core {
        if c.is_dir() && c != workspace {
            walk_dir(c, c, "core", &mut files)?;
        }
    }

    files.sort_by(|a, b| a.path.cmp(&b.path));

    let mut json_files = Vec::new();
    for f in &files {
        let fm_json = if let Some(ref fm) = f.frontmatter {
            let entries = fm
                .fields
                .iter()
                .map(|(k, v)| format!("\"{}\":\"{}\"", escape_json(k), escape_json(v)))
                .collect::<Vec<_>>()
                .join(",");
            format!("{{{}}}", entries)
        } else {
            "null".to_string()
        };

        let conf_json = if let Some(ref conf) = f.confidence {
            let reasons = conf
                .reasons
                .iter()
                .map(|r| format!("\"{}\"", escape_json(r)))
                .collect::<Vec<_>>()
                .join(",");
            format!(
                concat!(
                    "{{",
                    "\"score\":{},",
                    "\"level\":\"{}\",",
                    "\"reasons\":[{}]",
                    "}}"
                ),
                conf.score,
                escape_json(&conf.level),
                reasons
            )
        } else {
            "null".to_string()
        };

        let item = format!(
            concat!(
                "{{",
                "\"path\":\"{}\",",
                "\"size\":{},",
                "\"mtime_ns\":{},",
                "\"sha256\":\"{}\",",
                "\"frontmatter\":{},",
                "\"confidence\":{}",
                "}}"
            ),
            escape_json(&f.path),
            f.size,
            f.mtime_ns,
            escape_json(&f.sha256),
            fm_json,
            conf_json
        );
        json_files.push(item);
    }

    let core_str = core
        .map(|c| format!("\"{}\"", escape_json(&c.to_string_lossy())))
        .unwrap_or_else(|| "null".to_string());

    println!(
        concat!(
            "{{",
            "\"workspace\":\"{}\",",
            "\"core\":{},",
            "\"count\":{},",
            "\"files\":[{}]",
            "}}"
        ),
        escape_json(&workspace.to_string_lossy()),
        core_str,
        files.len(),
        json_files.join(",\n")
    );

    Ok(())
}

// =========================================================================
// Main entry point & CLI parsing
// =========================================================================

fn print_usage() {
    eprintln!(
        "Usage: korrigans-engine <subcommand> [options]\n\n\
        Subcommands:\n  \
        scan     --workspace <path> [--core <path>]\n  \
        tasks    --workspace <path>\n  \
        version  print version\n"
    );
}

fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() < 2 {
        print_usage();
        std::process::exit(1);
    }

    let subcmd = &args[1];
    let mut workspace: Option<PathBuf> = None;
    let mut core: Option<PathBuf> = None;

    let mut i = 2;
    while i < args.len() {
        match args[i].as_str() {
            "--workspace" | "-w" => {
                if i + 1 < args.len() {
                    workspace = Some(PathBuf::from(&args[i + 1]));
                    i += 1;
                }
            }
            "--core" | "-c" => {
                if i + 1 < args.len() {
                    core = Some(PathBuf::from(&args[i + 1]));
                    i += 1;
                }
            }
            "-h" | "--help" => {
                print_usage();
                return;
            }
            _ => {}
        }
        i += 1;
    }

    match subcmd.as_str() {
        "tasks" => {
            let ws = workspace.unwrap_or_else(|| env::current_dir().unwrap_or_default());
            if let Err(e) = run_tasks(&ws) {
                eprintln!("Error discovering tasks: {}", e);
                std::process::exit(1);
            }
        }
        "scan" => {
            let ws = workspace.unwrap_or_else(|| env::current_dir().unwrap_or_default());
            if let Err(e) = run_scan(&ws, core.as_deref()) {
                eprintln!("Error scanning directory: {}", e);
                std::process::exit(1);
            }
        }
        "version" | "--version" => {
            println!("korrigans-engine 0.1.0 (Rust standard library edition)");
        }
        _ => {
            eprintln!("Unknown subcommand: {}", subcmd);
            print_usage();
            std::process::exit(1);
        }
    }
}
