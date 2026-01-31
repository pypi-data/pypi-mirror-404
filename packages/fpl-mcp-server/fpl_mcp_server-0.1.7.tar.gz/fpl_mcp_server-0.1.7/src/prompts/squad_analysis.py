"""
FPL MCP Prompts - Squad Performance Analysis.

Prompts guide the LLM in analyzing squad performance over recent gameweeks
using underlying metrics and regression analysis.
"""

from ..tools import mcp


@mcp.prompt()
def analyze_squad_performance(team_id: int, num_gameweeks: int = 5) -> str:
    """
    Analyze squad performance using xGI-based metrics and regression analysis.

    This prompt guides the LLM to identify underperforming/overperforming players
    using underlying stats (xG, xA, xGI) rather than retrospective points.

    Args:
        team_id: FPL team ID of the manager to analyze
        num_gameweeks: Number of recent gameweeks to analyze (default: 5)
    """
    return f"""Analyze FPL squad performance for team ID {team_id} over the last {num_gameweeks} gameweeks.

**OBJECTIVE: Identify transfer targets using xGI-based regression analysis, not retrospective points.**

---

## 📊 **Performance Analysis Framework**

For each player in the squad, analyze:

### **1. Underlying Output Metrics (PRIMARY)**
- **xGI/90 (Expected Goal Involvements per 90 min)**: Total xG + xA over last {num_gameweeks} GW, normalized per 90
- **Minutes Played**: Total minutes + % of available minutes
  *<60% = rotation risk*
- **Games Played vs DNP**: Count starts, sub appearances, did not plays

### **2. Regression Analysis (CRITICAL)**
Calculate **xGI Delta** for each player:
- `Actual G+A (last {num_gameweeks} GW)` MINUS `xG + xA (last {num_gameweeks} GW)`

**Interpretation:**
- **Positive Delta (+2 to +4)**: OVERPERFORMING → Likely to regress (sell candidate)
- **Negative Delta (-2 to -4)**: UNDERPERFORMING → Due for improvement (keep/monitor)
- **Near Zero (-1 to +1)**: Performing to expectation (stable)

### **3. Player Categorization (xGI-Based)**

Instead of arbitrary PPG thresholds, use xGI/90:

- ⭐ **Elite Assets** (xGI/90 >0.6): Premium output, essential to keep
  *Even if underperforming actual points (negative delta), underlying stats suggest improvement coming*

- ✅ **Strong Contributors** (xGI/90 0.35-0.6): Reliable options, monitor for regression
  *If positive delta >+2, consider selling before decline*

- ⚠️ **Moderate Assets** (xGI/90 0.15-0.35): Acceptable for budget slots
  *If negative delta <-2, potential buy-low candidates*

- 🚨 **Underperformers** (xGI/90 <0.15): Transfer candidates
  *Low underlying output + poor fixtures = priority sell*

**Defenders/Goalkeepers:**
- Use defensive contribution + clean sheet odds instead of xGI
- xGC (Expected Goals Conceded) if available

---

## 🔍 **Transfer Priority Analysis**

### **For Each Underperformer (xGI/90 <0.15 OR injured):**

1. **Regression Context:**
   - If negative xGI delta: "Unlucky, but underlying stats still poor → Sell"
   - If positive xGI delta: "Overperforming low xGI → Definitely sell before regression"

2. **Availability Check:**
   - Injured/Suspended → 🚨 **URGENT** (transfer immediately)
   - DNP last 2 games → ⚠️ **HIGH** (rotation risk)
   - Minutes <60% last {num_gameweeks} GW → 🟡 **MEDIUM**

3. **Fixture Difficulty (Next 4 GW):**
   - Avg FDR >3.5 → Poor fixtures exacerbate low xGI
   - Avg FDR <2.5 → Fixtures can't help poor underlying stats

4. **Ownership Context:**
   - If template player (>30% ownership): May need to hold for rank protection
   - If differential (<10% ownership): Easy sell, minimal rank impact

5. **Transfer Recommendation:**
   - Provide urgency level: 🚨 URGENT / ⚠️ HIGH / 🟡 MEDIUM / 🟢 LOW
   - Suggest xGI-based replacement targets from `fpl_get_top_performers`

---

## 📈 **Squad Health Summary**

1. **Player Counts by Category:**
   - Elite Assets (xGI/90 >0.6): [X] players
   - Strong Contributors (xGI/90 0.35-0.6): [X] players
   - Moderate Assets (xGI/90 0.15-0.35): [X] players
   - Underperformers (xGI/90 <0.15): [X] players

2. **Regression Risk Summary:**
   - Players with xGI Delta >+2 (overperforming): [List names] → Potential sell targets
   - Players with xGI Delta <-2 (underperforming): [List names] → Monitor for improvement

3. **Priority Transfer Target:**
   - **Player Name** (xGI/90: [X.XX], xGI Delta: [+/-X.X], Fixtures: [avg FDR])
   - **Reason:** [injury / low xGI / rotation / regression risk]
   - **Urgency:** [URGENT/HIGH/MEDIUM/LOW]

4. **Overall Squad Health:**
   - Healthy (8+ strong contributors) / Moderate (5-7) / Poor (<5)

---

## 🔧 **Tool Calls**

Use these tools and resources:
1. `fpl_get_manager_by_team_id(team_id={team_id})` → Current squad composition
2. `fpl_get_top_performers(num_gameweeks={num_gameweeks})` → Benchmark against top xGI players
3. For each player:
   - `fpl://player/{{{{player_name}}}}/summary` → xG, xA, xGI, minutes, fixtures
4. `fpl://bootstrap/players` → Ownership %, price, transfer trends

---

## ⚠️ **Critical Rules**

1. **NEVER categorize by PPG alone** → Use xGI/90 for attackers, defensive contribution for defenders
2. **ALWAYS calculate xGI Delta** → Regression context is critical for sell decisions
3. **Account for ownership** → Template players need more justification to sell
4. **Prioritize injured/unavailable** → These are auto-sell regardless of xGI
"""
