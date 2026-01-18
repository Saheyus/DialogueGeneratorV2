# Automated Testing & Quality Framework

### Executive Summary

DialogueGenerator implements a **4-layer quality validation system** to maintain professional CRPG narrative quality at scale (1M+ lines by 2028):

**Testing Layers:**
- **Layer 1 (MVP, $0):** Structural tests - orphan nodes, cycles, player agency %, branching ratio
- **Layer 2 (V1.0, $0):** Slop detection - AI patterns, lexical diversity, lore dumps (EQ-Bench inspired)
- **Layer 3 (V1.5, $0.01/node):** LLM rubric scoring - 13 CRPG-specific abilities, selective user toggle
- **Layer 4 (V2.5, $0.02/comparison):** Pairwise Elo ranking - character ranking, template A/B testing (nice-to-have)

**Dual-Tier Baselines:**
- **Primary:** Planescape: Torment (150K words, professional CRPG reference) - validates genre-level quality
- **Secondary:** Character-specific manual baselines (Marc's writing per character) - validates voice consistency

**Key Metrics:** Slop Score (target <13 vs PS:T 10.38), Rubric Score (target >8/10), Acceptance Rate (target >80%)

**Annual Cost:** ~$1,100 for 1M nodes production (Layers 1-2 free, Layer 3 selective, Layer 4 minimal)

**Innovation:** Zero-cost baseline validation (deterministic tests + character-specific baseline comparison) + selective LLM judging for critical nodes only.

---

### Overview

DialogueGenerator implements a comprehensive, data-driven quality framework inspired by **EQ-Bench Creative Writing v3** and adapted for CRPG narrative authoring. This framework combines deterministic structural tests with LLM-assisted quality metrics, leveraging **dual-tier baselines** (Planescape: Torment professional reference + character-specific manual baselines) to ensure consistent, high-quality dialogue generation at scale.

**Philosophy:** Quality validation must be:
- **Automated** where possible (structural, slop detection) to enable scale (1M+ lines)
- **Human-guided** where needed (rubric feedback, manual baselines) to preserve craft
- **Data-driven** (metrics, baselines, trends) to enable objective improvement
- **Cost-conscious** (zero-cost layers prioritized, LLM judges selective)

**Key Innovation:** **Dual-tier baseline system** enables both character-specific style validation (character voice for Uresaïr, Genka Lien, etc.) AND genre-level quality benchmarking (Planescape: Torment gold standard).

---

### Testing Architecture Layers

The quality framework is organized in **4 layers** with increasing sophistication and cost:

**Layer 0: Baselines (Foundation)**
- Genre baseline: Planescape: Torment (1000 samples, 150K words total)
- Character-specific baselines: Manual writing samples per character (extensible)
- Storage: JSON files, `data/baselines/`
- **Cost:** One-time calculation ($0 ongoing)

**Layer 1: Structural Tests (MVP, $0 cost)**
- Deterministic validation (no LLM)
- Real-time feedback (inline badges)
- Tests: Orphan nodes, cycles, missing fields, player agency %, branching ratio
- **Implementation:** GraphValidationService (already exists), extend with metrics

**Layer 2: Slop Detection (V1.0, $0 cost)**
- Automated text analysis (no LLM)
- EQ-Bench slop metrics + CRPG-specific patterns
- Metrics: Slop words/trigrams, not-x-but-y patterns, lore dump patterns, lexical diversity
- **Implementation:** SlopDetector service (NLP library, regex)

**Layer 3: Rubric Scoring (V1.5, $0.01/node, selective)**
- LLM judge (Claude Sonnet 4)
- 13 CRPG-specific abilities (radar chart)
- User toggle ON/OFF (default OFF)
- **Cost:** ~$1,000/year (10% nodes evaluated)

**Layer 4: Pairwise Elo (V2.5, $0.02/comparison, nice-to-have)**
- Pairwise matchups for fine discrimination
- Monthly benchmark (20 characters x 30 nodes)
- Simplified Elo (not full Glicko loops)
- **Cost:** ~$72/year (monthly benchmarks)

**Total Annual Cost:** ~$1,100 for 1M nodes production (très acceptable)

---

### Dual-Tier Baseline System

#### Rationale

**Challenge:** DialogueGenerator serves two quality goals:
1. **Character Voice Fidelity** - Match Marc's unique writing style per character (poetic, metaphorical)
2. **Genre Quality Bar** - Achieve professional CRPG narrative quality (Planescape: Torment level)

**Solution:** Two-tier baselines enable both validations simultaneously, at zero ongoing cost.

#### Primary Baseline: Planescape: Torment

**Source:** Complete dialogue transcript (150,000 words, 10,000+ nodes)

**Justification:**
- **Gold Standard:** PS:T is industry reference for CRPG narrative excellence
- **Sample Size:** Massive dataset (1000+ sample nodes for baseline calculation)
- **Professional Quality:** Human-written, professionally edited, AAA game
- **Marketing Value:** "AI dialogue achieving Planescape: Torment quality" = investor pitch gold

**Baseline Metrics (calculated from 1000 random samples):**
```json
{
  "source": "Planescape: Torment",
  "sample_size": 1000,
  "total_words": 15420,
  "metrics": {
    "slop_score": 10.38,
    "slop_words_per_1k": 6.90,
    "slop_trigrams_per_1k": 0.09,
    "not_x_but_y_per_1k": 0.04,
    "vocab_level": 7.80,
    "sentence_length": 14.59,
    "lexical_diversity": 0.5065,
    "metaphor_density": 0.15
  }
}
```

**Usage:**
- All generated dialogues compared vs PS:T baseline
- Dashboard displays: "PS:T Quality: 8.6/10 ⭐ (Excellent)"
- Threshold: Generated slop score <13 (PS:T + 2.5 margin)

#### Secondary Baseline: Per-Character Manual Samples

**Source:** Marc's hand-written dialogue nodes (Articy Draft export)

**Current Samples:**
- **Uresaïr/Ethérée dialogue:** 22 nodes (12 NPC dialogue, 10 player choices)
- **Extensible:** Marc can write additional samples per character (Genka Lien, Raki-Biro, etc.)

**Example Character Baseline (Uresaïr):**
```json
{
  "character_name": "Uresaïr",
  "source": "Marc's manual nodes (Articy)",
  "sample_size": 12,
  "metrics": {
    "slop_score": 8.5,
    "vocab_level": 8.2,
    "sentence_length": 28.4,
    "lexical_diversity": 0.58,
    "metaphor_density": 0.42,
    "style_notes": "Poetic, metaphorical, contemplative"
  },
  "sample_excerpts": [
    "Le simoun m'apporte-t-il donc enfin un songe dont le parfum s'étende au-delà de ce monde ?",
    "Tu es une flamme qui brûle les mondes. Veux-tu nous brûler, nous aussi ?"
  ]
}
```

**Observations:**
- **Vocab Level:** 8.2 (character baseline) vs 7.8 (PS:T) - Character-specific baselines show elevated vocabulary
- **Sentence Length:** 28.4 (character baseline) vs 14.59 (PS:T) - Character baselines show longer, complex sentences
- **Metaphor Density:** 0.42 (character baseline) vs 0.15 (PS:T) - Character baselines show high metaphorical density
- **Slop Score:** 8.5 (character baseline) vs 10.38 (PS:T) - Manual baseline samples have less slop (as expected)

**Usage:**
- When character baseline exists: Compare generated vs character baseline
- Threshold: Generated slop ±2, vocab ±0.5, sentence length ±5 (acceptable deltas)
- Alert if deviation >threshold: "Déviation style Uresaïr détectée"

#### Validation Flow (Multi-Tier)

```
User generates node for Uresaïr
  ↓
Calculate node metrics (slop, vocab, style)
  ↓
Tier 1: Character-specific validation (if baseline exists)
  - Compare vs Uresaïr baseline
  - Score: 7.8/10 (Slop +2.7 borderline, vocab OK, metaphor OK)
  ↓
Tier 2: Genre validation (always)
  - Compare vs PS:T baseline
  - Score: 8.6/10 (Excellent vs professional reference)
  ↓
Dashboard display:
  Quality Score: 8.2/10
  ├─ Uresaïr Voice Match: 7.8/10 (Slop borderline)
  └─ PS:T Quality: 8.6/10 ⭐ (Excellent)
  
  Recommendations:
  - Reduce Slop Words (target <10 per 1k words)
  - Maintain metaphorical richness (OK)
```

---

### Layer 1: Structural Tests (MVP)

**Goal:** Catch graph structure bugs and validate dialogue flow logic.

**Cost:** $0 (deterministic code, no LLM)

**Tests:**

**ST-1: Orphan Nodes Detection**
- **Test:** Find nodes with no incoming/outgoing connections
- **Threshold:** 0 orphan nodes (except start/end nodes)
- **Alert:** "⚠️ 3 orphan nodes detected - graph incomplete"

**ST-2: Cycle Detection**
- **Test:** Find cycles in dialogue graph (A → B → C → A)
- **Threshold:** 0 infinite loops (warn if cycle detected)
- **Alert:** "⚠️ Cycle detected: Node A → B → C → A"

**ST-3: Missing Fields Validation**
- **Test:** Check required fields (speaker, text, connections)
- **Threshold:** 0 nodes with missing fields
- **Alert:** "❌ Node 42 missing speaker field"

**ST-4: Player Agency Ratio**
- **Test:** Calculate % of nodes that offer meaningful player choices
- **Formula:** `agency_ratio = (nodes_with_choices_2+) / total_nodes`
- **Threshold:** >40% (meaningful choice frequency)
- **Alert:** "⚠️ Agency 32% - below target 40%"

**ST-5: Branching Ratio**
- **Test:** Calculate branching/convergence balance
- **Formula:** `branching_ratio = divergence_points / convergence_points`
- **Threshold:** 0.8 - 1.5 (balanced graph)
- **Alert:** "⚠️ Branching 2.3 - too many divergences, graph may explode"

**Implementation:**
```python
# services/metrics/structural_validator.py

class StructuralValidator:
    def validate_dialogue(self, dialogue: Dialogue) -> StructuralReport:
        return {
            "orphan_nodes": self.find_orphans(dialogue),
            "cycles": self.detect_cycles(dialogue),
            "missing_fields": self.check_required_fields(dialogue),
            "agency_ratio": self.calculate_agency(dialogue),
            "branching_ratio": self.calculate_branching(dialogue)
        }
```

**UI Display:** Inline badges on graph nodes
- 🟢 Green: All tests pass
- 🟡 Yellow: Warnings (agency low, branching high)
- 🔴 Red: Errors (orphans, missing fields)

---

### Layer 2: Slop Detection (V1.0)

**Goal:** Detect "AI slop" patterns (overused phrases, purple prose, lore dumps) to maintain writing quality.

**Inspiration:** EQ-Bench Creative Writing v3 "Slop Score" methodology

**Cost:** $0 (NLP analysis, regex patterns, no LLM)

#### Slop Score Components

**SD-1: Slop Words (per 1k words)**

**Definition:** Overused words that indicate AI-generated text or lazy writing.

**EQ-Bench Base List (top 10):**
- whispered, stared, paused, glow, impossibly, trembling, nodded, shadows, flickered, shimmered

**CRPG-Specific Additions:**
- quest, tavern crowded, mysterious stranger, ancient artifact, destiny, prophecy, chosen one, fate

**Calculation:**
```python
def count_slop_words(text: str) -> float:
    word_count = len(text.split())
    slop_hits = sum(1 for word in SLOP_WORDS if word in text.lower())
    return (slop_hits / word_count) * 1000  # per 1k words
```

**Baseline Comparison:**
- **PS:T baseline:** 6.90 slop words per 1k
- **Character-specific baseline:** ~6-8 per 1k (manual writing)
- **Target:** <10 per 1k (acceptable), <15 (borderline), >15 (poor)

---

**SD-2: Slop Trigrams (per 1k words)**

**Definition:** Overused 3-word phrases that indicate formulaic writing.

**EQ-Bench Base List:**
- "something else something", "something else entirely", "one last time", "voice barely audible", "door swung open", "mind already racing"

**CRPG-Specific Additions:**
- "you must help", "but be warned", "time is short", "listen carefully now"

**Baseline Comparison:**
- **PS:T baseline:** 0.09 trigrams per 1k
- **Target:** <0.20 (good), <0.50 (acceptable), >0.50 (poor)

---

**SD-3: Not-X-But-Y Patterns (per 1k chars)**

**Definition:** Overused rhetorical pattern that indicates AI tendency to hedge or add unnecessary complexity.

**Pattern Detection (regex):**
```regex
(not|wasn't|isn't) .{1,50} (but|it was|it's)
```

**Examples:**
- "It wasn't the kind of kiss that promised to fix everything, it was something else entirely"
- "This wasn't the pleasant fog of endorphins. This was something closer to genuine amnesia."

**Baseline Comparison:**
- **PS:T baseline:** 0.04 per 1k chars
- **Target:** <0.10 (good), <0.20 (acceptable), >0.20 (poor)

---

**SD-4: Lore Dump Patterns (DialogueGenerator-Specific)**

**Definition:** Patterns indicating explicit exposition or "lore dumping" (violates "show don't tell").

**Pattern Detection (regex):**
```regex
(you know|as you remember|as you may recall|it is said that|allow me to explain|let me tell you)
```

**Examples:**
- "As you know, the Eternal Return is..."
- "You remember that Uresaïr is..."
- "Let me explain what happened..."

**Rationale:** CRPG dialogues should integrate lore naturally, not dump exposition.

**Target:** <2 patterns per dialogue (acceptable), >5 (poor)

---

**SD-5: Lexical Diversity (MATTR-500)**

**Definition:** Moving-Average Type-Token Ratio measures vocabulary richness (low diversity = repetitive).

**Calculation:**
- Sliding window of 500 words
- Calculate unique words / total words per window
- Average across all windows

**Baseline Comparison:**
- **PS:T baseline:** 0.5065 (human writing)
- **Target:** >0.55 (excellent), >0.50 (good), <0.45 (poor - too repetitive)

**Implementation:** NLTK or spaCy library

---

#### Composite Slop Score

**Formula (EQ-Bench inspired):**
```python
slop_score = (slop_words * 0.5) + (slop_trigrams * 2.0) + (not_x_but_y * 1.5) + (lore_dumps * 1.0)
```

**Interpretation:**
- **<12:** Excellent (comparable to human baseline)
- **12-15:** Good (acceptable for production)
- **15-20:** Borderline (review recommended)
- **>20:** Poor (needs revision)

**Dashboard Display:**
```
Slop Score: 12.3 (Good)

Details:
├─ Slop Words: 8.2 per 1k ✓ (target <10)
├─ Slop Trigrams: 0.15 per 1k ✓ (target <0.20)
├─ Not-X-But-Y: 0.08 per 1k chars ✓ (target <0.10)
├─ Lore Dumps: 1 detected ✓ (target <2)
└─ Lexical Diversity: 0.56 ⭐ (target >0.55)

Comparison:
- vs PS:T baseline: +1.9 (acceptable)
- vs Uresaïr baseline: +3.8 (borderline)
```

---

### Layer 3: Rubric Scoring (V1.5, Selective)

**Goal:** LLM-assisted quality feedback on 13 CRPG-specific abilities for targeted validation.

**Inspiration:** EQ-Bench rubric evaluation + CRPG narrative criteria

**Cost:** $0.01 per node (Claude Sonnet 4 judge)

**Strategy:** User toggle ON/OFF (default OFF) - use selective for critical nodes only

#### 13 CRPG-Specific Abilities

**Rubric evaluates each node on 13 dimensions (1-10 scale):**

**R1: Voice Consistency**
- Character speaks in established voice/dialect
- Vocabulary/tone match character baseline
- No jarring out-of-character moments

**R2: Lore Accuracy**
- Facts consistent with GDD
- No contradictions with established lore
- Accurate use of proper nouns, locations, history

**R3: Subtlety Lore Integration**
- "Show don't tell" - lore integrated naturally
- Avoids exposition dumps ("as you know...")
- Reveals lore through character actions/dialogue

**R4: Player Agency**
- Choices are meaningful (consequence-bearing)
- Player choices reflect distinct perspectives/values
- No false choices (all leading to same outcome)

**R5: Branching Coherence**
- Logical flow from previous node
- Choices connect coherently to next nodes
- No non-sequiturs or jarring transitions

**R6: Tone Consistency**
- Emotional tone appropriate for scene
- Maintains established mood (tragic, humorous, tense)
- Tone shifts are motivated, not random

**R7: Dialogue Naturalism**
- Avoids stilted/robotic phrasing
- Natural rhythm, not overly formal (unless character voice)
- Uses contractions, colloquialisms where appropriate

**R8: Character Insight**
- Reveals character motivation/personality
- Depth beyond surface dialogue
- Character growth or tension visible

**R9: Avoids Clichés**
- No generic CRPG tropes (mysterious tavern stranger, ancient prophecy)
- Fresh phrasing, not overused phrases
- Unique voice, not generic fantasy-speak

**R10: Avoids Flowery Verbosity**
- No excessive vocabulary flexing ("sempiternal", "ineffable" overused)
- Complexity serves character/scene, not show-off
- Balance sophistication with readability

**R11: Avoids Poetic Overload**
- Metaphor/poetry serves character voice, not excessive
- No purple prose or incoherent poetic rambling
- Clear meaning beneath poetic language

**R12: Plot/Character Coherence**
- Internal consistency (character choices logical)
- Plot developments motivated (no deus ex machina)
- Metaphors/symbols coherent with scene

**R13: Instruction Following**
- Dialogue follows generation prompt constraints
- Respects specified tone/length/context
- Includes required elements (choice count, branching)

#### Rubric Prompt (LLM Judge)

```
Evaluate the following CRPG dialogue node on these criteria (1-10 scale):

Context:
- Character: {character_name}
- Character baseline: {character_baseline_summary}
- Scene context: {scene_context}
- Previous node: {previous_node_text}

Generated Dialogue Node:
{generated_node_text}

Choices:
{generated_choices}

Criteria (score 1-10):
1. Voice Consistency (matches character baseline)
2. Lore Accuracy (consistent with GDD)
3. Subtlety Lore (show don't tell)
4. Player Agency (meaningful choices)
5. Branching Coherence (logical flow)
6. Tone Consistency (appropriate emotion)
7. Dialogue Naturalism (not stilted)
8. Character Insight (depth, motivation)
9. Avoids Clichés (fresh, unique)
10. Avoids Flowery Verbosity (no vocab flexing)
11. Avoids Poetic Overload (clear meaning)
12. Plot/Character Coherence (internal logic)
13. Instruction Following (prompt compliance)

For each criterion:
- Score (1-10)
- Brief explanation (1-2 sentences)
- Specific examples from text (quote)

Final composite score (average of 13 criteria).
```

**Output Format:**
```json
{
  "overall_score": 8.2,
  "criteria_scores": {
    "voice_consistency": {"score": 8, "explanation": "...", "example": "..."},
    "lore_accuracy": {"score": 9, "explanation": "...", "example": "..."},
    ...
  },
  "strengths": ["Natural dialogue flow", "Character voice consistent"],
  "weaknesses": ["Slight lore dump in opening line"],
  "recommendations": ["Reduce exposition, integrate lore through action"]
}
```

#### Rubric Usage Strategies

**Strategy A: Selective Rubric (MVP-V1.5)**
- User toggle ON/OFF per node (default OFF)
- Use for critical nodes (major NPCs, plot revelations)
- **Cost:** 10% nodes = 100K x $0.01 = $1,000/year (acceptable)

**Strategy B: Sampling Rubric (V2.0)**
- Automatic rubric on random sample (10% nodes)
- Statistical confidence: 90%+ with 10% sample
- **Cost:** 100K x $0.01 = $1,000/year

**Strategy C: Template Optimization Only (V2.5)**
- Rubric only for A/B testing templates
- 1000 tests/year x 60 nodes = 60K evaluations
- **Cost:** 60K x $0.01 = $600/year

**Recommendation:** Start with Strategy A (user toggle), evolve to C (template optimization).

---

### Layer 4: Pairwise Elo Ranking (V2.5, Nice-to-Have)

**Goal:** Fine discrimination between generated nodes for character ranking and template optimization.

**Inspiration:** EQ-Bench pairwise evaluation + Glicko rating system (simplified)

**Cost:** $0.02 per comparison (bidirectional)

**Status:** Nice-to-have (V2.5, not critical for production)

#### Methodology

**Pairwise Comparison Prompt:**
```
Compare the relative ability of each dialogue node on these criteria:

Node A (Character: Uresaïr):
{node_a_text}

Node B (Character: Uresaïr):
{node_b_text}

Criteria:
1. Character authenticity and insight
2. Interesting and original
3. Writing quality
4. Coherence (plot, character choices, metaphor)
5. Instruction following (prompt)
6. World and atmosphere
7. Avoids clichés (characters, dialogue, plot)
8. Avoids flowery verbosity & vocab maxxing
9. Avoids gratuitous metaphor or poetic overload

For each criterion:
- Pick the stronger node (no draws)
- Rate ability difference: + / ++ / +++ / ++++ / +++++ (1-5 scale)

Response format:
{
  "character_authenticity": {"winner": "A", "margin": "+++"},
  "interesting_original": {"winner": "B", "margin": "++"},
  ...
}
```

**Elo Calculation (Simplified):**
- Initial Elo: 1500 (all characters)
- Pairwise matchups: Sparse sampling (neighboring Elo scores)
- Win margin: Weighted by '+' count (1-5)
- Anchor scores: Reference node (human baseline) = 1500 fixed

**Use Cases:**

**UC-1: Character Ranking**
- Monthly benchmark: 20 characters x 30 nodes
- Pairwise matchups: ~300 comparisons (sparse)
- **Output:** Elo ranking per character (identify weak characters needing template tuning)
- **Cost:** 300 x $0.02 = $6/month ($72/year)

**UC-2: Template A/B Testing**
- Test template A vs B for same character
- 30 nodes each, 30 pairwise comparisons
- **Output:** Template A Elo 1420 vs Template B Elo 1350 → Use Template A
- **Cost:** 30 x $0.02 = $0.60 per A/B test

**UC-3: Quality Validation vs Baseline**
- Compare generated vs PS:T sample (human baseline)
- **Output:** DialogueGenerator avg Elo 1450 vs PS:T 1500 → "Near professional quality"

#### Implementation Notes

**Complexity:**
- Full Glicko system = complex (loops until stable)
- **Simplified approach:** Sparse sampling + anchor scores (no loops)
- **Sufficient for DialogueGenerator:** Ranking is relative, not absolute

**Alternative (V3.0+):**
- Skip Elo, use Rubric scores for ranking (simpler, cheaper)
- Elo adds fine discrimination but marginal value

**Recommendation:** Implement V2.5 if Marc wants character ranking dashboard. Otherwise, Rubric + Slop sufficient.

---

### Bias Mitigation Strategies

**Inspiration:** EQ-Bench identifies systematic biases in LLM judges. DialogueGenerator implements controls.

#### BM-1: Length Bias (Pairwise Comparisons)

**Problem:** LLM judges strongly favor longer outputs in pairwise tasks.

**Mitigation:** Truncate outputs at 4000 chars for pairwise comparisons.

**Rationale:** CRPG dialogue nodes rarely exceed 4000 chars. Truncation puts all nodes on equal footing.

**Impact:** No loss of judging ability (dialogue complete within 4000 chars).

---

#### BM-2: Position Bias

**Problem:** Judges may favor first or second position in pairwise comparisons.

**Mitigation:** Run all pairwise evaluations bidirectional (A vs B, then B vs A), average results.

**Cost:** 2x pairwise calls, but necessary for unbiased ranking.

---

#### BM-3: Complex Verbosity Bias

**Problem:** Judges easily impressed by vocab flexing (unnecessary sophistication).

**Mitigation:** Rubric criterion R10 (Avoids Flowery Verbosity) explicitly punishes excessive vocab.

**Prompt Guidance:** "Complexity should serve character/scene, not show off."

---

#### BM-4: Poetic Incoherence Bias

**Problem:** Judges impressed by relentless poetic prose bordering on incoherence (overtrained models).

**Challenge:** Difficult to differentiate purple prose from *good* poetic style (especially for highly poetic characters).

**Mitigation:** 
- Rubric criterion R11 (Avoids Poetic Overload) targets this explicitly
- Prompt guidance: "Clear meaning beneath poetic language required"
- Character baseline comparison: Uresaïr character baseline = high metaphor density (0.42) is *intended*

**Limitation:** Judge may still struggle. Manual review for highly poetic characters (Uresaïr).

---

#### BM-5: Lore Dump Bias (DialogueGenerator-Specific)

**Problem:** Judges may favor explicit exposition ("you know, the Eternal Return is...") over subtle integration.

**Mitigation:**
- Rubric criterion R3 (Subtlety Lore) explicitly values "show don't tell"
- Slop detection Layer 2 (SD-4: Lore Dump Patterns) detects explicit patterns
- Prompt guidance: "Lore integrated naturally through action/dialogue, not explained"

---

#### Biases NOT Controlled

**Self-Bias:** Judge may favor its own outputs (if same model used for generation + judging).
- **Mitigation:** Use different models (generate with GPT-4, judge with Claude Sonnet 4)

**Positivity Bias:** Unclear if judge favors positive/negative tone.
- **Mitigation:** None (assume balanced, monitor if pattern emerges)

**Smut Bias:** NSFW-tuned models may write towards erotica, judge punishes severely.
- **Mitigation:** None (DialogueGenerator not NSFW)

**Stylistic Biases:** Judge preferences may differ from author preferences or average human.
- **Mitigation:** Character-specific manual baselines override judge bias

---

### Implementation Roadmap

#### MVP (Sprint 1-2, ~5 days dev)

**Deliverables:**
- ✅ Baseline extraction scripts (Articy + PS:T)
- ✅ Layer 1: Structural tests (orphans, cycles, agency, branching)
- ✅ Inline badges (green/yellow/red, structural only)
- ✅ Storage: `data/baselines/*.json`

**Dependencies:**
- Python XML parser (Articy extraction)
- Graph traversal algorithms (cycle detection)

**Testing:**
- Unit tests: Structural validator (100% coverage)
- Integration test: Extract baselines from Marc's XML + PS:T TXT

---

#### V1.0 (Sprint 3-5, ~10 days dev)

**Deliverables:**
- ✅ Layer 2: Slop detection (words, trigrams, patterns, lexical diversity)
- ✅ Baseline comparison engine (dual-tier validation)
- ✅ SQLite migration (metrics storage, historical tracking)
- ✅ Dashboard: Slop Score + baseline comparison display

**Dependencies:**
- NLP library (NLTK or spaCy for MATTR calculation)
- Regex patterns (slop detection)
- SQLite schema design

**Testing:**
- Unit tests: Slop detector (verify counts, thresholds)
- Integration test: Calculate PS:T baseline, compare generated node

---

#### V1.5 (Sprint 6-8, ~15 days dev)

**Deliverables:**
- ✅ Layer 3: Rubric LLM judge (13 CRPG abilities, user toggle)
- ✅ Character-specific baselines (Marc writes more nodes per character)
- ✅ Analytics dashboard (per-dialogue, per-character, trends)
- ✅ Cost governance (track LLM judge usage, budget alerts)

**Dependencies:**
- Claude Sonnet 4 API integration (rubric judge)
- React dashboard components (metrics visualization)
- Per-character baseline storage expansion

**Testing:**
- Unit tests: Rubric prompt formatting, response parsing
- Integration test: Run rubric on sample node, verify scores

---

#### V2.5 (Sprint 13-15, ~10 days dev)

**Deliverables:**
- ✅ Layer 4: Pairwise Elo system (Simplified, sparse sampling)
- ✅ Monthly benchmark automation (20 characters x 30 nodes)
- ✅ Template A/B testing (automated feedback loop)

**Dependencies:**
- Elo calculation library (simplified Glicko)
- Pairwise comparison prompt engineering
- Benchmark scheduling (monthly cron job)

**Testing:**
- Unit tests: Elo calculation, anchor scores
- Integration test: Run monthly benchmark, verify ranking

---

### Success Metrics

**Quality Metrics (tracked in dashboard):**

**QM-1: Slop Score Trend**
- **Metric:** Average slop score per dialogue (over time)
- **Target:** Decreasing trend (improvement via template optimization)
- **Baseline:** PS:T 10.38, Marc's ~8.5

**QM-2: Baseline Match Rate**
- **Metric:** % generated nodes within acceptable delta vs baseline
- **Target:** >80% within thresholds (slop ±2, vocab ±0.5)

**QM-3: Rubric Score Average (if enabled)**
- **Metric:** Average rubric score (13 criteria, 1-10 scale)
- **Target:** >8.0 (excellent), >7.0 (good)

**QM-4: Manual Revision Rate**
- **Metric:** % nodes Marc edits after generation
- **Target:** <20% (80%+ accepted as-is)
- **Correlation:** Should correlate with slop/rubric scores

**QM-5: PS:T Quality Badge**
- **Metric:** % dialogues achieving "PS:T Quality: 8+/10"
- **Target:** >70% (marketing-ready benchmark)

---

### Cost Governance

**Annual Budget (1M nodes production):**

**Layer 1 (Structural):** $0
**Layer 2 (Slop):** $0
**Layer 3 (Rubric, 10% nodes):** ~$1,000
**Layer 4 (Elo, monthly):** ~$72
**Total:** ~$1,100/year

**Budget Alerts (V1.5+):**
- Monthly LLM judge usage tracking
- Alert if approaching budget ($100/month threshold)
- User dashboard: "Rubric calls this month: 420 / 1000"

**Optimization Strategies:**
- Default rubric OFF (user toggles for critical nodes)
- Rubric sampling (V2.0): 10% random vs 100% user-selected
- Elo benchmarks: Monthly vs weekly (reduce cost 4x)

---

### Reference Materials

**EQ-Bench Creative Writing v3:**
- Methodology: https://eqbench.com/creative_writing.html
- Slop Score: https://eqbench.com/slop-score.html
- Human Baseline: Slop 10.38, Lexical Diversity 0.5065

**Planescape: Torment:**
- Source: Linear dialogue transcript (150K words)
- Location: `docs/resources/Planescape_AStoryOfTorment.txt`

**Marc's Manual Nodes:**
- Source: Articy Draft XML export (22 nodes)
- Location: `docs/resources/MarcHumanDialogue.xml`
- Characters: Uresaïr, Ethérée (extensible: Genka Lien, Raki-Biro, etc.)

---

### Open Questions & Future Considerations

**OQ-1: Character Baseline Sample Size**
- Current: 22 nodes total (12 Uresaïr NPC, 10 player choices)
- Statistical minimum: 30 nodes for 90% confidence
- **Action:** Marc writes additional nodes per character (target 30+ per major character)

**OQ-2: Multi-Language Baselines (V3.0+)**
- Current: French only (Marc's primary language)
- Future: English translation support (if international release)
- **Challenge:** Baseline recalculation per language

**OQ-3: Rubric vs Elo Trade-Off**
- Both provide quality feedback, but Elo more expensive + complex
- **Question:** Is Elo ranking necessary, or Rubric + Slop sufficient?
- **Current decision:** Elo = nice-to-have (V2.5), evaluate based on V1.5 rubric results

**OQ-4: Real-Time Rubric Feedback (V2.0+)**
- Current: Rubric selective (user toggle)
- Future: Real-time rubric during generation? (UX: inline feedback while typing)
- **Challenge:** Latency (1-2s LLM call), cost (every node = $0.01)

---
