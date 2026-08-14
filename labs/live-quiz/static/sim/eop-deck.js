/* eop-deck.js — Week 1 simulation: a digital "Elevation of Privilege" deck.
 *
 * WHAT THIS IS FOR
 * Task 3 of the worksheet plays Microsoft's real EoP card deck against your
 * DFD — but that needs a printer and scissors (print-and-play PDF, cut into
 * 78 cards). Not everyone has both. This reproduces the actual mechanic —
 * draw a card, try to tie its threat to a real element on YOUR diagram, score
 * a point if you can — with no printing, no cutting, just a projector or a
 * shared screen. The 78 card prompts below are the real EoP deck text
 * (github.com/adamshostack/eop, CC-BY-3.0), not a paraphrase.
 *
 * This is deliberately NOT a quiz: there's no right answer to check, because
 * the "is this a real threat on my DFD" call is the whole exercise. The
 * player self-scores, same as the physical game — honesty is the point.
 */
(function () {
  "use strict";

  var SUITS = [
    { key: "S", name: "Spoofing", color: "#017BC4" },
    { key: "T", name: "Tampering", color: "#B83E00" },
    { key: "R", name: "Repudiation", color: "#6b4fa0" },
    { key: "I", name: "Information Disclosure", color: "#1B6408" },
    { key: "D", name: "Denial of Service", color: "#B01430" },
    { key: "E", name: "Elevation of Privilege", color: "#A87A00" }
  ];

  // The real EoP deck: 6 suits x 13 ranks = 78 cards. Text is verbatim from
  // cards.yaml in the official repo (2-10, J, Q, K, A order per suit).
  var DECK_TEXT = {
    S: [
      "An attacker could take over the port or socket that the server normally uses",
      "An attacker could try one credential after another and there's nothing to slow them down (online or offline)",
      "An attacker can anonymously connect, because we expect authentication to be done at a higher level",
      "An attacker can confuse a client because there are too many ways to identify a server",
      "An attacker can spoof a server because identifiers aren't stored on the client and checked for consistency on re-connection (no key persistence)",
      "An attacker can connect to a server or peer over a link that isn't authenticated (and encrypted)",
      "An attacker could steal credentials stored on the server and reuse them (for example, a key stored in a world-readable file)",
      "An attacker who gets a password can reuse it (use stronger authenticators)",
      "An attacker can choose to use weaker or no authentication",
      "An attacker could steal credentials stored on the client and reuse them",
      "An attacker could go after the way credentials are updated or recovered (account recovery doesn't require disclosing the old password)",
      "Your system ships with a default admin password, and doesn't force a change",
      "You've invented a new Spoofing attack"
    ],
    T: [
      "An attacker can modify your build system and produce signed builds of your software",
      "An attacker can take advantage of your custom key exchange or integrity control which you built instead of using standard crypto",
      "Your code makes access control decisions all over the place, rather than with a security kernel",
      "An attacker can replay data without detection because your code doesn't provide timestamps or sequence numbers",
      "An attacker can write to a data store your code relies on",
      "An attacker can bypass permissions because you don't make names canonical before checking access permissions",
      "An attacker can manipulate data because there's no integrity protection for data on the network",
      "An attacker can provide or control state information",
      "An attacker can alter information in a data store because it has weak/open permissions or includes a group equivalent to everyone",
      "An attacker can write to some resource because permissions are granted to the world or there are no ACLs",
      "An attacker can change parameters over a trust boundary after validation (e.g. a hidden HTML field, or a pointer to critical memory)",
      "An attacker can load code inside your process via an extension point",
      "You've invented a new Tampering attack"
    ],
    R: [
      "An attacker can pass data through the log to attack a log reader, and there's no documentation of what validation is done",
      "A low-privilege attacker can read interesting security information in the logs",
      "An attacker can alter digital signatures because the signature system is weak, or uses MACs where it should use a signature",
      "An attacker can alter log messages on a network because they lack strong integrity controls",
      "An attacker can create a log entry without a timestamp (or no log entry is timestamped)",
      "An attacker can make the logs wrap around and lose data",
      "An attacker can make a log lose or confuse security information",
      "An attacker can use a shared key to authenticate as different principals, confusing the information in the logs",
      "An attacker can get arbitrary data into logs from unauthenticated (or weakly authenticated) outsiders without validation",
      "An attacker can edit logs and there's no way to tell (perhaps because there's no heartbeat for the logging system)",
      "An attacker can say “I didn't do that,” and you'd have no way to prove them wrong",
      "The system has no logs",
      "You've invented a new Repudiation attack"
    ],
    I: [
      "An attacker can brute-force file encryption because there's no defense in place (e.g. password stretching)",
      "An attacker can see error messages with security-sensitive content",
      "An attacker can read content because messages (an email, an HTTP cookie) aren't encrypted even if the channel is",
      "An attacker may be able to read a document or data because it's encrypted with a non-standard algorithm",
      "An attacker can read data because it's hidden or occluded (for undo or change tracking) and the user might forget it's there",
      "An attacker can act as a 'man in the middle' because you don't authenticate endpoints of a network connection",
      "An attacker can access information through a search indexer, logger, or other such mechanism",
      "An attacker can read sensitive information in a file with permissive permissions",
      "An attacker can read information in files or databases with no access controls",
      "An attacker can discover the fixed key being used to encrypt",
      "An attacker can read the entire channel because it (HTTP, SMTP) isn't encrypted",
      "An attacker can read network information because there's no cryptography used",
      "You've invented a new Information Disclosure attack"
    ],
    D: [
      "An attacker can make your authentication system unusable or unavailable",
      "An attacker can drain an easily-replaceable battery",
      "An attacker can drain a battery that's hard to replace (sealed in a phone, an implanted device, or hard to reach)",
      "An attacker can spend your cloud budget",
      "An attacker can make a server unavailable without ever authenticating, but the problem goes away when the attacker stops",
      "An attacker can make a client unavailable and the problem persists after the attacker goes away",
      "An attacker can make a server unavailable and the problem persists after the attacker goes away",
      "An attacker can make a client unavailable without ever authenticating, and the problem persists after they go away",
      "An attacker can make a server unavailable without ever authenticating, and the problem persists after they go away",
      "An attacker can cause the logging subsystem to stop working",
      "An attacker can amplify a denial-of-service attack through this component roughly 10 to 1",
      "An attacker can amplify a denial-of-service attack through this component roughly 100 to 1",
      "You've invented a new Denial of Service attack"
    ],
    E: [
      "An attacker has compromised a key technology supplier",
      "An attacker can access the cloud service which manages your devices",
      "An attacker can escape from a container or other sandbox",
      "An attacker can force data through different validation paths which give different results",
      "An attacker could take advantage of permissions you set, but don't use",
      "An attacker can provide a pointer across a trust boundary, rather than data which can be validated",
      "An attacker can enter data that is checked while still under their control and used later on the other side of a trust boundary",
      "There's no reasonable way for a caller to figure out what validation of tainted data you perform before passing it to them",
      "There's no reasonable way for a caller to figure out what security assumptions you make",
      "An attacker can reflect input back to a user, like cross-site scripting",
      "You include user-generated content within your page, possibly including the content of random URLs",
      "An attacker can inject a command that the system will run at a higher privilege level",
      "You've invented a new Elevation of Privilege attack"
    ]
  };

  var DECK = [];
  SUITS.forEach(function (s) {
    DECK_TEXT[s.key].forEach(function (text) {
      DECK.push({ suit: s, text: text });
    });
  });

  function shuffled(arr) {
    var a = arr.slice();
    for (var i = a.length - 1; i > 0; i--) {
      var j = Math.floor(Math.random() * (i + 1));
      var t = a[i]; a[i] = a[j]; a[j] = t;
    }
    return a;
  }

  var pile = [], drawn = 0, tied = 0, seenSuits = {}, current = null, judged = false;

  var suitRow = document.getElementById("suit-row");
  var cardEl = document.getElementById("card");
  var suitNameEl = document.getElementById("suit-name");
  var textEl = document.getElementById("card-text");
  var drawBtn = document.getElementById("draw");
  var tieBtn = document.getElementById("tie");
  var passBtn = document.getElementById("pass");
  var drawnEl = document.getElementById("drawn");
  var tiedEl = document.getElementById("tied");
  var doneEl = document.getElementById("done");

  function renderSuitRow() {
    suitRow.innerHTML = "";
    SUITS.forEach(function (s) {
      var chip = document.createElement("span");
      chip.className = "eop-chip" + (seenSuits[s.key] ? " is-seen" : "");
      chip.style.setProperty("--chip-color", s.color);
      chip.textContent = s.key;
      chip.title = s.name;
      suitRow.appendChild(chip);
    });
  }

  function renderEmpty() {
    cardEl.classList.remove("is-shown");
    suitNameEl.textContent = "";
    textEl.textContent = "";
    tieBtn.hidden = true;
    passBtn.hidden = true;
    drawBtn.hidden = false;
    drawBtn.textContent = drawn === 0 ? "Draw a card →" : "Draw next card →";
  }

  function draw() {
    if (pile.length === 0) {
      pile = shuffled(DECK);
    }
    current = pile.pop();
    judged = false;
    drawn++;
    seenSuits[current.suit.key] = true;
    drawnEl.textContent = String(drawn);
    renderSuitRow();

    cardEl.classList.add("is-shown");
    cardEl.style.setProperty("--suit-color", current.suit.color);
    suitNameEl.textContent = current.suit.key + " — " + current.suit.name;
    textEl.textContent = current.text;

    drawBtn.hidden = true;
    tieBtn.hidden = false;
    passBtn.hidden = false;
    tieBtn.disabled = false;
    passBtn.disabled = false;
  }

  function judge(scored) {
    if (judged) return;
    judged = true;
    if (scored) { tied++; tiedEl.textContent = String(tied); }
    tieBtn.disabled = true;
    passBtn.disabled = true;
    drawBtn.hidden = false;
    drawBtn.textContent = "Draw next card →";
    var allSix = SUITS.every(function (s) { return seenSuits[s.key]; });
    if (allSix) doneEl.classList.add("is-shown");
  }

  drawBtn.addEventListener("click", draw);
  tieBtn.addEventListener("click", function () { judge(true); });
  passBtn.addEventListener("click", function () { judge(false); });

  renderSuitRow();
  renderEmpty();
})();
