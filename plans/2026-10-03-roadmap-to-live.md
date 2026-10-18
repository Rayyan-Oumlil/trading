---
created: 2026-10-03
objective: Rendre l'algorithme progressivement plus fort sans se mentir, définir objectivement quand passer à l'argent réel, et répliquer exactement le système en réel en sécurité.
status: proposé — attend les 3 décisions de Rayyan (§11)
data: backtests/portfolio_stats/results/2026-10-03.json (script backtests/portfolio_stats/combined_v1.py)
---

# Feuille de route : algo plus fort → argent réel

**Légende :**
- **[F]** fait sourcé (lien en fin de document)
- **[E]** estimation ou calcul de notre part
- **[D]** décision que toi seul peux prendre

---

## 0. En bref

1. **Alpaca n'ouvre pas de compte réel aux résidents canadiens [F].**
   - Le passage au réel se fera donc chez un autre broker.
   - **IBKR Canada** est le seul candidat trouvé qui permet à un Canadien de trader des ETF américains (SPY, IBIT…) **par API** [F].
   - Conséquence : on porte le robot sur IBKR et on le teste en papier là-bas avant le réel.
2. **Aujourd'hui, notre portefeuille ≈ SPY [E].**
   - Sur 2018→2026 : 14,8 %/an contre 14,5 % ; Sharpe 0,86 contre 0,81 ; pire baisse −27 % contre −34 %.
   - Le volet SPY-tendance seul fait 8,6 %/an : il réduit le risque mais coûte du rendement.
   - Contre SPY, l'avantage mesuré est nul (ratio d'information 0,004).
3. **« Si mon bénéfice papier est très bien » n'est pas un bon déclencheur [E].**
   - Il faut environ **3,7 ans** de données pour prouver statistiquement qu'un Sharpe de 0,86 est positif.
   - Sur 3 mois, être **12,5 points derrière SPY** arrive 1 fois sur 20 par simple hasard.
   - La décision « réel » doit reposer sur trois choses, pas sur quelques bons mois : un backtest solide, une exécution fidèle, et un comportement dans la bande attendue.
4. **Selon la règle du §5, la version actuelle (v1) n'est pas encore « assez bonne » pour le réel [E].**
   - Elle échoue sur le Sharpe (0,86 < 0,91 exigé) et sur la pire baisse (−27,5 % > −27,0 % permis).
   - On itère d'abord (Phase 1). C'est exactement ton plan, mais avec des règles qui t'empêchent de te mentir.

---

## 1. Où on en est (2026-10-03)

| | |
|---|---|
| Compte papier (Alpaca) | 100 000 $ le 2026-04-23 → 103 448 $ (+3,4 % contre SPY +9,2 %) |
| Portefeuille v1 | SPY 85,5 % · BTC 5 % · ETH 5 %, chacun en croisement SMA 10/50, échange seulement au changement de signal |
| Backtest v1, 2018→2026 [E] | CAGR 14,8 % · vol 17,8 % · Sharpe 0,86 · pire baisse −27,5 % |
| SPY conservé, même période [E] | CAGR 14,5 % · vol 19,0 % · Sharpe 0,81 · pire baisse −33,7 % |
| Volet SPY-tendance seul [E] | CAGR 8,6 % · Sharpe 0,77 · pire baisse −15,1 % |
| Bande normale sur 3 mois [E] | retard sur SPY ≥ −12,5 pts (5e centile) ; pire baisse ≥ −14,2 % (5e centile) |
| Essais déjà faits (N) | **≈ 10** : SMA 10/50, VIX25, RSI(2), RSI(2) avec stop, rsi2-multi ×3 variantes, momentum sectoriel, dual momentum, crypto trend. Chaque essai rend le suivant plus suspect (§2.4). |
| Infra | robot déterministe, garde-fous, frein automatique, Telegram, 146 tests |

---

## 2. Ce que disent les recherches

### 2.1 Brokers pour un résident canadien

| Broker | ETF américains par API ? | Crypto | Points clés | Verdict |
|---|---|---|---|---|
| **Alpaca** | Réel : **non**, les Canadiens ne sont pas éligibles [F]. Papier : oui. | non | Garde-le comme **compte papier de référence**. | ❌ réel |
| **IBKR Canada** | **Oui pour les titres US. Interdit pour les titres canadiens** : règle OCRI (ex-OCRCVM), DMR 3200 A [F]. | Crypto directe pour les Canadiens : infos contradictoires, **à vérifier** [F]. ETF bitcoin US (IBIT, frais 0,25 %) achetables par un Canadien [F]. | API = TWS API via **IB Gateway**, un programme qui doit rester connecté et demande une ré-authentification 2FA chaque semaine [F]. L'API Web en OAuth est officiellement réservée aux institutions [F]. CELI et REER disponibles [F]. Commission US : 0,005 $/action, min 1 $ [F]. Change de devises : 0,2 point de base, min 2 $ US [F]. | ✅ **recommandé** |
| Questrade | **Non** : l'API personnelle est en lecture seule ; passer des ordres est réservé aux partenaires [F]. | — | — | ❌ |
| moomoo Canada | API pour les comptes canadiens **non confirmée** | — | Réglementé OCRI ; CELI et REER [F]. | ❓ à vérifier |
| Public.com | — | — | **Pas disponible au Canada** [F]. | ❌ |
| Kraken | — | Oui, au Canada, plateforme enregistrée [F] | Frais palier 1 : **0,40 % maker / 0,80 % taker** [F]. | ✅ alternative crypto (chère) |
| Coinbase Advanced | — | Oui [F] | Moins de 1 000 $ de volume : 0,60 % / **1,20 %**. De 1 000 à 10 000 $ : 0,35 % / 0,75 % [F]. Nouvelle grille annoncée le 2026-09-16, à revérifier [F]. | ⚠️ cher à petite taille |
| Binance, Bybit, OKX | — | **Ont quitté le Canada en 2023** [F] | — | ❌ (conflit avec CLAUDE.md, §10) |

### 2.2 Fiscalité (Canada / Québec, 2026)

- **Gains en capital : taux d'inclusion de 50 %.** La hausse à 2/3 a été annulée le 2025-03-21 [F].
- **Revenu d'entreprise ou gain en capital ?** C'est une question de faits [F] :
  - les critères sont la fréquence, la durée de détention, les connaissances spéciales et l'usage de la marge ;
  - si c'est une « entreprise », le gain est **100 % imposable**, même dans un **CELI** [F].
- **Perte apparente :** si tu rachètes le même titre 30 jours avant ou après une vente à perte (toi ou une personne affiliée, **y compris ton CELI**), la perte est refusée. Si le rachat se fait dans le CELI, elle est **perdue pour de bon** [F].
  - ⚠️ Notre croisement de moyennes revend et rachète parfois en quelques jours (exemple réel : 22 → 23 sept.).
- **Crypto :** traitée comme une marchandise. Chaque disposition est imposable, y compris crypto → crypto ; c'est du capital ou de l'entreprise selon les faits [F].
  - Un CELI ne peut pas détenir de crypto directement, seulement via des ETF [E, à confirmer].
- **CELI 2026 :** plafond de 7 000 $ ; cumul maximal de 109 000 $ selon l'année de tes 18 ans. Vérifie ton droit dans « Mon dossier » de l'ARC [F].
- **Dividendes américains :** **15 % retenus dans un CELI, 0 % dans un REER** (traité fiscal) [F].
- **Québec :** deux déclarations, fédérale et Revenu Québec [E]. → **1 heure avec un fiscaliste avant la Phase 4** (assurance peu chère).

### 2.3 Papier vs réel

- Le papier **sous-estime le glissement**, ignore la file d'attente des ordres à cours limité, et simule les exécutions partielles au hasard (10 % chez Alpaca) [F].
- Nos ordres SPY partent après la clôture et s'exécutent à l'ouverture suivante. En réel, un gap d'ouverture s'écarte du prix du signal [E]. On le mesure déjà : frein si l'écart dépasse 2 %.
- **Règle PDT (day trading) : supprimée.** Approbation SEC le 2026-04-14, en vigueur le 2026-06-04 [F]. Elle ne nous concernait de toute façon pas : on détient pendant des jours ou des semaines.
- À petite taille, **les minimums de frais pèsent lourd** : 1 $ par ordre chez IBKR, taux taker en crypto (§9).

### 2.4 Ne pas se mentir (anti-surapprentissage)

- **Probabilité de surapprentissage (PBO) :** la probabilité que la meilleure version en échantillon finisse sous la médiane hors échantillon [F].
- **Deflated Sharpe Ratio (DSR) :** corrige le Sharpe selon le **nombre d'essais** et les queues épaisses. « Aurais-je trouvé ça par chance en essayant N variantes ? » [F]
- **Durée minimale d'historique (MinTRL) :** combien de temps il faut pour prouver un Sharpe supérieur à un seuil [F]. Pour notre v1 : **≈ 3,7 ans** pour prouver un Sharpe > 0 [E].
- **Harvey, Liu, Zhu :** avec tout le data mining en finance, exiger une statistique t > 3, pas > 2 [F].
- **Walk-forward et hors échantillon :** la PBO complète le walk-forward mais ne remplace pas la confirmation en conditions réelles [F].
- **Ce qu'on fait déjà bien :** pré-inscription, une seule exécution, résultats sur disque.
- **Ce qui manque :** un **compteur N d'essais** et le DSR calculé automatiquement.

### 2.5 Taille des positions et risque

- **Ciblage de volatilité :** il améliore le Sharpe des actifs risqués comme les actions, et réduit les rendements extrêmes dans toutes les classes d'actifs [F].
  - Moreira et Muir trouvent de gros gains [F], mais d'autres travaux le contestent : échec hors échantillon (Cederburg et al.), effet annulé par les coûts (Barroso & Detzel) [F].
  - → À **tester**, pas à supposer.
- **Kelly fractionnaire :** le Kelly complet maximise la croissance mais il est très risqué à court terme ; une fraction garde l'essentiel du gain avec beaucoup moins de risque [F].
  - Pour nous : pas de levier, jamais. Kelly rappelle surtout qu'on ne mise pas plus gros que l'avantage prouvé, qui est aujourd'hui ≈ 0 contre SPY.
- **Frein en réel :** voir §6. Le frein bloque les **achats**, jamais les **ventes**.

---

## 3. Feuille de route datée [E]

| Phase | Dates | Objectif | Critères de sortie (chiffrés) | Échec si… |
|---|---|---|---|---|
| **0. Stabiliser** | 2026-10-05 → 10-16 | Le système corrigé tourne proprement | 10 séances d'affilée : 0 run rouge inexpliqué, 0 double trade, décisions identiques au rejeu des règles, achats crypto et ré-entrée SPY exécutés **une seule fois** | Double trade, trade sans signal ou frein inexpliqué → on corrige et on recompte à 0 |
| **1. Itérer** | 2026-10-19 → 12-18 (9 sem.) | Trouver une **v2** qui bat clairement SPY ; construire les outils | ≤ 9 tests pré-inscrits (1 par semaine), registre N + DSR + MinTRL automatiques, **v2 figée qui passe la partie A du §5**, compte IBKR ouvert et papier IBKR actif | Rien ne passe → v1 reste en papier, on continue. **Pas de réel.** |
| **2. Valider** (papier Alpaca) | 2026-12-21 → 2027-03-26 (~60 séances) | Prouver que le code fait ce que dit le backtest | Parties **B et C** du §5 | Écart papier/rejeu > 1 pt, ou sortie de bande → diagnostic, retour en Phase 1 |
| **3. Miroir** (papier IBKR) | 2027-01-04 → 03-26 (en parallèle de la Phase 2) | Prouver qu'IBKR exécute comme Alpaca | ≥ 40 séances, 100 % de décisions identiques, 0 ordre rejeté inexpliqué, écart médian de prix d'exécution ≤ 10 points de base, réauthentification hebdomadaire sans séance manquée | ≥ 2 séances manquées à cause de la passerelle → régler l'hébergement (§6) |
| **Revue** | 2027-03-29 | Appliquer le §5 tel qu'écrit, consigner la décision dans `journal/` | — | — |
| **4. Réel petit** | 2027-04-05 → 07-02 | Le même système en vrai, petite taille | 1re semaine en **mode ombre** (ordres calculés sur le vrai compte, pas envoyés), puis réel. Écart réel vs papier IBKR ≤ 0,5 pt/mois, 0 incident | Baisse > 25 % depuis le sommet, ou perte d'un jour > 7 % → frein (achats bloqués) et revue |
| **5. Monter en taille** | à partir de 2027-07 | Augmenter par paliers | ×2 au maximum par trimestre, seulement si la Phase 4 tient. Plafond **[D]** : un montant dont une perte de 30 % ne change rien à ta vie | Nouvelle pire baisse au-delà de celle du backtest → retour au palier précédent |

**À noter :**
- Ouvre le compte IBKR **pendant la Phase 1**, car l'ouverture prend des jours.
- IBKR peut exiger un compte réel approuvé, voire alimenté, avant d'activer le compte papier [E, à vérifier].

---

## 4. Le processus d'itération hebdomadaire

### Le cycle (une idée maximum par semaine)

| Jour | Étape | Livrable |
|---|---|---|
| Lun | Revue : P&L de la semaine, registre, incidents | 5 minutes de lecture |
| Mar | Choisir l'idée du backlog et écrire la **pré-inscription** | entrée dans `research/queue.md`, **committée avant le code** (l'horodatage fait preuve) |
| Mer | Coder le test (tests unitaires d'abord), puis **geler le code** | commit « code gelé » |
| Jeu | Exécuter **une seule fois** ; DSR avec N = nombre total d'essais | `results/*.json` avec le SHA + ligne dans `backtests/registry.md` |
| Ven | Décider (PASS ou FAIL selon la règle écrite) et écrire au journal | `journal/AAAA-MM-JJ.md` ; si PASS, la stratégie devient candidate pour la v2 |

### Règles
- Chaque test **augmente N, même un échec**.
- Un FAIL n'est **jamais** retesté sans nouvelle thèse écrite (CLAUDE.md §7).
- Un PASS n'entre pas automatiquement dans le portefeuille. Il faut un test au niveau du portefeuille : est-ce que ça **monte le Sharpe** du tout et **réduit la pire baisse** ?
- Un changement de portefeuille par mois au maximum.

### Modèle de pré-inscription
- Thèse en une phrase
- Source
- Univers
- Règles d'entrée et de sortie
- **Paramètres, tous tirés de la source**
- Coûts **réels** du broker visé
- Fenêtres : complète et récente (2022→)
- Critère de réussite
- **Numéro d'essai N**
- « Ce qui me ferait abandonner l'idée »

### Backlog priorisé

| # | Idée | Pourquoi | Source | Test proposé (à figer en pré-inscription) |
|---|---|---|---|---|
| **0** | **Crypto via ETF US** (IBIT et équivalent ETH) exécutés à l'ouverture US | Prérequis du réel : c'est la seule route crypto peu chère chez IBKR. Mais on perd le 24/7, donc il faut vérifier que l'avantage survit. | IBIT, frais 0,25 % [F] | Même signal BTC/ETH, exécution à la prochaine ouverture NYSE. PASS si le Sharpe est ≥ 80 % de la version 24/7 **et** bat toujours le simple fait de garder BTC/ETH. |
| **1** | **Ciblage de volatilité** sur le volet SPY | Le volet SPY coûte du rendement (8,6 %/an) ; sur les actions, ce ciblage vise un meilleur Sharpe | Harvey et al. 2018 ; Moreira & Muir 2017, avec leurs critiques [F] | En tendance haussière : exposition = min(100 %, cible ÷ vol réalisée sur 20 jours), la cible étant la vol long terme de SPY ; sinon cash |
| **2** | **GTAA5 de Faber** (moyenne 10 mois, 5 classes d'actifs) | Plus de paris indépendants : c'est la vraie façon de monter un Sharpe | Faber 2007 [F] | SPY, EFA, IEF, VNQ, DBC à 20 % chacun ; investi au-dessus de la moyenne 10 mois, cash sinon ; revue mensuelle ; 2005→ |
| **3** | **Momentum de série temporelle 12 mois**, multi-actifs | Le résultat le plus robuste de la littérature sur les tendances | Moskowitz, Ooi, Pedersen 2012 [F] | 12 mois, mêmes ETF + or, pondération inverse de la vol. **Seulement si l'idée 2 échoue** (elles se recoupent). |
| **4** | **Effet de tournant de mois** sur SPY | Une autre famille de signal (calendaire), peu corrélée | McConnell & Xu 2008 [F] | Long SPY du dernier jour du mois aux 3 premiers jours, cash sinon. Preuves anciennes, donc attentes faibles. |
| **5** | **Momentum absolu** comme bouclier du volet SPY | A presque évité 2008 dans notre test (−2,7 % contre −36 %) | Antonacci [F] | Nouvelle thèse explicite, volet SPY seulement. Proche d'un test déjà échoué → seuil de preuve plus haut. |

---

## 5. Critère « assez bon pour le réel »

Écrit le 2026-10-03, **avant** tout résultat de la v2. Non négociable.

**Partie A : preuve d'avantage (backtest de la v2 figée). Tout est obligatoire.**
1. Chaque volet a passé son propre test pré-inscrit.
2. Sur la même période (2018→ au minimum ; 2005→ pour les volets actions) : **Sharpe du portefeuille ≥ Sharpe de SPY + 0,10**.
3. **Pire baisse ≤ 80 % de celle de SPY** sur la même période.
4. **DSR ≥ 0,95**, avec N = nombre total d'essais du registre.
5. Rentable dans au moins 2 régimes, par exemple le krach de 2020, la baisse de 2022 et les années haussières (porte 1 de CLAUDE.md).

**Partie B : fidélité (papier, au moins 60 séances, paramètres figés)**

6. Écart cumulé entre le papier et le rejeu du backtest sur les mêmes jours ≤ **1,0 point**.
7. 0 incident inexpliqué sur les 20 dernières séances, et miroir IBKR à 100 % de décisions identiques.

**Partie C : comportement dans la bande.** Le but n'est pas « bénéfice très bien », mais « rien d'anormal ».

8. Retard sur SPY sur la période ≤ 5e centile historique pour la même durée (v1 : **−12,5 pts sur 3 mois**).
9. Pire baisse ≤ 5e centile historique pour la même durée (v1 : **−14 % sur 3 mois**).

**Partie D : toi**

10. Tu expliques chaque ligne (porte 3) : quiz de 10 questions sur le code, résultat 10/10.
11. Le montant de départ est de l'argent dont la perte totale ne change rien à ta vie. Fonds d'urgence à part.

**Verrou :**
- Les seuils ne changent **que** par une entrée datée dans `journal/`, écrite **avant** un nouveau test.
- Un échec = pas de réel, sans négociation.

**v1 aujourd'hui [E] : pas assez bonne.**
- Point 2 : ❌ (0,86 < 0,81 + 0,10 = 0,91).
- Point 3 : ❌ (−27,5 % pire que 0,8 × −33,7 % = −27,0 %).
- Point 4 : pas encore calculé.

**Pourquoi le +0,10 :** le réel ajoute des frais, de l'impôt, de l'exploitation et un risque de bug. Si l'algo ne bat pas *clairement* SPY, le choix rationnel est d'acheter un ETF S&P 500 et de ne rien faire.

---

## 6. Architecture du miroir papier → réel

**Principe : un seul cerveau, plusieurs mains.**
- Les décisions sont calculées **une fois**, puis appliquées à chaque compte avec les mêmes pondérations × l'avoir propre de ce compte.
- Le papier et le réel ne peuvent donc pas diverger sur les décisions, seulement sur l'exécution, et c'est exactement ce qu'on mesure.

```
                    (GitHub Actions, 20h10 ET)
 données ──► portfolio/decide.py ──► memory/decisions/AAAA-MM-JJ.json   ← la seule vérité
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          ▼                               ▼                               ▼
 execute(alpaca-paper)          execute(ibkr-paper)             execute(ibkr-live)
 GitHub Actions                 hôte avec IB Gateway            même hôte, ARMÉ
 référence                      miroir (Phase 3)                réel (Phase 4)
          └──────────────► routines_pkg/reconcile.py ◄────────────────────┘
               positions vs attendu, écart papier/réel → Telegram + frein
```

**Règles de sécurité en réel :**
- **Double clé :** le réel ne s'exécute que si `live-trading/ARMED` existe (daté, et justifié dans `journal/`) **et** si la variable `LIVE_TRADING=1` est définie sur l'hôte.
- **Frein = achats bloqués, ventes permises.**
  - Arrêter une stratégie de tendance pendant un krach bloquerait justement sa sortie.
  - Aujourd'hui `.HALT` bloque tout ; à corriger en réel.
- **Plafonds :**
  - taille maximale d'un ordre = poids × avoir × 1,05 ;
  - plafond absolu en $ **[D]** ;
  - liste fermée des symboles par compte.
- **Réconciliation quotidienne :** positions réelles vs positions attendues, et écart de rendement papier/réel. Hors tolérance → frein + Telegram.
- **Secrets :** les identifiants IBKR restent **uniquement** sur l'hôte réel, jamais sur GitHub.

**Hébergement d'IB Gateway** (il doit rester connecté, avec 2FA chaque semaine sur ton téléphone [F]) :
- (a) **Ton PC** : gratuit, et c'est déjà le déclencheur de 20h10. Suffisant pour les Phases 3 et 4 à petite taille. Une séance manquée se rattrape sans risque de doublon grâce à l'idempotence.
- (b) **Petit VPS** (~5 à 10 $/mois [E]) avec IB Gateway et IBC en Docker : pour la Phase 5.

**Fichiers à créer ou modifier :**

| Fichier | Rôle |
|---|---|
| `brokers/base.py` (nouveau) | Interface `Broker` : compte, positions, ordres, calendrier, historique |
| `brokers/alpaca_broker.py` (nouveau) | Adapte l'actuel `paper_trading/alpaca_client.py` |
| `brokers/ibkr_broker.py` (nouveau) | IBKR via `ib_async` ; ordres à l'ouverture (OPG/MOO) pour SPY et les ETF |
| `portfolio/decide.py` (nouveau) | Signaux + pondérations → `memory/decisions/<date>.json` (avec l'empreinte des données) |
| `portfolio/execute.py` (nouveau) | Applique les décisions à **un** compte : mise à l'échelle, garde-fous, frein |
| `config/accounts.yaml` (nouveau) | `alpaca-paper` (référence), `ibkr-paper` (miroir), `ibkr-live` (plafonds) |
| `routines_pkg/reconcile.py` (nouveau) | Écart quotidien entre comptes, positions vs attendu, Telegram |
| `live-trading/README.md`, `live-trading/ARMED` (nouveaux) | Porte du réel : date et justification |
| `deploy/ib-gateway/` (nouveau) | docker-compose et modèle de config IBC, **sans secrets** |
| `backtests/registry.md`, `backtests/stats/dsr.py` (nouveaux) | Registre des essais N ; DSR, MinTRL, PBO ; avec tests |
| `run_signal.py` | Devient un mince enchaînement : `decide` puis `execute(alpaca-paper)` |
| `strategies/portfolio.py` | Correspondance volet → instrument par broker (BTC/USD chez Alpaca ↔ IBIT chez IBKR) |
| `paper_trading/guards.py`, `paper_trading/kill_switch.py` | Plafonds, frein « achats seulement », frein par compte |
| `routines_pkg/desk_snapshot.py`, `routines_pkg/auto_halt.py` | Par compte |
| `.github/workflows/daily-trade.yml` | Décider, publier les décisions, exécuter le papier |
| `requirements.txt` | `ib_async` (version épinglée) |
| `CLAUDE.md` | Portes et brokers (§10), **après ton accord** |

---

## 7. Plan d'argent réel

- **Broker : IBKR Canada, IBKR Pro, compte au comptant (sans marge) [D].**
  - Sans marge, l'interdiction d'emprunter devient structurelle.
  - Les titres US sont tradables par API ; les titres canadiens ne le sont pas, et on n'en a pas besoin.
- **Crypto :**
  - **Via ETF US** si l'idée 0 du backlog passe.
  - Sinon via Kraken, avec des ordres maker à 0,40 %.
  - Ou pas de crypto en réel tant que le compte est petit (voir les coûts au §9).
- **Type de compte [D]. Ma recommandation : non enregistré (au comptant) pour la Phase 4.**
  - Les pertes sont déductibles, il n'y a pas d'ambiguïté « entreprise dans le CELI », et c'est compatible avec les ETF crypto.
  - Inconvénients : impôt sur les gains (inclusion de 50 %) et suivi de la règle de perte apparente.
  - Le **CELI viendra plus tard** si la rotation reste faible (moins d'environ 10 transactions par an), après avis d'un fiscaliste.
- **Montant de départ [D] :** **2 000 à 5 000 $** suggérés.
  - En dessous, les frais minimums mangent l'avantage (§9).
  - Une mauvaise année peut coûter 25 à 30 %.
- **Devises :** convertir CAD → USD **une fois** chez IBKR (0,2 point de base, min 2 $ US [F]) et garder les USD.
- **Montée en taille :**
  - ×2 au maximum par trimestre, à date fixe, seulement si les critères tiennent.
  - **Jamais après un excellent mois**, jamais pour « se refaire » après une perte.
- **Retraits :** aucun pendant la Phase 4. Ensuite, une revue annuelle.

---

## 8. Risques

| Type | Risque | Parade |
|---|---|---|
| Technique | Bug qui trade de travers (comme le NaN de septembre) | Tests en CI avant chaque run, garde-fous, frein, mode ombre avant le réel |
| Technique | IB Gateway déconnecté (2FA hebdomadaire manquée) | Alerte Telegram, rattrapage idempotent, VPS en Phase 5 |
| Technique | Écart entre la donnée de décision et le prix réel | Une seule source de décision (fichier de décisions) ; mesure du gap ; frein si l'écart dépasse 2 % |
| Technique | Fuite d'identifiants | Secrets seulement sur l'hôte réel ; clés crypto sans droit de retrait |
| Marché | Krach ou gap d'ouverture | Volet SPY en tendance (souvent à plat dans les krachs) ; le frein ne bloque jamais les ventes |
| Marché | Crypto −60 % (déjà vu en backtest) | Volet limité à 10 % ; pas de renforcement en baisse |
| Marché | Faillite d'une plateforme crypto (leçon FTX) | ETF chez IBKR plutôt qu'un exchange ; sinon solde minimal sur l'exchange |
| Marché | Change USD/CAD | Rester en USD ; savoir que le gain imposable se calcule en CAD |
| Fiscal | CELI requalifié en « entreprise » | Phase 4 en compte non enregistré ; faible rotation ; avis d'un fiscaliste |
| Fiscal | Perte apparente (rachat en moins de 30 jours) | Le suivre dans le journal ; ne pas acheter le même titre dans le CELI |
| Fiscal | Calcul du coût de base en CAD | Exporter les relevés IBKR chaque mois ; tableau de coûts de base |
| Comportemental | Augmenter la taille après un bon mois | Paliers à date fixe seulement (§7) |
| Comportemental | Modifier le système en pleine baisse | Changement seulement via pré-inscription et journal ; bande de normalité du §5 |
| Comportemental | Accumuler les essais jusqu'à « trouver » | Compteur N et DSR obligatoires ; une idée par semaine |

---

## 9. Attentes honnêtes [E]

**Ordres de grandeur, avant impôts et frais.** 2018–2026 a été une période exceptionnelle (SPY +14,5 %/an). Sur le long terme, compte plutôt ~10 %/an nominal pour les actions américaines, avec de longues périodes bien pires.

| Capital | Année « normale » (+5 à +12 %) | Mauvaise année (−10 à −25 %) | Pire baisse historique de la v1 (−27 %) |
|---|---|---|---|
| 1 000 $ | +50 à +120 $ | −100 à −250 $ | −275 $ |
| 5 000 $ | +250 à +600 $ | −500 à −1 250 $ | −1 375 $ |
| 20 000 $ | +1 000 à +2 400 $ | −2 000 à −5 000 $ | −5 500 $ |

Tant que la partie A du §5 n'est pas passée, attends-toi à faire **à peu près comme SPY, avec plus de travail**.

**Coûts du volet crypto** (≈ 8,8 changements de signal par an et par crypto [E]) :

| Route | Coût par transaction | Frein annuel sur le volet crypto |
|---|---|---|
| Hypothèse du backtest | 0,25 % | ≈ 2,2 % |
| Kraken maker / taker | 0,40 % / 0,80 % [F] | ≈ 3,5 % / 7,0 % |
| Coinbase, moins de 1 000 $ de volume (taker) | 1,20 % [F] | ≈ 10,6 % |
| ETF chez IBKR, compte de 5 000 $ (~250 $ par crypto) | 1 $ minimum ≈ 0,4 %, plus 0,25 %/an de frais de fonds | ≈ 3,8 % |
| ETF chez IBKR, compte de 20 000 $ (~1 000 $ par crypto) | ≈ 0,1 %, plus 0,25 %/an | ≈ 1,1 % |

**Pourquoi la plupart des débutants en trading algorithmique perdent :**
1. **Ils sur-ajustent** : beaucoup d'essais, et on garde le meilleur par chance [F].
2. **Ils sous-estiment les coûts** : voir le tableau ci-dessus.
3. **Ils tradent trop souvent** : 97 % des day traders brésiliens qui ont persisté plus de 300 jours ont perdu de l'argent [F].
4. **Ils utilisent du levier.**
5. **Ils ont des bugs non surveillés** : on en a eu un.
6. **Ils changent le système pendant une baisse normale.**
7. **Ils augmentent la taille après une période chanceuse.**

---

## 10. Conflits avec CLAUDE.md (à trancher, rien n'a été modifié)

1. **Porte 2 (« 2+ semaines de papier vertes ») :** trop courte (la MinTRL est d'environ 3,7 ans) et ambiguë (« vertes » = profit ou bon fonctionnement ?). → La remplacer par les parties B et C du §5 **[D]**.
2. **§5 « Live broker candidate : Public.com » :** pas disponible au Canada [F]. → IBKR Canada.
3. **§5 exchanges crypto (Binance, Bybit, OKX…) :** ont quitté le Canada en 2023 [F]. Blofin, WEX et Tubbit n'ont pas été vérifiés. → À retirer.
4. **§5 Alpaca :** convient au papier, impossible en réel pour un Canadien [F].
5. **§6 ma-crossover « Gate 2 : SOFT-PASS » :** obsolète depuis le bug NaN. L'horloge redémarre à la Phase 0.

---

## 11. Les 3 décisions à prendre maintenant

1. **Adopter la règle du §5 telle quelle**, avant tout nouveau test. Ça veut aussi dire admettre que la v1 n'est pas « assez bonne » et lancer la Phase 1.
2. **Valider IBKR Canada comme broker du réel**, avec la crypto via ETF US à tester (idée 0). Ensuite, ouvrir le compte dès la Phase 1 pour activer le papier IBKR.
3. **Choisir le type de compte et le montant de départ maximum.** Je recommande un compte non enregistré au comptant, avec 2 000 à 5 000 $.

---

## Sources

**Brokers**
- Alpaca, résidents canadiens : [BrokerChooser](https://brokerchooser.com/broker-reviews/alpaca-trading-review/alpaca-trading-canada) · [forum Alpaca](https://forum.alpaca.markets/t/cant-create-individual-account-in-canada/7291) · [Alpaca non-US](https://alpaca.markets/support/tag/non-us)
- IBKR, restriction API sur les titres canadiens : [doc IBKR](https://www.interactivebrokers.com/docs/web-api/v1/requirements-limitations/canadian-residents-restricted-from-programmatically-trading-canadian-products) · [QuantConnect (citations d'IBKR)](https://www.quantconnect.com/forum/discussion/7303/canadians-not-allowed-to-use-interactive-brokers-api-anymore/)
- IBKR, réauthentification quotidienne et hebdomadaire : [doc IBKR](https://www.interactivebrokers.com/docs/tws-api/doc/tws-settings/daily-weekly-reauthentication)
- IBKR, Web API et OAuth : [IBKR Campus](https://www.interactivebrokers.com/campus/ibkr-api-page/webapi-doc/)
- IBKR, commissions et change : [commissions](https://www.interactivebrokers.ca/en/index.php?f=49761) · [ETF](https://www.interactivebrokers.ca/en/trading/products-etfs.php)
- IBKR, CELI et REER : [IBKR](https://www.interactivebrokers.ca/cn/accounts/rsp_tfsa_information.php?p=tfsa)
- IBKR, crypto : [BrokerChooser community](https://community.brokerchooser.com/t/crypto-trading-service/1431)
- IBIT accessible aux Canadiens : [Morningstar.ca](https://morningstar.ca/ca/news/259299/new-ishares-bitcoin-etf-brings-lower-cost-option-to-canadas-competitive-crypto-market-.aspx)
- Questrade, API : [Questrade API](https://www.questrade.com/api/home) · [entente d'accès API](https://www.questrade.com/disclosure/legal-notice-and-disclosures/api-access-agreement)
- moomoo Canada : [Finder](https://finder.com/ca/moomoo-review)
- Public.com : [BrokerChooser](https://brokerchooser.com/bg/broker-reviews/publiccom-review/publiccom-canada)
- Kraken, frais : [grille Kraken](https://kraken.com/features/fee-schedule) · [Datawallet](https://www.datawallet.com/crypto/kraken-fees-explained)
- Coinbase, frais : [Coinbase Advanced](https://www.coinbase.com/Advanced-trade) · [Bankrate](https://www.bankrate.com/investing/coinbase-review)
- Exchanges crypto au Canada : [Finder](https://finder.com/ca/cryptocurrency/exchanges)
- Départs du Canada en 2023 : [OKX (Cointelegraph)](https://cointelegraph.com/news/okx-to-cease-operations-in-canada-by-june-22-2023) · [Bybit (Finance Magnates)](https://financemagnates.com/cryptocurrency/bybit-joins-binance-and-others-to-exit-from-canada/amp) · [Binance (ForkLog)](https://forklog.com/en/binance-to-wind-down-operations-in-canada-amid-tighter-regulation/)

**Fiscalité**
- Taux d'inclusion : [Stephenson Harwood](https://www.stephensonharwood.com/insights/cancellation-of-canadian-capital-gains-inclusion-rate-increase/) · [The Logic](https://thelogic.co/briefing/carney-officially-kills-the-capital-gains-tax-hike/)
- CELI et trading actif : [TaxPage](https://taxpage.com/articles-and-tips/carrying-on-a-trading-business/) · [RBC Direct Investing](https://www.rbcdirectinvesting.com/learn/en/di/hubs/investing-academy/article/frequent-trading-in-your-registered-accounts/kp1bu4tc)
- Perte apparente : [Advisor.ca](https://advisor.ca/tax/tax-news/tax-loss-selling-superficial-loss-and-identical-property-rules/) · [Sun Life](https://www.sunlifeglobalinvestments.com/en/insights/investor-education/tax-and-estate-planning/the-superficial-loss-rules-have-you-tripped-the-wire/)
- Crypto, ARC : [Canada.ca](https://www.canada.ca/en/revenue-agency/news/newsroom/tax-tips/tax-tips-2023/cryptocurrency.html)
- Plafond CELI 2026 : [Fidelity.ca](https://www.fidelity.ca/en/insights/articles/tfsa-contribution-limit/)
- Retenue américaine, CELI vs REER : [Questrade](https://www.questrade.com/learning/rrsp-foreign-withholding-tax) · [Finiki](https://finiki.org/wiki/Foreign_withholding_taxes)

**Papier vs réel et PDT**
- Papier vs réel : [forum Alpaca](https://forum.alpaca.markets/t/slippage-paper-trading-vs-real-trading/2801) · [TradersPost](https://blog.traderspost.io/article/paper-trading-vs-live-trading-key-differences-and-what-to-expect)
- Fin de la règle PDT : [SEC SR-FINRA-2025-017](https://www.sec.gov/files/rules/sro/finra/2026/34-105226.pdf) · [ACA Group](https://www.acaglobal.com/industry-insights/finra-ends-the-pattern-day-trader-rule/)

**Méthodologie anti-surapprentissage**
- Deflated Sharpe Ratio : [SSRN 2460551](https://papers.ssrn.com/abstract=2460551)
- Probability of Backtest Overfitting : [SSRN 2326253](https://papers.ssrn.com/abstract=2326253)
- Statistical Overfitting : [SSRN 2507040](https://papers.ssrn.com/abstract=2507040)
- Sharpe Ratio Efficient Frontier (MinTRL) : [Journal of Risk](https://www.risk.net/journal-risk/2223785/sharpe-ratio-efficient-frontier)
- Harvey, Liu, Zhu : [SSRN 2513152](https://papers.ssrn.com/abstract=2513152)
- PBO et walk-forward : [LuxAlgo](https://www.luxalgo.com/library/concept/probability-of-backtest-overfitting.md)

**Taille des positions**
- Moreira & Muir : [NBER w22208](https://www.nber.org/papers/22208)
- Harvey et al., Impact of Volatility Targeting : [Duke](https://scholars.duke.edu/publication/1370354)
- MacLean, Thorp, Ziemba : [PDF Berkeley](https://www.stat.berkeley.edu/~aldous/157/Papers/Good_Bad_Kelly.pdf)

**Idées de stratégies**
- Faber GTAA : [Onveston](https://onveston.substack.com/p/decades-of-dominance-the-investing)
- Time Series Momentum : [AQR](https://www.aqr.com/library/journal-articles/time-series-momentum) · [SSRN 2089463](https://papers.ssrn.com/abstract=2089463)
- Liu & Tsyvinski : [SSRN 3226806](https://papers.ssrn.com/abstract=3226806)
- Antonacci : [Alpha Architect](https://alphaarchitect.com/risk-premia-harvesting-through-momentum/)
- McConnell & Xu : [CFA Institute](https://rpc.cfainstitute.org/research/financial-analysts-journal/2008/equity-returns-at-the-turn-of-the-month)

**Ce qui fait perdre les débutants**
- Day trading : [Chague, De-Losso, Giovannetti, SSRN 3423101](https://ssrn.com/abstract=3423101)
