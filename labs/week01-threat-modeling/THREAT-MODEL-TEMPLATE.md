# Threat Model — <app name>

## 1. Data-flow diagram
(Insert your DFD image. Mark trust boundaries with dashed lines.)
![DFD ของ sample-app](<img/DFD worksheet w1 02.drawio.png>)

## 2. Elements & trust boundaries
| Element | Type (process/store/entity/flow) | Trust boundary crossed? |
|---|---|---|
| Web client | external entity | yes (Internet → app) |
| Flask app | process | yes (Internet -> Flask app) |
| SQLite DB (`notes.db`) | data store |No (Internet -> Flask app ->notes.db) |
| `uploads/` store | data store | No (Internet -> Flask app -> uploads) |

## 3. STRIDE analysis
| Element | S | T | R | I | D | E |
|---|---|---|---|---|---|---|
| /notes | S | T | R | I | D | - |
| /upload | - | T | R | I | D | - |
| /files/<name> | - | - | - | I | | - |
## 3b. Systems-level pass

### Trust boundaries end-to-end
A request from the client to `notes.db` crosses 2 boundaries:
1. Internet → Flask app** (Public Internet → Application Tier) — no authentication, no input validation
2. Flask app → notes.db / uploads/ (Application Tier → Data Tier) — no access control, client data inserted directly

Neither crossing has any check on it.

### Assume one element is fully owned
- Flask app owned → attacker can read/modify/delete all notes in `notes.db`, read/overwrite all files in `uploads/`, and path-traverse to the host filesystem via unsanitized filenames.
- uploads/ owned → attacker places malicious files (malware, phishing pages) and any user can download them via `/files/<name>` without authentication — the server becomes a malware distribution point.

### Chain two "low" findings
`Path traversal via /upload (no secure_filename)` → `/files/<name> serves any file without auth` → attacker overwrites application files and serves malicious content to all users.

### One-line system claim
> "Even if every element-level mitigation in Task 8 is implemented, this system still fails if there is no authentication — any anonymous user on the network can still read, create, and manipulate all data."
## 4. Top 5 risks (likelihood × impact) + mitigation
1.
2.
3.
4.
5.
