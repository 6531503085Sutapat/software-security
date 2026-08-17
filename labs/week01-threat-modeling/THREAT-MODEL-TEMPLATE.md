# Threat Model — <app name>

## 1. Data-flow diagram
![DFD image in week01](<img/DFD worksheet week1.png>)


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

## 4. Top 5 risks (likelihood × impact) + mitigation
1.
2.
3.
4.
5.
